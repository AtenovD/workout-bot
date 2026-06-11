from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Bot
    bot_token: str
    admin_ids: list[int] = []

    # Database
    database_url: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "workout_bot"
    postgres_user: str = "workout_user"
    postgres_password: str = ""

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # S3
    s3_endpoint: str = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "workout-bot-media"
    s3_public_url: str = "http://localhost:9000/workout-bot-media"

    # Sentry
    sentry_dsn: Optional[str] = None

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    webhook_host: Optional[str] = None
    webhook_path: str = "/webhook"
    api_secret: str = "secret"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
