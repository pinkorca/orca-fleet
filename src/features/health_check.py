"""Health check feature for validating account sessions."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum, auto

from src.config import get_config
from src.core.client import TelegramClient
from src.core.session_manager import SessionManager
from src.utils.logger import get_logger


class AccountStatus(Enum):
    """Status of an account session."""

    ACTIVE = auto()
    EXPIRED = auto()
    BANNED = auto()
    ERROR = auto()


@dataclass
class AccountHealth:
    """Health check result for an account."""

    phone: str
    status: AccountStatus
    message: str
    name: str | None = None


class HealthChecker:
    """Checks health of all managed accounts."""

    def __init__(self) -> None:
        self.config = get_config()
        self.session_manager = SessionManager()
        self.logger = get_logger(__name__)

    async def check_account(self, phone: str) -> AccountHealth:
        """Check health of a single account."""
        session_path = self.session_manager.get_session_path(phone)
        client = TelegramClient(session_path, phone)

        try:
            await client.connect()
            is_valid, message = await client.check_session_valid()

            if is_valid:
                me = await client.get_me()
                name = None
                if me:
                    name = f"{me.first_name or ''} {me.last_name or ''}".strip() or None
                return AccountHealth(
                    phone=phone,
                    status=AccountStatus.ACTIVE,
                    message=message,
                    name=name,
                )
            status = AccountStatus.EXPIRED
            if "banned" in message.lower():
                status = AccountStatus.BANNED
            return AccountHealth(phone=phone, status=status, message=message)

        except Exception as e:
            self.logger.debug(f"Health check error for {phone}: {e}")
            return AccountHealth(
                phone=phone,
                status=AccountStatus.ERROR,
                message=str(e),
            )
        finally:
            await client.disconnect()

    async def check_all_accounts(
        self,
        progress_callback: callable | None = None,
    ) -> list[AccountHealth]:
        """
        Check health of all stored accounts.

        Args:
            progress_callback: Optional callback(current) for progress updates
        """
        phones = self.session_manager.get_all_phones()
        if not phones:
            return []

        results: list[AccountHealth] = []
        total = len(phones)

        for i, phone in enumerate(phones, 1):
            result = await self.check_account(phone)
            results.append(result)

            if progress_callback:
                progress_callback(i)

            # Small delay between checks to avoid rate limiting
            if i < total:
                await asyncio.sleep(0.5)

        return results

    def get_summary(self, results: list[AccountHealth]) -> dict[str, int]:
        """Get summary counts from health check results."""
        summary = {
            "total": len(results),
            "active": 0,
            "expired": 0,
            "banned": 0,
            "error": 0,
        }
        for result in results:
            if result.status == AccountStatus.ACTIVE:
                summary["active"] += 1
            elif result.status == AccountStatus.EXPIRED:
                summary["expired"] += 1
            elif result.status == AccountStatus.BANNED:
                summary["banned"] += 1
            else:
                summary["error"] += 1
        return summary
