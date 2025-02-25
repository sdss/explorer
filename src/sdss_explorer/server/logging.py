import logging
import logging.config

from ..util.config import settings


def setup_logging():
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format":
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "detailed": {
                "format":
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s - %(lineno)d"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "level": "INFO" if settings.dev else "DEBUG",
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": "app.log",
                "formatter": "detailed",
                "level": "INFO" if settings.dev else "DEBUG",
            },
        },
        "loggers": {
            "dashboard": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "server": {
                "level": "DEBUG",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    })
