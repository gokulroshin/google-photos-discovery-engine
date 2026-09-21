from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class ModelRunBase(BaseModel):
    model_name: str = Field(default="gemini-1.5-pro")
    prompt_version: str = Field(default="1.0.0")
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ModelRunCreate(ModelRunBase):
    pass


class ModelRunResponse(ModelRunBase):
    id: str
    project_id: str
    status: str
    records_total: int
    records_success: int
    records_failed: int
    error_log: Optional[Dict[str, Any]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
