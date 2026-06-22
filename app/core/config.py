from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from typing import List
import json
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Application
    app_name: str = "IT Support Chatbot v2.0"
    debug: bool = False

    # LLM Provider
    llm_provider: str = Field(default="groq", alias="LLM_PROVIDER")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")

    # Storage
    chroma_dir: str = Field(default="./storage/chromadb", alias="CHROMA_DIR")
    docs_dir: str = Field(default="./storage/docs", alias="DOCS_DIR")

    # Authentication
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_expiry_hours: int = Field(default=24, alias="JWT_EXPIRY_HOURS")

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")

    # CORS - Now properly defined
    cors_allowed_origins: List[str] = Field(
        default=["http://localhost:3000"],
        alias="CORS_ALLOWED_ORIGINS"
    )

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            try:
                # Try to parse as JSON
                return json.loads(v)
            except json.JSONDecodeError:
                # If JSON fails, split by comma
                return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        populate_by_name = True
        extra = "ignore"  # Ignore extra fields from .env

settings = Settings()
logger.info(f"✓ Settings loaded successfully")
logger.info(f"  CORS enabled for: {settings.cors_allowed_origins}")