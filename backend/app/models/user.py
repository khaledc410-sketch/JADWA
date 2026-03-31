import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    email_verified = Column(Boolean, default=False)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(20))
    phone_verified = Column(Boolean, default=False)
    full_name_ar = Column(String(255))
    full_name_en = Column(String(255))
    preferred_language = Column(String(2), default="ar")  # 'ar' | 'en'
    national_id = Column(String(20))
    company_name_ar = Column(String(255))
    company_name_en = Column(String(255))
    company_cr_number = Column(String(20))  # Commercial Registration
    role = Column(String(50), default="owner")  # owner | member | admin
    avatar_url = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    projects = relationship("Project", back_populates="user")
    branding_assets = relationship("BrandingAsset", back_populates="user")
