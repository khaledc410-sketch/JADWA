import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class ReportRun(Base):
    __tablename__ = "report_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    celery_task_id = Column(String(100))

    # Status: queued | running | completed | failed
    status = Column(String(20), default="queued")

    # Pipeline progress state — tracks which agents have run
    pipeline_state = Column(JSONB, default=dict)

    # Current step description (for SSE progress)
    current_step = Column(String(255))
    progress_percent = Column(Integer, default=0)

    # Verdict + structured sections (saved after Compiler, before PDF)
    verdict_data = Column(JSONB)  # Executive summary verdict JSON
    sections_data = Column(JSONB)  # All compiled report sections

    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="report_runs")
    outputs = relationship("ReportOutput", back_populates="run")
    agent_logs = relationship("AgentLog", back_populates="run")


class ReportOutput(Base):
    __tablename__ = "report_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("report_runs.id"), nullable=False)

    language = Column(String(2), nullable=False)  # 'ar' | 'en'
    pdf_url = Column(Text)  # S3 URL
    page_count = Column(Integer)
    file_size_kb = Column(Integer)
    generation_time_seconds = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("ReportRun", back_populates="outputs")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("report_runs.id"), nullable=False)

    agent_name = Column(String(100), nullable=False)
    status = Column(
        String(20), default="pending"
    )  # pending | running | completed | failed
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    error_message = Column(Text)
    tokens_used = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    run = relationship("ReportRun", back_populates="agent_logs")
