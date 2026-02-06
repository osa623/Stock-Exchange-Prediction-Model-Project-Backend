from pydantic_settings import BaseSettings, SettingsConfigDict

# backend db config

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Stock Platform Backend"
    ENV: str = "dev"
    DATABASE_URL: str = ""



settings = Settings()  