from pydantic import BaseSettings
from typing import Optional
class Settings(BaseSettings): # pyright: ignore[reportGeneralTypeIssues]
    # Database
    DATABASE_URL: Optional[str] = "sqlite:///./data/chroma_db/chroma.sqlite3"
    # LLM / AI service
    GEMINI_API_KEY: Optional[str] = None
    groq_api_key: Optional[str] = None
    secret_key: Optional[str] = None
    # App Configuration
    app_name: str = "MedAI"
    app_env: str = "development"
    debug: bool = True
    # URLs
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"
    # Voice Settings
    voice_language: str = "en-US"
    supported_languages: str = "en,am"
    class Config:
        extra = "allow"
        env_file = ".env"
        case_sensitive = False


# Settings instance
settings = Settings()


