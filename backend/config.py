"""
AI Chatbot — Configuration
Created by: Satyam Tiwari (iamsatyampandit@gmail.com)

Central place for every environment-driven setting. Nothing else in the
codebase should read os.environ directly — import `settings` instead.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

def _database_url() -> str:
    """
    Resolve the database URL.

    - If DATABASE_URL is set (e.g. a PostgreSQL URL provided by a host like
      Render/Railway/Heroku), use it as-is. Those platforms often hand out
      URLs starting with 'postgres://', which SQLAlchemy 2.x no longer
      accepts — it must be 'postgresql://', so we patch it here.
    - Otherwise fall back to a local SQLite file, so the project runs
      out of the box with zero external setup.
    """
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return "sqlite:///./chatbot.db"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


@dataclass(frozen=True)
class Settings:
    # --- App metadata ---
    APP_NAME: str = "Tiwari"
    CREATOR_NAME: str = "Satyam Tiwari"
    CREATOR_EMAIL: str = "iamsatyampandit@gmail.com"
    VERSION: str = "1.0.0"

    # --- Database ---
    DATABASE_URL: str = _database_url()

    # --- AI provider ---
    # Works with Anthropic's Messages API by default. Point AI_API_URL /
    # AI_API_KEY / AI_MODEL at any compatible chat-completions style API.
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "anthropic").strip().lower()
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_API_URL: str = os.getenv("AI_API_URL", "https://api.anthropic.com/v1/messages")
    AI_MODEL: str = os.getenv("AI_MODEL", "claude-sonnet-4-6")
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "1024"))
    AI_SYSTEM_PROMPT: str = os.getenv(
        "AI_SYSTEM_PROMPT",
        "You are a helpful, concise AI assistant embedded in a web chat "
        "application built by Satyam Tiwari.",
    )

    # --- Server ---
    HOST: str = os.getenv("HOST", "0.0.0.0")
    FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "8000"))
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    CORS_ORIGINS: list = tuple(
        o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")
    )


settings = Settings()
