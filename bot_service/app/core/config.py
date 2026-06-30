from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.example", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="bot-service", validation_alias="APP_NAME")
    env: str = Field(default="local", validation_alias="ENV")
    bot_token: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
    jwt_secret: str = Field(default="change_me_super_secret", validation_alias="JWT_SECRET")
    jwt_alg: str = Field(default="HS256", validation_alias="JWT_ALG")
    redis_url: str = Field(default="redis://192.168.1.98:6379/0", validation_alias="REDIS_URL")
    rabbitmq_url: str = Field(default="amqp://guest:guest@192.168.1.98:5672//", validation_alias="RABBITMQ_URL")
    openrouter_api_key: str = Field(default="", validation_alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", validation_alias="OPENROUTER_BASE_URL")
    openrouter_model: str = Field(default="stepfun/step-3.5-flash:free", validation_alias="OPENROUTER_MODEL")
    openrouter_site_url: str = Field(default="https://example.com", validation_alias="OPENROUTER_SITE_URL")
    openrouter_app_name: str = Field(default="bot-service", validation_alias="OPENROUTER_APP_NAME")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()