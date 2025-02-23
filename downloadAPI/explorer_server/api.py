import asyncio
from multiprocessing import Process
from typing import cast
from concurrent.futures.process import ProcessPoolExecutor
from contextlib import asynccontextmanager
from http import HTTPStatus
from functools import partial

from fastapi import BackgroundTasks
from typing import Dict
from uuid import UUID, uuid4
from fastapi import FastAPI
from pydantic import BaseModel, Field

from .filter import filter_dataframe


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
    filepath: str = cast(str, None)


jobs: Dict[UUID, Job] = {}

app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


async def run_in_process(fn, *args, **kwargs):
    """Helper to run in background"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(fn, *args, **kwargs)
                                      )  # wait and return result


async def start_filter(uid: UUID, release: str, datatype: str, dataset: str,
                       **kwargs) -> None:
    """Starts a filtering job"""
    jobs[uid].filepath = await run_in_process(filter_dataframe, uid, release,
                                              datatype, dataset, **kwargs)
    jobs[uid].status = "complete"


@app.post("/filter_subset/{release}/{datatype}/{dataset}",
          status_code=HTTPStatus.ACCEPTED)
async def task_handler(
    background_tasks: BackgroundTasks,
    release: str,
    datatype: str,
    dataset: str,
    expression: str = "",
    carton: str = "",
    mapper: str = "",
    flags: str = "",
):
    """Task handler endpoint"""
    new_task = Job()  # create jobspec
    jobs[new_task.uid] = new_task  # add to global joblist
    # bundle data
    kwargs = dict(
        expression=expression,
        carton=carton,
        mapper=mapper,
        flags=flags,
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
