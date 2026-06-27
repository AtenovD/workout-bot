from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Telegram
    BOT_TOKEN: str
    ADMIN_IDS: str = ""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://workout_user:secret@localhost:5432/workout_bot"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "workout_bot"
    POSTGRES_USER: str = "workout_user"
    POSTGRES_PASSWORD: str = "secret"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # S3
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET: str = "workout-bot-media"
    S3_PUBLIC_URL: Optional[str] = None

    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    API_SECRET: str = "change_me"

    # AI coach
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_TIMEOUT_SECONDS: float = 8.0

    @property
    def admin_ids_list(self) -> list[int]:
        return [int(x) for x in self.ADMIN_IDS.split(",") if x.strip()]


settings = Settings()
