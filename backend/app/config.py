"""
Application Configuration
Loads environment variables and provides configuration settings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str
    
    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI Models
    YOLO_MODEL_PATH: str = "models_ai/best.pt"
    
    # Azure AI Foundry
    AZURE_AI_ENDPOINT: str = ""
    AZURE_AI_API_KEY: str = ""
    LLM_PROVIDER: str = "azure"
    
    # Azure Computer Vision (separate from LLM endpoint)
    AZURE_CV_ENDPOINT: str = "https://stockit-foundry.services.ai.azure.com"
    
    # Azure LLM endpoint (Llama 3.3)
    AZURE_LLM_ENDPOINT: str = ""
    
    # Ollama (alternative)
    OLLAMA_ENDPOINT: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    
    # Application
    DEBUG: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "StockIT API"
    VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
