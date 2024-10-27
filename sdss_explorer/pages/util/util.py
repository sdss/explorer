"""Util functions for the app"""

import uuid

import vaex as vx  # noqa

__all__ = [
    "check_catagorical",
    "generate_unique_key",
]


def check_catagorical(expression: str) -> bool:
    return (expression.dtype == "string") | (expression.dtype == 'bool')


def generate_unique_key(key: str = '') -> str:
    """Generates a unique UUID-based key for given string."""

    def make_uuid(*_ignore):
        return str(uuid.uuid4())

    return key + make_uuid()
