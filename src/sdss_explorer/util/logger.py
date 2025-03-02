"""Logging configuration and setup"""

from os.path import join as pathjoin
import logging
import logging.config
import solara as sl

__all__ = ["setup_logging"]


class MultiLineFormatter(logging.Formatter):
    """Multi-line formatter with UUKID prepended."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_header_length(self, record):
        """Get the header length of a given record."""
        record_no_msg = logging.LogRecord(
            name=record.name,
            level=record.levelno,
            pathname=record.pathname,
            lineno=record.lineno,
            msg="",
            args=(),
            exc_info=None,
        )
        record_no_msg.kernel_id = record.kernel_id  # ensure this is copied properly
        return len(super().format(record_no_msg))

    def format(self, record):
        """Format a record with added indentation and custom property prepended."""
        # get header
        head, *trailing = super().format(record).splitlines(True)
        # first = record.getMessage().splitlines(True)[0]
        # head = head.replace(first, "")

        # Format the message and preserve multiline formatting
        indent = " " * (self.get_header_length(record))
        # indent = " "

        return head + "".join(indent + line for line in trailing)


def get_kernel_id() -> str:
    """Fetches kernel ID per context"""
    try:
        return str(sl.get_kernel_id())
    except Exception:
        return "dummy"


def setup_logging(
    log_path: str = "./",
    log_file: str = "explorerApp.log",
    console_log_level: str = "DEBUG",
    file_log_level: str = "INFO",
):
    """
    Configures the logging system with a rotating file handler.

    Args:
        log_path: log path
        log_file: log filename
        console_log_level: log level for console as full uppercase string
        file_log_level: log level for file as full uppercase string
    """
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "()":
                # logging.Formatter,
                MultiLineFormatter,  # use custom multi-line formatter
                "format":
                "%(asctime)s - %(name)s - %(levelname)s - %(kernel_id)s - %(message)s",  # standard format
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": console_log_level,
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "standard",
                "level": file_log_level,
                "filename": pathjoin(log_path, log_file),
                "mode": "a",
            },
        },
        "loggers": {
            "dashboard": {
                "handlers": ["console", "file"],
                "level": file_log_level,
                "propagate": False,
            },
            "server": {
                "handlers": ["console", "file"],
                "level": file_log_level,
                "propagate": False,
            },
        },
    }

    # set record factory to set kernel id
    oldfactory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = oldfactory(*args, **kwargs)
        if getattr(record, "kernel_id", None) is None:
            record.kernel_id = get_kernel_id()
        return record

    logging.setLogRecordFactory(record_factory)

    logging.config.dictConfig(logging_config)
    return
