import asyncio
import logging
from typing import cast
from concurrent.futures.process import ProcessPoolExecutor
from contextlib import asynccontextmanager
from http import HTTPStatus
from functools import partial
from timeit import default_timer as timer

from fastapi import BackgroundTasks
from typing import Dict
from uuid import UUID, uuid4
from fastapi import FastAPI
from pydantic import BaseModel, Field

from explorer_server.logging import setup_logging
from explorer_server.filter import filter_dataframe

setup_logging()

logger = logging.getLogger("explorerdownload")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.executor = ProcessPoolExecutor(max_workers=5)
    try:
        yield
    finally:
        app.state.executor.shutdown()  # free any resources


class Job(BaseModel):
    uid: UUID = Field(default_factory=uuid4)
    status: str = "in_progress"
    message: str = ""
    filepath: str = cast(str, None)


jobs: Dict[UUID, Job] = {}

app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


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
    combotype: str = "AND",
    invert: bool = False,
):
    """Task handler endpoint"""
    new_task = Job()  # create jobspec
    jobs[new_task.uid] = new_task  # add to global joblist
    # bundle data
    kwargs = dict(
        name=name,
        expression=expression,
        carton=carton,
        mapper=mapper,
        flags=flags,
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
