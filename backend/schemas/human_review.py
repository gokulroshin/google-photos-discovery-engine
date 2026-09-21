from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class HumanReviewCreate(BaseModel):
    evidence_record_id: str
    action: str = Field(..., pattern="^(approved|corrected|rejected)$")
    corrections: Optional[Dict[str, Any]] = None
    reviewer_notes: Optional[str] = None


class BulkReviewCreate(BaseModel):
    evidence_record_ids: List[str]
    action: str = Field(..., pattern="^(approved|rejected)$")
    reviewer_notes: Optional[str] = None


class HumanReviewResponse(BaseModel):
    id: str
    evidence_record_id: str
    reviewer_id: str
    action: str
    corrections: Optional[Dict[str, Any]] = None
    reviewer_notes: Optional[str] = None
    reviewed_at: datetime

    model_config = ConfigDict(from_attributes=True)
