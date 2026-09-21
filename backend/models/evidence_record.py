import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.types import JSONType, ArrayType, VectorType


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_record_id = Column(String(36), ForeignKey("source_records.id", ondelete="CASCADE"), nullable=False, index=True)
    model_run_id = Column(String(36), ForeignKey("model_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    is_relevant = Column(Boolean, default=False, nullable=False, index=True)
    relevance_labels = Column(ArrayType(), nullable=False, default=list)
    retrieval_scenario = Column(String(255), nullable=True)
    memory_cues = Column(JSONType, nullable=False, default=dict)
    missing_information = Column(Text, nullable=True)
    search_behavior = Column(Text, nullable=True)
    retrieval_outcome = Column(String(50), nullable=True, index=True)
    failure_points = Column(ArrayType(), nullable=False, default=list)
    user_segment = Column(String(100), nullable=True)
    evidence_excerpt = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.0, nullable=False, index=True)
    rationale = Column(Text, nullable=True)
    needs_human_review = Column(Boolean, default=False, nullable=False, index=True)
    is_genuine_experience = Column(Boolean, default=True, nullable=False)
    embedding = Column(VectorType(768), nullable=True)
    embedding_stale = Column(Boolean, default=False, nullable=False, index=True)
    embedding_model_version = Column(String(50), nullable=True, default="text-embedding-004")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    source_record = relationship("SourceRecord", back_populates="evidence_records")
    model_run = relationship("ModelRun", back_populates="evidence_records")
    human_reviews = relationship("HumanReview", back_populates="evidence_record", cascade="all, delete-orphan")
