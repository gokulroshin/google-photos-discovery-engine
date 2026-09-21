import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.types import JSONType


class OpportunityArea(Base):
    __tablename__ = "opportunity_areas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    taxonomy_category_id = Column(String(36), ForeignKey("taxonomy_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    evidence_frequency = Column(Integer, default=0, nullable=False)
    evidence_diversity = Column(JSONType, nullable=False, default=dict)
    unique_author_count = Column(Integer, default=0, nullable=False)
    user_impact_score = Column(Float, default=0.0, nullable=False)
    abandonment_rate = Column(Float, default=0.0, nullable=False)
    workaround_exists = Column(Boolean, default=False, nullable=False)
    strategic_relevance = Column(Float, default=0.0, nullable=False)
    problem_clarity = Column(Float, default=0.0, nullable=False)
    potential_reach = Column(String(100), nullable=True)
    validation_effort = Column(String(50), default="medium", nullable=False)  # low | medium | high
    scoring_methodology = Column(Text, nullable=True)
    analyst_notes = Column(Text, nullable=True)
    status = Column(String(50), default="draft", nullable=False)  # draft | validated | rejected | speculative
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    project = relationship("ResearchProject", back_populates="opportunity_areas")
    taxonomy_category = relationship("TaxonomyCategory", back_populates="opportunity_areas")
