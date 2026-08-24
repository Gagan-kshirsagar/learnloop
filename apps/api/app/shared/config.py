from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LEARNLOOP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "LearnLoop API"
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/learnloop"
    secret_key: str = "dev-secret-key-change-in-prod"

    # Auth configuration
    auth_provider: str = "jwt"
    jwt_secret_key: str = "dev-jwt-secret-key-change-in-prod"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # AI / Tutor configuration
    google_api_key: str = ""
    llm_provider: str = "gemini"
    embeddings_provider: str = "gemini"
    rag_score_threshold: float = 0.05


@lru_cache
def get_settings() -> Settings:
    return Settings()
