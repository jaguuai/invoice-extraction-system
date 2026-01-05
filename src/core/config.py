"""
Core Configuration
Central configuration management using Pydantic Settings
Reads from environment variables and .env file
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # ==========================================
    # APPLICATION
    # ==========================================
    APP_NAME: str = "invoice-extraction-system"
    ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # ==========================================
    # API
    # ==========================================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # ==========================================
    # REDIS
    # ==========================================
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ==========================================
    # OLLAMA (Local LLM)
    # ==========================================
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    USE_LOCAL_LLM: bool = True
    
    # ==========================================
    # OPENAI (Fallback API)
    # ==========================================
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # ==========================================
    # ANTHROPIC (Alternative)
    # ==========================================
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"
    
    # ==========================================
    # PRIVACY & KVKK COMPLIANCE
    # ==========================================
    PRIVACY_MODE: str = "smart"  # smart, always_local, always_api
    DATA_RETENTION_HOURS: int = 24
    AUTO_DELETE_UPLOADS: bool = True
    
    # ==========================================
    # OCR SETTINGS
    # ==========================================
    TESSERACT_LANG: str = "tur+eng"
    OCR_DPI: int = 300
    
    # ==========================================
    # VALIDATION
    # ==========================================
    VAT_RATE: float = 0.18
    ARITHMETIC_TOLERANCE: float = 0.01  # 1 kuruş tolerance
    
    # ==========================================
    # FILE STORAGE (FIXED - Relative Paths)
    # ==========================================
    UPLOAD_DIR: str = "./data/uploads"
    PROCESSED_DIR: str = "./data/processed"
    TEMP_DIR: str = "./data/temp"
    
    # ==========================================
    # LOGGING (FIXED - Relative Path)
    # ==========================================
    LOG_DIR: str = "./logs"
    LOG_ROTATION: str = "100 MB"
    LOG_RETENTION: str = "10 days"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_settings() -> Settings:
    """Get settings instance (for FastAPI dependency injection)"""
    return settings


def is_production() -> bool:
    """Check if running in production"""
    return settings.ENV == "production"


def is_development() -> bool:
    """Check if running in development"""
    return settings.ENV == "development"