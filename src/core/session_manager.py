"""Session management for Telegram accounts."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from src.config import get_config
from src.core.exceptions import SessionNotFoundError

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass
class SessionInfo:
    """Information about a stored session."""

    phone: str
    session_path: Path

    @property
    def session_name(self) -> str:
        """Get session name without extension for Telethon."""
        return str(self.session_path.with_suffix(""))

    @property
    def exists(self) -> bool:
        """Check if session file exists."""
        return self.session_path.exists()


class SessionManager:
    """Manages Telegram session files."""

    def __init__(self) -> None:
        self.config = get_config()
        self.sessions_dir = self.config.sessions_dir

    def _phone_to_filename(self, phone: str) -> str:
        """Convert phone number to safe filename."""
        # Remove + and any non-digit characters, keep only numbers
        clean = "".join(c for c in phone if c.isdigit())
        return f"session_{clean}"

    def get_session_info(self, phone: str) -> SessionInfo:
        """Get session info for a phone number."""
        filename = self._phone_to_filename(phone)
        session_path = self.sessions_dir / f"{filename}.session"
        return SessionInfo(phone=phone, session_path=session_path)

    def get_session_path(self, phone: str) -> str:
        """Get the session path (without .session extension) for Telethon."""
        info = self.get_session_info(phone)
        return info.session_name

    def list_sessions(self) -> Iterator[SessionInfo]:
        """List all stored sessions."""
        for session_file in self.sessions_dir.glob("session_*.session"):
            # Extract phone from filename: session_1234567890.session -> 1234567890
            phone = session_file.stem.replace("session_", "")
            yield SessionInfo(phone=phone, session_path=session_file)

    def get_session_count(self) -> int:
        """Get the number of stored sessions."""
        return sum(1 for _ in self.list_sessions())

    def session_exists(self, phone: str) -> bool:
        """Check if a session exists for the given phone."""
        return self.get_session_info(phone).exists

    def delete_session(self, phone: str) -> None:
        """Delete a session file."""
        info = self.get_session_info(phone)
        if not info.exists:
            raise SessionNotFoundError(f"Session for {phone} not found")

        info.session_path.unlink()

        # Also remove journal file if it exists
        journal = info.session_path.with_suffix(".session-journal")
        if journal.exists():
            journal.unlink()

    def get_all_phones(self) -> list[str]:
        """Get all phone numbers with stored sessions."""
        return [session.phone for session in self.list_sessions()]
