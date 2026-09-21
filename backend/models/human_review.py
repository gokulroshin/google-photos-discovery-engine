import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.types import JSONType


class HumanReview(Base):
    __tablename__ = "human_reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evidence_record_id = Column(String(36), ForeignKey("evidence_records.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(String(255), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # approved | corrected | rejected
    corrections = Column(JSONType, nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    evidence_record = relationship("EvidenceRecord", back_populates="human_reviews")
