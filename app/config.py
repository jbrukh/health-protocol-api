from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    health_tracker_api_token: str
    health_tracker_database_path: str = "./data/health.db"

    # Withings integration
    withings_client_id: str | None = None
    withings_client_secret: str | None = None
    base_url: str | None = None  # e.g., https://your-app.railway.app

settings = Settings()
