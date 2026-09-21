from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, AliasChoices


class SourceRecordBase(BaseModel):
    source_platform: str = Field(..., description="Platform e.g. reddit, play_store, app_store, forum, manual_upload")
    source_url: Optional[str] = None
    source_date: Optional[datetime] = None
    raw_content: str = Field(..., min_length=1)
    author_handle: str = Field(default="anonymous_user")
    collection_method: str = Field(default="manual_import")
    metadata_json: Dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("metadata_json", "metadata"),
        serialization_alias="metadata",
    )
    language: Optional[str] = None


class SourceRecordCreate(SourceRecordBase):
    dedup_hash: Optional[str] = None


class SourceRecordResponse(SourceRecordBase):
    id: str
    project_id: str
    is_duplicate: bool
    dedup_hash: str
    collection_date: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SourceRecordListResponse(BaseModel):
    items: List[SourceRecordResponse]
    total: int
    total_before_filters: int
    page: int
    page_size: int
    total_pages: int
    applied_filters: Dict[str, Any] = Field(default_factory=dict)


class ImportSummaryResponse(BaseModel):
    records_accepted: int
    records_skipped_duplicate: int
    records_failed: int
    validation_errors: List[str] = Field(default_factory=list)
