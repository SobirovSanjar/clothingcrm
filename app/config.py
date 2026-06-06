"""Application configuration loaded from environment variables / .env file."""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central configuration object."""

    APP_NAME: str = os.getenv("APP_NAME", "ClothCRM")
    APP_DESCRIPTION: str = (
        "Cloud CRM for a wholesale clothing company (ERP / CRM / WMS scenario)"
    )

    # SQLAlchemy async URL. Example:
    #   postgresql+asyncpg://crm:crm@localhost:5432/crm
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://crm:crm@localhost:5432/crm",
    )

    # Used to sign session cookies. CHANGE THIS in production.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # Session lifetime in seconds (default 8 hours).
    SESSION_MAX_AGE: int = int(os.getenv("SESSION_MAX_AGE", str(8 * 60 * 60)))

    # Connection pool tuning (relevant for the cloud load-balancing / scaling story).
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))


settings = Settings()
