"""orca-fleet: Multi-Account Telegram Manager.

Entry point for the application.
"""

from __future__ import annotations

import sys

from src.config import get_config
from src.menu.menu import MainMenu
from src.utils.logger import setup_logger


def main() -> int:
    """Application entry point."""
    try:
        # Initialize logging
        setup_logger()

        # Validate config exists (will be checked again in menu with user feedback)
        get_config()

        # Run the main menu
        menu = MainMenu()
        menu.run()

        return 0

    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
