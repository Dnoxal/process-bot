from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    discord_token: str = Field(default="", alias="DISCORD_TOKEN")
    discord_command_prefix: str = Field(default="!", alias="DISCORD_COMMAND_PREFIX")
    discord_guild_id: int | None = Field(default=None, alias="DISCORD_GUILD_ID")
    allowed_channel_ids_raw: str = Field(default="", alias="PROCESS_ALLOWED_CHANNEL_IDS")
    database_url: str = Field(
        default=f"sqlite:///{Path.cwd() / 'data' / 'process_bot.db'}",
        alias="DATABASE_URL",
    )
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    @field_validator("discord_guild_id", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @property
    def allowed_channel_ids(self) -> set[int]:
        if not self.allowed_channel_ids_raw.strip():
            return set()
        return {
            int(channel_id.strip())
            for channel_id in self.allowed_channel_ids_raw.split(",")
            if channel_id.strip()
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
