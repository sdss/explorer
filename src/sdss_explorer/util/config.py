"""Application settings. Places everything that is set by an envvar under a namespace."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Global settings for webapp, defined by environment variables"""
    model_config = SettingsConfigDict(env_prefix="explorer_")
    nworkers: int = Field(default=2, description="How many gunicorn/uvicorn workers to run with.")

    nprocesses: int = Field(default=2, description="How many export processes to run concurrently. The max possible will on memory spec of the machine.")

    home: str = Field(default=os.path.expanduser("~"),
                      validation_alias="VAEX_HOME",
                      description="The home directory for caching and fingerprinting by vaex. Defaults to `$HOME`.")

    logpath: str = Field(default=os.path.expanduser("~"),
                         description="The home directory for logs. Defaults to `$HOME`.")

    loglevel: str = Field(default="INFO",
                          description="The log level for stdout/err. Defaults to INFO.")

    datapath: str = Field(default="./home",
                          description="The datapath to explorer files. Expects to be formatted in `./[release]/[explorer|columns]All[datatype]-[vastra].[hdf5|parquet]`")

    scratch: str = Field(default="./scratch",
                         description="The datapath to a scratch space for custom summary file outputs.")

    dev: bool = Field(
        default=False,
        description="Whether to consider the environment a development one or not. Also checks against whether server instance is production for dashboard."
    )

    vastra: str = Field(default="0.6.0",
                        validation_alias="VASTRA",
                        description="Astra reduction versions to read.")

    solara: bool = Field(
        default=False, validation_alias="EXPLORER_MOUNT_DASHBOARD",
        description="Whether to mount the dashboard in the FastAPI server instance."
    )

    api_url: str = Field(default="http://localhost:8050",
                         description="API url for download server. Defaults to localhost on port 8050.")

    download_url: str = Field(
        default="https://bing.com/search?query=",
        description="Public download URL for serving files. Defaults to bing (for fun)."
    )


# NOTE: vaex additionally has settings
# VAEX_HOME -> where the cache is
# others described in README.md

settings = Settings()
