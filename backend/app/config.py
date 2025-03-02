from pydantic_settings import BaseSettings
from typing import Optional
import os
import logging
import sys

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # API Settings
    API_BASE_URL: str
    FOOTBALL_API_KEY: str
    RAPIDAPI_HOST: str

    # Database Settings
    db_name: str
    db_user: str
    db_password: str
    db_host: str
    db_port: str
    
    # Redis Settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str 

    # PGAdmin settings
    PGADMIN_EMAIL: str 
    PGADMIN_PASSWORD: str 

    OPENAI_API_KEY: Optional[str] = None

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

# Initialize settings with better error handling
try:
    settings = Settings()
    logger.info(f"Successfully loaded configuration. Database host: {settings.db_host}, Redis host: {settings.REDIS_HOST}")
except Exception as e:
    logger.error(f"Error loading configuration: {e}")
    logger.error("Environment variables are not properly set. Please check your .env file or Docker environment variables.")
    sys.exit(1)