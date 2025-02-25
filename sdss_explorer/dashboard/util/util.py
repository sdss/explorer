"""Util functions for the app"""

import uuid
import os

import vaex as vx  # noqa

__all__ = [
    "check_catagorical",
    "generate_unique_key",
    "validate_release",
    "validate_pipeline",
]


def check_catagorical(expression: str) -> bool:
    return (expression.dtype == "string") | (expression.dtype == "bool")


def generate_unique_key(key: str = "") -> str:
    """Generates a unique UUID-based key for given string."""

    def make_uuid(*_ignore):
        return str(uuid.uuid4())

    return key + make_uuid()


def validate_release(path, release) -> bool:
    """Validates whether release is valid."""
    if path:
        for it in os.scandir(path):
            if it.is_dir() and (it.name == release):
                return True
    return False


def validate_pipeline(df, pipeline) -> bool:
    """Validates whether pipeline is valid."""
    if df:
        if any(pipeline == c for c in df["pipeline"].unique()):
            return True
    return False
