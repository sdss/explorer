import asyncio
import os
import logging
from concurrent.futures.process import ProcessPoolExecutor
from contextlib import asynccontextmanager
from http import HTTPStatus
from functools import partial
from timeit import default_timer as timer

from fastapi import BackgroundTasks
from fastapi import FastAPI
from uuid import UUID
import vaex.cache
import vaex.logging

from .logging import setup_logging
from .filter import filter_dataframe
from .jobs import Job, jobs
from ..util.config import settings

setup_logging()

vaex.logging.remove_handler()  # dump handler
vaex.cache.on()  # ensure cache on!

logger = logging.getLogger("server")

# solara server setup(?)
try:
    os.environ["SOLARA_APP"] = "sdss_explorer.dashboard"
    assert settings.solara  # check if we want to mount the server or not
    # this solara import needs to come after the os environ setup
    import solara.server.fastapi as solara_server
except AssertionError:
    solara_server = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.executor = ProcessPoolExecutor(max_workers=settings.nworkers)
    try:
        yield
    finally:
        app.state.executor.shutdown()  # free any resources


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def health_check():
    return {"This is": "Explorer server"}


async def run_in_process(fn, *args, **kwargs):
    """Helper to run in background"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(app.state.executor,
                                      partial(fn, *args, **kwargs)
                                      )  # wait and return result


async def start_filter(uid: UUID, release: str, datatype: str, dataset: str,
                       **kwargs) -> None:
    """Starts a filtering job"""
    try:
        start = timer()
        jobs[uid].filepath = await run_in_process(filter_dataframe, uid,
                                                  release, datatype, dataset,
                                                  **kwargs)
        logger.info(f"job {uid} completed! took {timer() - start:.4f}s")
        jobs[uid].status = "complete"
    except Exception as e:
        logger.info(f"job {uid} failed: {e}")
        jobs[uid].message = str(e)
        jobs[uid].status = "failed"


@app.post("/filter_subset/{release}/{datatype}/{dataset}",
          status_code=HTTPStatus.ACCEPTED)
async def task_handler(
    background_tasks: BackgroundTasks,
    release: str,
    datatype: str,
    dataset: str,
    name: str = "A",
    expression: str = "",
    carton: str = "",
    mapper: str = "",
    flags: str = "",
    crossmatch: str = "",
    cmtype: str = "",
    combotype: str = "AND",
    invert: bool = False,
):
    """Task handler endpoint

    Note:
        You can't have this kwargs overload because it needs to know the properties.

    Args:
        Everything from the subset
    """
    new_task = Job()  # create jobspec
    jobs[new_task.uid] = new_task  # add to global joblist
    # bundle data
    kwargs = dict(
        name=name,
        expression=expression,
        carton=carton,
        mapper=mapper,
        flags=flags,
        crossmatch=crossmatch,
        cmtype=cmtype,
        combotype=combotype,
        invert=invert,
    )
    background_tasks.add_task(start_filter, new_task.uid, release, datatype,
                              dataset, **kwargs)
    return new_task


@app.get("/status/{uid}")
async def status_handler(uid: UUID):
    """Status check endpoint"""
    return jobs[uid]


@app.get("/status-all")
async def status_all():
    """Get all job statuses"""
    return jobs


# mount if found
if solara_server:
    app.mount("/solara/", app=solara_server.app)
