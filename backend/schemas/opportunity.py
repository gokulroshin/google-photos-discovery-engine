from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class OpportunityAreaBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    evidence_frequency: int = 0
    evidence_diversity: Dict[str, int] = Field(default_factory=dict)
    unique_author_count: int = 0
    user_impact_score: float = Field(default=0.0, ge=0.0, le=10.0)
    abandonment_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    workaround_exists: bool = False
    strategic_relevance: float = Field(default=0.0, ge=0.0, le=10.0)
    problem_clarity: float = Field(default=0.0, ge=0.0, le=10.0)
    potential_reach: Optional[str] = None
    validation_effort: str = Field(default="medium", pattern="^(low|medium|high)$")
    scoring_methodology: Optional[str] = None
    analyst_notes: Optional[str] = None
    status: str = Field(default="draft", pattern="^(draft|validated|rejected|speculative)$")


class OpportunityAreaCreate(OpportunityAreaBase):
    taxonomy_category_id: Optional[str] = None


class OpportunityAreaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    user_impact_score: Optional[float] = None
    abandonment_rate: Optional[float] = None
    workaround_exists: Optional[bool] = None
    strategic_relevance: Optional[float] = None
    problem_clarity: Optional[float] = None
    potential_reach: Optional[str] = None
    validation_effort: Optional[str] = None
    analyst_notes: Optional[str] = Field(None, description="Required when manually overriding AI scores")
    status: Optional[str] = None


class OpportunityAreaResponse(OpportunityAreaBase):
    id: str
    project_id: str
    taxonomy_category_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OpportunityListResponse(BaseModel):
    items: List[OpportunityAreaResponse]
    total: int
