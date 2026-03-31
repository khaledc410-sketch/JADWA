import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class DataCache(Base):
    __tablename__ = "data_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(
        String(50), nullable=False
    )  # rfta | hrdf | sama | mci | gastat | vision2030
    cache_key = Column(String(255), nullable=False)
    data = Column(JSONB, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("source", "cache_key", name="uq_data_cache_source_key"),
    )
