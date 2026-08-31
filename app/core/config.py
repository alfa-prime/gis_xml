from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_api_key: str = Field(
        validation_alias="APP_API_KEY"
    )
    logs_level: str = Field(
        default="INFO",
        validation_alias="LOGS_LEVEL",
    )
    gateway_url: str = Field(
        validation_alias="GATEWAY_URL",
    )

    gateway_request_endpoint: str = Field(
        validation_alias="GATEWAY_REQUEST_ENDPOINT",
    )

    gateway_api_key: str = Field(
        validation_alias="GATEWAY_API_KEY",
    )

    gateway_session_id: str = Field(
        validation_alias="GATEWAY_SESSION_ID",
    )

    request_timeout: float = Field(
        default=30.0,
        validation_alias="REQUEST_TIMEOUT",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # noqa
