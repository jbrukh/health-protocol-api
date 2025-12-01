from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://localhost/health_protocol"

    @field_validator("database_url", mode="before")
    @classmethod
    def convert_postgres_url(cls, v: str) -> str:
        """Convert Railway's postgresql:// to postgresql+asyncpg:// for async support."""
        if v and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    api_key: str = "change-me-in-production"
    environment: str = "development"

    # Server URL for OpenAPI (auto-detected on Railway)
    server_url: Optional[str] = None
    railway_public_domain: Optional[str] = None

    @property
    def openapi_server_url(self) -> Optional[str]:
        """Get the server URL for OpenAPI schema."""
        if self.server_url:
            return self.server_url
        if self.railway_public_domain:
            return f"https://{self.railway_public_domain}"
        return None

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
