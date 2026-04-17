"""Application settings and defaults."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Runtime configuration loaded from environment or defaults."""

    model_config = SettingsConfigDict(
        env_prefix="TALKING_AVATAR_",
        extra="ignore",
    )

    app_name: str = "Talking Avatar Generator"
    database_url: str = "sqlite:///./talking_avatar_generator.db"
    asset_dir: Path = Path("./var/avatar_assets")
    max_image_size_bytes: int = Field(default=5 * 1024 * 1024, ge=1)
    max_script_length: int = Field(default=300, ge=1)
    default_voice: str = "Default Voice"
