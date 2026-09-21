from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"


class ExportRequestParams(BaseModel):
    format: ExportFormat = ExportFormat.CSV
