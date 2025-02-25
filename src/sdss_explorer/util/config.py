"""Application settings. Places everything that is set by an envvar under a namespace."""

import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Global settings for webapp, defined by environment variables"""

    nworkers: int = Field(default=2, validation_alias="EXPLORER_NWORKERS")
    """How many gunicorn/uvicorn workers to run with."""

    nprocesses: int = Field(default=2, validation_alias="EXPLORER_NPROCESSES")
    """How many export processes to run concurrently. The max possible will on memory spec of the machine."""

    home: str = Field(default=os.path.expanduser("~"),
                      validation_alias="VAEX_HOME")  # TODO: default None
    """The home directory for logging and caching. Defaults to `$HOME`."""

    datapath: str = Field(
        default="./data",
        validation_alias="EXPLORER_DATAPATH")  # TODO: default None
    """The datapath to explorer files. Expects to be formatted in `./[release]/[explorer|columns]All[datatype]-[vastra].[hdf5|parquet]`"""

    scratch: str = Field(
        default="./scratch",
        validation_alias="EXPLORER_SCRATCH")  # TODO: default None
    """The datapath to a scratch space for custom summary file outputs."""

    dev: bool = Field(
        default=False,
        validation_alias="EXPLORER_DEV")  # used for logging configuration
    """Whether to consider the environment a development one or not. Also checks against whether server instance is production for dashboard."""

    vastra: str = "0.6.0"
    """Astra reduction versions to read."""

    solara: bool = Field(
        default=False, validation_alias="EXPLORER_MOUNT_DASHBOARD"
    )  # for future, in case one wants to host both simultaneously
    """Whether to mount the dashboard in the FastAPI server instance."""

    api_url: str = Field(default="http://localhost:8050",
                         validation_alias="EXPLORER_API_URL")
    """API url for download server. Defaults to localhost on port 8050."""


# NOTE: vaex additionally has settings
# VAEX_HOME -> where the cache is
# others described in README.md

settings = Settings()
