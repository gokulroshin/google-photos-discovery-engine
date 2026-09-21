from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Unique research project name")
    description: Optional[str] = Field(None, description="Detailed project description or scope")
    research_questions: List[str] = Field(default_factory=list, description="Target research questions")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    research_questions: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(draft|active|archived)$")


class ProjectResponse(ProjectBase):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    record_count: int = 0
    evidence_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):
    active_jobs_count: int = 0
    total_categories_count: int = 0
    total_opportunities_count: int = 0


class ProjectListResponse(BaseModel):
    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
