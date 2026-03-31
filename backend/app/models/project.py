import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Sector: franchise | real_estate | fnb | retail
    sector = Column(String(50), nullable=False)

    # Project name (bilingual)
    name_ar = Column(String(255))
    name_en = Column(String(255))

    # All intake form data as JSONB
    intake_data = Column(JSONB, nullable=False, default=dict)

    # Status: draft | processing | completed | failed
    status = Column(String(20), default="draft")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="projects")
    report_runs = relationship("ReportRun", back_populates="project")
