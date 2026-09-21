from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from backend.schemas.source_record import SourceRecordResponse


class MemoryCuesSchema(BaseModel):
    person: Optional[str] = None
    place: Optional[str] = None
    time: Optional[str] = None
    event: Optional[str] = None
    object: Optional[str] = None
    visual: Optional[str] = None
    text: Optional[str] = None
    emotion: Optional[str] = None
    purpose: Optional[str] = None
    source: Optional[str] = None


class EvidenceRecordBase(BaseModel):
    is_relevant: bool
    relevance_labels: List[str] = Field(default_factory=list)
    retrieval_scenario: Optional[str] = None
    memory_cues: Dict[str, Any] = Field(default_factory=dict)
    missing_information: Optional[str] = None
    search_behavior: Optional[str] = None
    retrieval_outcome: Optional[str] = None
    failure_points: List[str] = Field(default_factory=list)
    user_segment: Optional[str] = None
    evidence_excerpt: Optional[str] = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    rationale: Optional[str] = None
    needs_human_review: bool = False
    is_genuine_experience: bool = True
    embedding_stale: bool = False
    embedding_model_version: Optional[str] = "text-embedding-004"


class EvidenceRecordCreate(EvidenceRecordBase):
    source_record_id: str
    model_run_id: Optional[str] = None
    embedding: Optional[List[float]] = None


class EvidenceRecordResponse(EvidenceRecordBase):
    id: str
    source_record_id: str
    model_run_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceRecordDetailResponse(EvidenceRecordResponse):
    source_record: Optional[SourceRecordResponse] = None
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None


class EvidenceRecordListResponse(BaseModel):
    items: List[EvidenceRecordResponse]
    total: int
    total_before_filters: int
    page: int
    page_size: int
    total_pages: int
    applied_filters: Dict[str, Any] = Field(default_factory=dict)
