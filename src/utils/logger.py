"""Logging configuration for orca-fleet."""
from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from src.config import get_config

if TYPE_CHECKING:
    pass

_loggers: dict[str, logging.Logger] = {}


def setup_logger() -> None:
    """Configure the root logger for the application."""
    config = get_config()

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (only warnings and above to avoid cluttering CLI)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)

    # File handler (all logs)
    log_file = config.logs_dir / "orca-fleet.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger("src")
    root_logger.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Suppress noisy Telethon logs
    logging.getLogger("telethon").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module."""
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
    return _loggers[name]
