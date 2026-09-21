import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.types import JSONType


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="queued")  # queued | running | completed | failed | paused | cancelled
    config = Column(JSONType, nullable=False, default=dict)
    records_found = Column(Integer, default=0, nullable=False)
    records_stored = Column(Integer, default=0, nullable=False)
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    error_details = Column(JSONType, nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("ResearchProject", back_populates="ingestion_jobs")
    source_records = relationship("SourceRecord", back_populates="ingestion_job")
