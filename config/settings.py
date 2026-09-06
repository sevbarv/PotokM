from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str
    POTOK_API_TOKEN: str
    POTOK_API_BASE_URL: str = "https://app.potok.io/api/v3"
    AI_API_URL: str = "https://openrouter.ai/api/v1/chat/completions"
    AI_API_KEY: str
    AI_MODEL: str = "google/gemini-2.5-flash-preview-05-20"
    DATABASE_URL: str = "sqlite+aiosqlite:///hr_agent.db"
    TIMEZONE: str = "Europe/Moscow"
    DEFAULT_ADMIN_ID: int
    ENV: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
