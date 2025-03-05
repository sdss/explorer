"""Jobs structuring classes"""

from typing import cast, Dict
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

__all__ = ["Job", "jobs"]


class Job(BaseModel):
    uid: UUID = Field(default_factory=uuid4)
    status: str = "in_progress"
    message: str = ""
    filepath: str = cast(str, None)


jobs: Dict[UUID, Job] = {}
