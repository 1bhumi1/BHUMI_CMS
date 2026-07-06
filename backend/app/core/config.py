from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ==========================
    # Application
    # ==========================
    APP_NAME: str = "College Management System API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ==========================
    # Database
    # ==========================
    DATABASE_URL: str
    SYNC_DATABASE_URL: str

    # ==========================
    # JWT Security
    # ==========================
    SECRET_KEY: str
    JWT_SECRET: str
    JWT_REFRESH_SECRET: str

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12

    # ==========================
    # Gemini AI
    # ==========================
    GEMINI_API_KEY: str
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # ==========================
    # MCP
    # ==========================
    MCP_SERVER_URL: str = "http://localhost:8001"

    # ==========================
    # CORS
    # ==========================
    ALLOWED_HOSTS: str = "localhost,127.0.0.1,*"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ==========================
    # Rate Limiting
    # ==========================
    RATE_LIMIT_PER_MINUTE: int = 60

    # ==========================
    # Redis
    # ==========================
    REDIS_URL: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return []

        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def allowed_hosts_list(self) -> List[str]:
        if not self.ALLOWED_HOSTS:
            return []

        return [
            host.strip()
            for host in self.ALLOWED_HOSTS.split(",")
            if host.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"


settings = Settings()