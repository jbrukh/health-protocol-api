from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    health_tracker_api_token: str
    health_tracker_database_path: str = "./data/health.db"


settings = Settings()
