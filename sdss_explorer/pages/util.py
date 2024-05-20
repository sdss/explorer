import uuid

import vaex as vx  # noqa


def check_catagorical(expression: str) -> bool:
    return expression.dtype == "string"


def generate_unique_key(key: str) -> str:
    """Generates a unique UUID-based key for given string."""

    def make_uuid(*_ignore):
        return str(uuid.uuid4())

    return key + make_uuid()
