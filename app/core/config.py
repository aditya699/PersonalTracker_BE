from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "PersonalTracker"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    MONGO_URI: str
    MONGO_DB_NAME: str = "personal_tracker"

    OPENAI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
