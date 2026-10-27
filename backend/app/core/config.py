import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SafeQR-Cloud Backend"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    
    # Cloud Connections
    UPSTASH_REDIS_REST_URL: str = os.getenv("UPSTASH_REDIS_REST_URL", "")
    UPSTASH_REDIS_REST_TOKEN: str = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Telegram Emergency Webhook
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "8739682883:AAGXiSPNEWTug5FidnWuflCXuqRwpyZalfU")
    DEFAULT_GUARDIAN_CHAT_ID: str = os.getenv("DEFAULT_GUARDIAN_CHAT_ID", "5456687635")

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
