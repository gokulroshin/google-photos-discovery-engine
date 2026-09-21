import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.types import JSONType


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    markdown_content = Column(Text, nullable=False)
    json_content = Column(JSONType, nullable=False, default=dict)
    evidence_count = Column(Integer, nullable=False, default=0)
    pending_reviews_count = Column(Integer, nullable=False, default=0)
    model_version = Column(String(100), nullable=True)
    prompt_version = Column(String(50), nullable=False, default="1.0.0")
    status = Column(String(50), nullable=False, default="completed")  # generating | completed | failed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship
    project = relationship("ResearchProject", back_populates="reports")
