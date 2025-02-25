"""General utility functions"""

import uuid
import os

import vaex as vx  # noqa

__all__ = [
    "check_categorical",
    "generate_unique_key",
    "validate_release",
    "validate_pipeline",
]


def check_categorical(expression: vx.Expression) -> bool:
    """Checks whether a given expression is categorical or not.

    Args:
        expression: the expression to validate

    Returns:
        bool: whether the expression can be considered categorical data or not
    """
    return (expression.dtype == "string") | (expression.dtype == "bool")


def generate_unique_key(key: str = "") -> str:
    """Generates a unique UUID-based key for given string.

    Args:
        key: a sub-key to prefix with

    Returns:
        A new unique key with a UUID4 postpended.
    """

    def make_uuid(*_ignore):
        return str(uuid.uuid4())

    return key + make_uuid()


def validate_release(path: str, release: str) -> bool:
    """Validates whether release is valid.

    This traverses the provided path to see whether there is a folder of that name `release`.

    Args:
        path: the datapath to check whether `release` is valid against
        release: the release to check against

    Returns:
        `True`: if an valid release for this dataframe
        `False`: if an invalid release for this dataframe
    """
    if path:
        for it in os.scandir(path):
            if it.is_dir() and (it.name == release):
                return True
    return False


def validate_pipeline(df: vx.DataFrame, pipeline: str) -> bool:
    """Validates whether pipeline is valid.

    This checks membership of the pipeline in the dataframe.

    Note:
        This method assumes `pipeline` is a valid column in `df`.

    Args:
        df: dataframe to check whether `pipeline` is valid against
        pipeline: the pipeline to check against

    Returns:
        `True`: if an valid pipeline for this dataframe
        `False`: if an invalid pipeline for this dataframe
    """
    if df:
        if any(pipeline == c for c in df["pipeline"].unique()):
            return True
    return False
