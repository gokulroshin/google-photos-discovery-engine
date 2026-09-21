import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.types import JSONType


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    research_questions = Column(JSONType, nullable=False, default=list)
    status = Column(String(50), nullable=False, default="active")  # draft | active | archived
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    source_records = relationship("SourceRecord", back_populates="project", cascade="all, delete-orphan")
    ingestion_jobs = relationship("IngestionJob", back_populates="project", cascade="all, delete-orphan")
    model_runs = relationship("ModelRun", back_populates="project", cascade="all, delete-orphan")
    taxonomy_categories = relationship("TaxonomyCategory", back_populates="project", cascade="all, delete-orphan")
    opportunity_areas = relationship("OpportunityArea", back_populates="project", cascade="all, delete-orphan")
    reports = relationship("ResearchReport", back_populates="project", cascade="all, delete-orphan")

