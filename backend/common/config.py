from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

# backend db config

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Application
    APP_NAME: str = "Stock Platform Backend"
    ENV: str = "dev"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    
    # Security - CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Firebase Authentication
    FIREBASE_PROJECT_ID: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Secret Key (for any future JWT/session needs)
    SECRET_KEY: str = "change-this-in-production"


settings = Settings()  