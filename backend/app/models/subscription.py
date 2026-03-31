import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan = Column(String(20), nullable=False)  # basic | pro | enterprise
    status = Column(
        String(20), default="active"
    )  # active | cancelled | past_due | trialing
    moyasar_subscription_id = Column(String(100))
    moyasar_customer_id = Column(String(100))
    reports_used_this_month = Column(Integer, default=0)
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Plan limits
    PLAN_LIMITS = {
        "basic": {
            "reports_per_month": 2,
            "sectors": 2,
            "languages": ["ar"],
            "pages": 40,
        },
        "pro": {
            "reports_per_month": 10,
            "sectors": 4,
            "languages": ["ar", "en"],
            "pages": 50,
        },
        "enterprise": {
            "reports_per_month": -1,
            "sectors": 4,
            "languages": ["ar", "en"],
            "pages": 55,
        },
    }

    # SAR pricing
    PLAN_PRICES_SAR = {
        "basic": 99,
        "pro": 299,
        "enterprise": 799,
    }

    user = relationship("User", back_populates="subscriptions")
