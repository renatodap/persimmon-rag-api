"""
Application configuration using Pydantic Settings.
All environment variables are validated on startup.
"""
from typing import List
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_KEY: str = Field(..., description="Supabase anonymous key")
    SUPABASE_SERVICE_KEY: str = Field(..., description="Supabase service role key")

    # AI APIs
    ANTHROPIC_API_KEY: str = Field(..., description="Anthropic API key for Claude")
    GOOGLE_GEMINI_API_KEY: str = Field(..., description="Google Gemini API key")
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")

    # Application
    ENVIRONMENT: str = Field("development", description="Environment (development/production)")
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    ALLOWED_ORIGINS: str = Field(
        "http://localhost:3000", description="Comma-separated CORS origins"
    )

    # JWT
    JWT_SECRET: str = Field(..., description="JWT secret key")
    JWT_ALGORITHM: str = Field("HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, description="JWT expiration in minutes")

    # Rate Limiting
    REDIS_URL: str = Field("redis://localhost:6379", description="Redis URL for rate limiting")

    # Webhooks
    WEBHOOK_SECRET: str = Field(
        "default-webhook-secret-change-in-production",
        description="Secret for signing webhook payloads",
    )

    # Server
    PORT: int = Field(8000, description="Server port")
    HOST: str = Field("0.0.0.0", description="Server host")

    @validator("JWT_SECRET")
    def validate_jwt_secret(cls, v: str) -> str:
        """Ensure JWT secret is sufficiently long."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v

    @validator("ALLOWED_ORIGINS")
    def parse_allowed_origins(cls, v: str) -> List[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in v.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Global settings instance
settings = Settings()
