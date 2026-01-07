"""Bulk leave feature for leaving channels/groups with multiple accounts."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Callable

from src.config import get_config
from src.core.client import TelegramClient
from src.core.session_manager import SessionManager
from src.utils.logger import get_logger
from src.utils.validators import ChannelType, parse_channel_input


@dataclass
class LeaveResult:
    """Result of a single leave operation."""

    phone: str
    success: bool
    message: str


@dataclass
class BulkLeaveResult:
    """Aggregated result of bulk leave operation."""

    target: str
    results: list[LeaveResult]

    @property
    def successful_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.success)


class BulkLeaver:
    """Handles leaving channels/groups with multiple accounts."""

    def __init__(self) -> None:
        self.config = get_config()
        self.session_manager = SessionManager()
        self.logger = get_logger(__name__)

    def _get_random_delay(self) -> float:
        """Get random delay between leaves to avoid rate limiting."""
        return random.uniform(self.config.join_delay_min, self.config.join_delay_max)

    async def leave_with_account(
        self,
        phone: str,
        target: str,
        is_invite: bool,
    ) -> LeaveResult:
        """Leave a channel/group with a single account."""
        session_path = self.session_manager.get_session_path(phone)
        client = TelegramClient(session_path, phone)

        try:
            await client.connect()

            if not await client.is_authorized():
                return LeaveResult(
                    phone=phone,
                    success=False,
                    message="Session expired",
                )

            if is_invite:
                success, message = await client.leave_by_invite(target)
            else:
                success, message = await client.leave_channel(target)

            return LeaveResult(phone=phone, success=success, message=message)

        except Exception as e:
            self.logger.debug(f"Leave error for {phone}: {e}")
            return LeaveResult(phone=phone, success=False, message=str(e))
        finally:
            await client.disconnect()

    async def bulk_leave(
        self,
        target_input: str,
        phones: list[str] | None = None,
        progress_callback: Callable[[int, LeaveResult], None] | None = None,
    ) -> BulkLeaveResult:
        """
        Leave a channel/group with multiple accounts.

        Args:
            target_input: Channel username, t.me link, or invite link
            phones: Optional list of phones to use (default: all accounts)
            progress_callback: Optional callback(current, result) for progress

        Returns:
            BulkLeaveResult with all individual results
        """
        # Parse the target input
        parsed = parse_channel_input(target_input)
        if not parsed.is_valid:
            return BulkLeaveResult(
                target=target_input,
                results=[
                    LeaveResult(
                        phone="N/A",
                        success=False,
                        message=f"Invalid target: {target_input}",
                    ),
                ],
            )

        is_invite = parsed.channel_type == ChannelType.INVITE_LINK
        target = parsed.value

        # Get accounts to use
        if phones is None:
            phones = self.session_manager.get_all_phones()

        if not phones:
            return BulkLeaveResult(
                target=target_input,
                results=[
                    LeaveResult(
                        phone="N/A",
                        success=False,
                        message="No accounts available",
                    ),
                ],
            )

        results: list[LeaveResult] = []
        total = len(phones)

        for i, phone in enumerate(phones, 1):
            result = await self.leave_with_account(phone, target, is_invite)
            results.append(result)

            if progress_callback:
                progress_callback(i, result)

            # Add delay between leaves (except for the last one)
            if i < total:
                delay = self._get_random_delay()
                self.logger.debug(f"Waiting {delay:.1f}s before next leave")
                await asyncio.sleep(delay)

        return BulkLeaveResult(target=target_input, results=results)
