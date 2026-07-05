import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    APP_NAME: str = "College Management System API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str
    SYNC_DATABASE_URL: str

    # Security
    SECRET_KEY: str
    JWT_SECRET: str
    JWT_REFRESH_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12

    # CORS & Trusted Hosts
    ALLOWED_HOSTS: str = "localhost,127.0.0.1,*"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Redis Cache
    REDIS_URL: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        """
        Split the CORS_ORIGINS string by comma to get a list of origins.
        """
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

settings = Settings()
