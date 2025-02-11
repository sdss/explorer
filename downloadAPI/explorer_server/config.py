"""Configuration settings"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    APP_NAME: str = "Vaex Export Service"
    EXPORT_DIR: str = "exports"
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_FORMATS: list = ["csv", "parquet"]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
