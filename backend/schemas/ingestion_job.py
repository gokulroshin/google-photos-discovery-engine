from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class IngestionJobBase(BaseModel):
    source_type: str = Field(..., description="e.g. manual_import, play_store, app_store, reddit, youtube, forum")
    config: Dict[str, Any] = Field(default_factory=dict)


class IngestionJobCreate(IngestionJobBase):
    pass


class IngestionJobResponse(IngestionJobBase):
    id: str
    project_id: str
    status: str
    records_found: int
    records_stored: int
    last_heartbeat_at: Optional[datetime] = None
    error_details: Optional[Dict[str, Any]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class IngestionJobListResponse(BaseModel):
    items: List[IngestionJobResponse]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1
