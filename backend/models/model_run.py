import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.types import JSONType


class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    model_name = Column(String(100), nullable=False, default="gemini-1.5-pro")
    prompt_version = Column(String(50), nullable=False, default="1.0.0")
    parameters = Column(JSONType, nullable=False, default=dict)
    status = Column(String(50), nullable=False, default="queued")  # queued | running | completed | failed | paused
    records_total = Column(Integer, default=0, nullable=False)
    records_success = Column(Integer, default=0, nullable=False)
    records_failed = Column(Integer, default=0, nullable=False)
    error_log = Column(JSONType, nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("ResearchProject", back_populates="model_runs")
    evidence_records = relationship("EvidenceRecord", back_populates="model_run", cascade="all, delete-orphan")
