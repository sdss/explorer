import logging
import logging.config
import os

DEV = bool(os.getenv("EXPLORER_DEV", False))

# logging_config.py


def setup_logging():
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s - %(lineno)d"
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "simple",
                    "level": "INFO" if DEV else "DEBUG",
                },
                "file": {
                    "class": "logging.FileHandler",
                    "filename": "app.log",
                    "formatter": "detailed",
                    "level": "INFO" if DEV else "DEBUG",
                },
            },
            "loggers": {
                "": {  # Root logger
                    "handlers": ["console", "file"],
                    "level": "DEBUG",
                    "propagate": False,
                },
                "explorerdownload": {
                    "level": "DEBUG",
                    "handlers": ["console"],
                    "propagate": False,
                },
            },
        }
    )


# Then, call setup_logging in your main module to initialize logging
