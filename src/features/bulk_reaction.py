"""Bulk reaction feature for sending reactions with multiple accounts."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Callable

from src.config import get_config
from src.core.client import TelegramClient
from src.core.session_manager import SessionManager
from src.utils.logger import get_logger
from src.utils.validators import MessageLinkType, parse_message_link


@dataclass
class ReactionResult:
    """Result of a single reaction operation."""

    phone: str
    success: bool
    message: str


@dataclass
class BulkReactionResult:
    """Aggregated result of bulk reaction operation."""

    target: str
    emoji: str
    results: list[ReactionResult]

    @property
    def successful_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.success)


class BulkReactor:
    """Handles sending reactions with multiple accounts."""

    def __init__(self) -> None:
        self.config = get_config()
        self.session_manager = SessionManager()
        self.logger = get_logger(__name__)

    def _get_random_delay(self) -> float:
        """Get random delay between reactions to avoid rate limiting."""
        return random.uniform(self.config.join_delay_min, self.config.join_delay_max)

    async def react_with_account(
        self,
        phone: str,
        peer: str,
        message_id: int,
        emoji: str,
        is_private: bool,
    ) -> ReactionResult:
        """Send a reaction with a single account."""
        session_path = self.session_manager.get_session_path(phone)
        client = TelegramClient(session_path, phone)

        try:
            await client.connect()

            if not await client.is_authorized():
                return ReactionResult(
                    phone=phone,
                    success=False,
                    message="Session expired",
                )

            if is_private:
                entity = await client.resolve_entity(int(f"-100{peer}"))
            else:
                entity = await client.resolve_entity(peer)

            success, message = await client.send_reaction(entity, message_id, emoji)
            return ReactionResult(phone=phone, success=success, message=message)

        except Exception as e:
            self.logger.debug(f"Reaction error for {phone}: {e}")
            return ReactionResult(phone=phone, success=False, message=str(e))
        finally:
            await client.disconnect()

    async def bulk_react(
        self,
        message_link: str,
        emoji: str,
        phones: list[str] | None = None,
        progress_callback: Callable[[int, ReactionResult], None] | None = None,
    ) -> BulkReactionResult:
        """
        Send a reaction with multiple accounts.

        Args:
            message_link: Message link (t.me/channel/123 or t.me/c/ID/123)
            emoji: Emoji to react with
            phones: Optional list of phones to use (default: all accounts)
            progress_callback: Optional callback(current, result) for progress

        Returns:
            BulkReactionResult with all individual results
        """
        parsed = parse_message_link(message_link)
        if not parsed.is_valid:
            return BulkReactionResult(
                target=message_link,
                emoji=emoji,
                results=[
                    ReactionResult(
                        phone="N/A",
                        success=False,
                        message=f"Invalid message link: {message_link}",
                    ),
                ],
            )

        is_private = (
            parsed.link_type
            in (
                MessageLinkType.PRIVATE_CHANNEL,
                MessageLinkType.TOPIC_MESSAGE,
            )
            and parsed.peer.isdigit()
        )

        if phones is None:
            phones = self.session_manager.get_all_phones()

        if not phones:
            return BulkReactionResult(
                target=message_link,
                emoji=emoji,
                results=[
                    ReactionResult(
                        phone="N/A",
                        success=False,
                        message="No accounts available",
                    ),
                ],
            )

        results: list[ReactionResult] = []
        total = len(phones)

        for i, phone in enumerate(phones, 1):
            result = await self.react_with_account(
                phone,
                parsed.peer,
                parsed.message_id,
                emoji,
                is_private,
            )
            results.append(result)

            if progress_callback:
                progress_callback(i, result)

            if i < total:
                delay = self._get_random_delay()
                self.logger.debug(f"Waiting {delay:.1f}s before next reaction")
                await asyncio.sleep(delay)

        return BulkReactionResult(target=message_link, emoji=emoji, results=results)
