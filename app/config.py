"""
Application configuration settings
"""
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "AI English Tutor"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # Database MySQL
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: str = "phi123455"
    DATABASE_NAME: str = "english_ai_speak"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct MySQL database URL"""
        return f"mysql+pymysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    # JWT Security
    SECRET_KEY: str = "webtienganhAI"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # AI Services - OhMyGPT (OpenAI-compatible API)
    OHMYGPT_API_KEY: Optional[str] = None
    OHMYGPT_BASE_URL: str = "https://api.ohmygpt.com/v1"
    OHMYGPT_MODEL: str = "gpt-4o-mini"
    OHMYGPT_TEMPERATURE: float = 0.7
    OHMYGPT_MAX_TOKENS: int = 2000
    
    # Deepgram API - Speech Recognition & Pronunciation
    DEEPGRAM_API_KEY: Optional[str] = None
    DEEPGRAM_MODEL: str = "nova-2"
    DEEPGRAM_SMART_FORMAT: bool = True
    DEEPGRAM_PUNCTUATE: bool = True
    DEEPGRAM_LANGUAGE: str = "en-US"


    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_AUDIO_FORMATS: List[str] = ["mp3", "wav", "m4a", "ogg"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # CORS - Allow multiple origins for development
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:5500",  # Live Server / FE
        "http://127.0.0.1:3000",
        "*"  # Allow all origins in development (remove in production!)
    ]
    
    # Redis (Optional)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
