from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Meta WhatsApp Cloud API Settings
    whatsapp_api_base_url: str = Field(
        default="https://graph.facebook.com",
        alias="WHATSAPP_API_BASE_URL",
    )
    whatsapp_api_version: str = Field(
        default="v20.0",
        alias="WHATSAPP_API_VERSION",
    )
    whatsapp_access_token: str = Field(
        default="",
        alias="WHATSAPP_ACCESS_TOKEN",
    )
    whatsapp_phone_number_id: str = Field(
        default="",
        alias="WHATSAPP_PHONE_NUMBER_ID",
    )
    whatsapp_waba_id: str = Field(
        default="",
        alias="WHATSAPP_WABA_ID",
    )

    # Application Settings
    app_env: str = Field(default="development", alias="APP_ENV")
    dry_run: bool = Field(default=True, alias="DRY_RUN")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    cors_origins: List[str] = Field(default=["*"], alias="CORS_ORIGINS")

    @property
    def is_configured_for_live(self) -> bool:
        """Returns True if minimum credentials for Meta Cloud API are present and DRY_RUN is False."""
        return bool(
            not self.dry_run
            and self.whatsapp_access_token.strip()
            and self.whatsapp_phone_number_id.strip()
        )

    @property
    def messages_endpoint(self) -> str:
        """Constructs the Meta Graph API messages endpoint."""
        base = self.whatsapp_api_base_url.rstrip("/")
        version = self.whatsapp_api_version.strip("/")
        phone_id = self.whatsapp_phone_number_id.strip()
        return f"{base}/{version}/{phone_id}/messages"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
