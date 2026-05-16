from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Finance WebApp"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/finance_db"
    SQLITE_URL: str = "sqlite:///./finance.db"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Provider API keys (empty string = use free tier / no auth)
    FINNHUB_API_KEY: str = ""
    COINGECKO_API_KEY: str = ""

    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
