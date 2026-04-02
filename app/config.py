from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/safety_wearable"
    SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    OPENAI_API_KEY: str = ""

    FALL_CONFIRM_TIMEOUT_SECONDS: int = 5
    APP_NAME: str = "SmartSafetyWearable"
    DEBUG: bool = True

    model_config = {"env_file": ".env", "case_sensitive": True}


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
