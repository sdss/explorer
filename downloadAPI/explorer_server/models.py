"""Settings models for application"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List


class Data(BaseModel):
    """Data of subset. Mirrors what is requested in explorer.pages.dataclass.subset.Subset"""

    expression: str
    dataset: str
    carton: list[str]
    mapper: list[str]
    flags: list[str]
    selections: list[dict[str]]


class ExportResponse(BaseModel):
    status: str
    filepath: str
    download_url: str
    row_count: int
