from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "JM Camera Sourcing AI"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/jm_camera"
    redis_url: str = "redis://redis:6379/0"
    ebay_marketplace_deletion_verification_token: str = ""
    ebay_marketplace_deletion_endpoint_url: str = ""
    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    ebay_marketplace_id: str = "EBAY_US"
    yahoo_fetch_mode: str = "fallback"
    yahoo_request_min_delay_seconds: float = 0.2
    yahoo_request_max_delay_seconds: float = 0.8
    yahoo_request_timeout_seconds: float = 10.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
