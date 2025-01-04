"""Logging configuration and setup"""

import logging
from os.path import join as pathjoin

import logging
import logging.config

__all__ = ["setup_logging"]


class MultiLineFormatter(logging.Formatter):
    """Multi-line formatter with UUKID prepended."""

    def __init__(self, fmt=None, datefmt=None, kernel_id=None):
        super().__init__(fmt, datefmt)
        self.kernel_id = kernel_id

    def get_header_length(self, record):
        """Get the header length of a given record."""
        return len(super().format(
            logging.LogRecord(
                name=record.name,
                level=record.levelno,
                pathname=record.pathname,
                lineno=record.lineno,
                msg="",
                args=(),
                exc_info=None,
            )))

    def format(self, record):
        """Format a record with added indentation and custom property prepended."""
        # Add the custom property to the record
        record.kernel_id = self.kernel_id
        # TODO:kernel_id_field = f"{record.kernel_id} - "

        # get header
        head, *trailing = super().format(record).splitlines(True)
        # first = record.getMessage().splitlines(True)[0]
        # head = head.replace(first, "")

        # Format the message and preserve multiline formatting
        indent = " " * (self.get_header_length(record)
                        )  # + len(kernel_id_field))

        return head + "".join(indent + line for line in trailing)


def setup_logging(
    log_path: str = "./logs/",
    log_file: str = "app.log",
    console_log_level=logging.DEBUG,
    file_log_level=logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5,
    kernel_id: str = "dummy",
):
    """
    Configures the logging system with a rotating file handler.

    Args:
        log_file (str): Path to the log file.
        log_level (int): Logging level (e.g., logging.DEBUG, logging.INFO).
        max_bytes (int): Maximum size of a log file before rotation.
        backup_count (int): Number of backup files to keep.
        kernel_id (str): Kernel identifier to use for logging
    """
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "()":
                MultiLineFormatter,  # Use the custom multi-line formatter
                "format":
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Standard format
                "kernel_id":
                kernel_id,  # Pass the custom property to the formatter
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": console_log_level,
            },
            "rotating_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "filename": pathjoin(log_path, log_file),
                "maxBytes": max_bytes,
                "backupCount": backup_count,
                "level": file_log_level,
            },
        },
        "loggers": {
            # Example: Custom logger configuration for a specific module
            "sdss_explorer": {
                "handlers": ["console", "rotating_file"],
                "level": file_log_level,
                "class": "ExplorerLogger",
                "kernel_id": "dummy",
                "propagate": False,
            }
        },
    }

    logging.config.dictConfig(logging_config)
    return
