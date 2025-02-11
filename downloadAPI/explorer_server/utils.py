"""Utility functions"""

import os
import uuid
from datetime import datetime
import vaex
from typing import Dict, List, Any


def generate_unique_filename(prefix: str = "export",
                             extension: str = "csv") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{unique_id}.{extension}"


def ensure_export_dir(export_dir: str) -> None:
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)


def create_vaex_dataframe(data: Dict[str, List[Any]]) -> vaex.DataFrame:
    return vaex.from_dict(data)
