from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.example", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="auth-service", validation_alias="APP_NAME")
    env: str = Field(default="local", validation_alias="ENV")
    jwt_secret: str = Field(default="change_me_super_secret", validation_alias="JWT_SECRET")
    jwt_alg: str = Field(default="HS256", validation_alias="JWT_ALG")
    access_token_expire_minutes: int = Field(default=60, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    sqlite_path: str = Field(default="./auth.db", validation_alias="SQLITE_PATH")
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        db_path = Path(self.sqlite_path)
        if not db_path.is_absolute():
            db_path = Path.cwd() / db_path
        return f"sqlite+aiosqlite:///{db_path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()