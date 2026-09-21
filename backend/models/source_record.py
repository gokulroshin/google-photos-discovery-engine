import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.types import JSONType


class SourceRecord(Base):
    __tablename__ = "source_records"
    __table_args__ = (
        UniqueConstraint("project_id", "dedup_hash", name="uq_project_dedup_hash"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source_platform = Column(String(50), nullable=False, index=True)
    source_url = Column(Text, nullable=True)
    source_date = Column(DateTime(timezone=True), nullable=True)
    raw_content = Column(Text, nullable=False)
    author_handle = Column(String(255), nullable=False, default="anonymous_user")
    collection_method = Column(String(50), nullable=False, default="manual_import")
    collection_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ingestion_job_id = Column(String(36), ForeignKey("ingestion_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    is_duplicate = Column(Boolean, default=False, nullable=False)
    dedup_hash = Column(String(64), nullable=False, index=True)
    metadata_json = Column("metadata", JSONType, default=dict, nullable=False)
    language = Column(String(20), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    project = relationship("ResearchProject", back_populates="source_records")
    ingestion_job = relationship("IngestionJob", back_populates="source_records")
    evidence_records = relationship("EvidenceRecord", back_populates="source_record", cascade="all, delete-orphan")
