"""Util functions for the app"""

import uuid
import os

import vaex as vx  # noqa

__all__ = [
    "check_catagorical",
    "_datapath",
    'open_file',
    "generate_unique_key",
]


def check_catagorical(expression: str) -> bool:
    return (expression.dtype == "string") | (expression.dtype == 'bool')


def open_file(filename):
    """Loader for files to catch excepts"""
    # get dataset name
    datapath = _datapath()

    # fail case for no envvar
    if datapath is None:
        return None

    # TODO: verify auth status when attempting to load a working group dataset

    # fail case for no file found
    try:
        dataset = vx.open(f"{datapath}/{filename}")
        return dataset
    except Exception as e:  # noqa
        # NOTE: this deals with exception quietly; can be changed later if desired
        print('Exception on dataload encountered', e)
        return None


def _datapath():
    """fetches path to parquet files from envvar"""
    datapath = os.getenv(
        "EXPLORER_DATAPATH"
    )  # NOTE: does not expect a slash at end of the envvar, can account for it in future
    if datapath:
        return datapath
    else:
        return None


def generate_unique_key(key: str = '') -> str:
    """Generates a unique UUID-based key for given string."""

    def make_uuid(*_ignore):
        return str(uuid.uuid4())

    return key + make_uuid()
