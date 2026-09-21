import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.types import JSONType, ArrayType


class TaxonomyCategory(Base):
    __tablename__ = "taxonomy_categories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    definition = Column(Text, nullable=False)
    user_segment = Column(String(100), nullable=True)
    common_memory_cues = Column(JSONType, nullable=False, default=dict)
    missing_information = Column(Text, nullable=True)
    common_search_behavior = Column(Text, nullable=True)
    failure_mechanism = Column(Text, nullable=False)
    evidence_count = Column(Integer, default=0, nullable=False)
    unique_author_count = Column(Integer, default=0, nullable=False)
    source_diversity = Column(JSONType, nullable=False, default=dict)
    representative_excerpts = Column(ArrayType(), nullable=False, default=list)
    confidence_level = Column(String(20), default="high", nullable=False)  # high | medium | low
    open_questions = Column(ArrayType(), nullable=False, default=list)
    product_implications = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    project = relationship("ResearchProject", back_populates="taxonomy_categories")
    opportunity_areas = relationship("OpportunityArea", back_populates="taxonomy_category")
