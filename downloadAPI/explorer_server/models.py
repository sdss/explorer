"""Settings models for application"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List


class DataFrameData(BaseModel):
    columns: Dict[str,
                  List[Any]] = Field(...,
                                     description="Column-based DataFrame data")


class ExportResponse(BaseModel):
    status: str
    filepath: str
    download_url: str
    row_count: int
    column_count: int
