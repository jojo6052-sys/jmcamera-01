from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "JM Camera Sourcing AI"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/jm_camera"
    redis_url: str = "redis://redis:6379/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
