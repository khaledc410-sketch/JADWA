import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class BrandingAsset(Base):
    __tablename__ = "branding_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    logo_url = Column(Text)
    primary_color = Column(String(7), default="#1B4332")  # Dark green (Saudi-inspired)
    secondary_color = Column(String(7), default="#40916C")
    report_title_prefix_ar = Column(String(255))
    report_title_prefix_en = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="branding_assets")
