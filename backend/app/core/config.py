from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    database_url: str = "sqlite:///./inventory.db"
    jwt_secret_key: str = "replace-this-in-development"
    access_token_expire_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
