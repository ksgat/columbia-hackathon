"""
Configuration management using pydantic-settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App
    app_name: str = "Prophecy API"
    debug: bool = True

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    # Database (Supabase provides PostgreSQL)
    database_url: str = ""

    # OpenRouter API (for Claude and other LLMs)
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-opus-4-6"  # Prophet uses Opus 4.6

    # Redis (optional for now)
    redis_url: str = "redis://localhost:6379"

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # CORS
    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Convenience instance
settings = get_settings()
