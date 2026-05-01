from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Finance WebApp"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/finance_db"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    SECRET_KEY: str = "change-me-in-production"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
