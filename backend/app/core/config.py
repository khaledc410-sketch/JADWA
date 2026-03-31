from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "JADWA"
    APP_NAME_AR: str = "جدوى"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://jadwa:jadwa_dev_pass@localhost:5432/jadwa"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-6"

    # Storage (S3-compatible)
    S3_BUCKET: str = "jadwa-reports"
    S3_ENDPOINT: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "me-south-1"  # Bahrain region (closest to Saudi)

    # Moyasar (Saudi payment gateway)
    MOYASAR_SECRET_KEY: Optional[str] = None
    MOYASAR_PUBLISHABLE_KEY: Optional[str] = None

    # Data seed path
    DATA_SEED_PATH: str = "/data-seed"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
