# Core layer - session management, Telethon client wrapper, exceptions
from src.core.client import TelegramClient
from src.core.exceptions import AuthenticationError, OrcaFleetError, SessionError
from src.core.session_manager import SessionManager

__all__ = [
    "AuthenticationError",
    "OrcaFleetError",
    "SessionError",
    "SessionManager",
    "TelegramClient",
]
