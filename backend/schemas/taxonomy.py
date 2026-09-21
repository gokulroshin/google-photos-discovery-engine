from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class TaxonomyCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    definition: str = Field(..., min_length=1)
    user_segment: Optional[str] = None
    common_memory_cues: Dict[str, Any] = Field(default_factory=dict)
    missing_information: Optional[str] = None
    common_search_behavior: Optional[str] = None
    failure_mechanism: str = Field(..., min_length=1)
    confidence_level: str = Field(default="high", pattern="^(high|medium|low)$")
    open_questions: List[str] = Field(default_factory=list)
    product_implications: Optional[str] = None


class TaxonomyCategoryCreate(TaxonomyCategoryBase):
    version: int = 1
    evidence_count: int = 0
    unique_author_count: int = 0
    source_diversity: Dict[str, int] = Field(default_factory=dict)
    representative_excerpts: List[str] = Field(default_factory=list)


class TaxonomyCategoryUpdate(BaseModel):
    name: Optional[str] = None
    definition: Optional[str] = None
    user_segment: Optional[str] = None
    missing_information: Optional[str] = None
    common_search_behavior: Optional[str] = None
    failure_mechanism: Optional[str] = None
    confidence_level: Optional[str] = None
    open_questions: Optional[List[str]] = None
    product_implications: Optional[str] = None


class TaxonomyCategoryResponse(TaxonomyCategoryBase):
    id: str
    project_id: str
    version: int
    evidence_count: int
    unique_author_count: int
    source_diversity: Dict[str, int]
    representative_excerpts: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaxonomyListResponse(BaseModel):
    items: List[TaxonomyCategoryResponse]
    total: int
    version: int
