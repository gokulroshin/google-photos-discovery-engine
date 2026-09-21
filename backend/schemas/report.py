from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class ResearchReportCategory(BaseModel):
    id: str
    name: str
    definition: str
    evidence_count: int
    confidence_level: str
    failure_mechanism: str
    product_implications: str


class ResearchReportOpportunity(BaseModel):
    id: str
    name: str
    user_impact_score: float
    strategic_relevance: float
    problem_clarity: float
    abandonment_rate: Optional[float] = 0.0
    validation_effort: str
    potential_reach: str
    status: str


class ResearchReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    project_name: str
    title: str
    generated_at: str
    categories_count: int
    opportunities_count: int
    evidence_count: int
    pending_reviews_count: int
    model_version: Optional[str] = None
    prompt_version: Optional[str] = "1.0.0"
    categories: List[Dict[str, Any]] = []
    opportunities: List[Dict[str, Any]] = []
    markdown: str
    created_at: datetime


class ReportSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    title: str
    status: str
    evidence_count: int
    pending_reviews_count: int
    model_version: Optional[str] = None
    prompt_version: Optional[str] = "1.0.0"
    created_at: datetime
