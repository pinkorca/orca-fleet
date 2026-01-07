"""Configuration management for orca-fleet."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


class Config:
    """Application configuration loaded from environment variables."""

    _instance: Config | None = None

    def __new__(cls) -> Config:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        load_dotenv()

        # Project paths
        self.project_root = Path(__file__).parent.parent
        self.sessions_dir = self.project_root / "data" / "sessions"
        self.logs_dir = self.project_root / "logs"

        # Ensure directories exist
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Telegram API credentials
        self.api_id: int = int(os.getenv("API_ID", "0"))
        self.api_hash: str = os.getenv("API_HASH", "")

        # Rate limiting for bulk operations
        self.join_delay_min: int = int(os.getenv("JOIN_DELAY_MIN", "30"))
        self.join_delay_max: int = int(os.getenv("JOIN_DELAY_MAX", "60"))

        # Logging
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def is_configured(self) -> bool:
        """Check if API credentials are properly configured."""
        return self.api_id != 0 and len(self.api_hash) > 0

    def validate(self) -> None:
        """Raise error if configuration is invalid."""
        if not self.is_configured:
            raise ValueError(
                "Telegram API credentials not configured. "
                "Please set API_ID and API_HASH in .env file. "
                "Get credentials from https://my.telegram.org",
            )


def get_config() -> Config:
    """Get the global configuration instance."""
    return Config()
