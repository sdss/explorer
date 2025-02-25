"""Everything that is set by an envvar under one namespace"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    nworkers: int = Field(default=2, validation_alias="EXPLORER_NEXPORTERS")
    datapath: str = Field(
        default="./data",
        validation_alias="EXPLORER_DATAPATH")  # TODO: default None
    scratch: str = Field(
        default="./scratch",
        validation_alias="EXPLORER_DATAPATH")  # TODO: default None
    dev: bool = Field(
        default=False,
        validation_alias="EXPLORER_DEV")  # used for logging configuration
    vastra: str = "0.6.0"
    solara: bool = False  # for future, in case one wants to host both simultaneously


# NOTE: vaex additionally has settings
# VAEX_HOME -> where the cache is
# others described in README.md

settings = Settings()
