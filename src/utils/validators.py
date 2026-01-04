"""Input validation utilities."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto


class ChannelType(Enum):
    """Type of channel/group input."""

    USERNAME = auto()  # @username or username
    INVITE_LINK = auto()  # t.me/+hash or t.me/joinchat/hash
    INVALID = auto()


@dataclass
class ChannelInput:
    """Parsed channel input."""

    original: str
    channel_type: ChannelType
    value: str  # username or invite hash

    @property
    def is_valid(self) -> bool:
        return self.channel_type != ChannelType.INVALID


def validate_phone(phone: str) -> tuple[bool, str]:
    """
    Validate and normalize phone number.
    Returns (is_valid, normalized_or_error_message).
    """
    # Remove spaces, dashes, parentheses
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)

    # Must start with + and contain only digits after
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned

    # Check format: + followed by 7-15 digits
    if not re.match(r"^\+\d{7,15}$", cleaned):
        return False, "Invalid format. Use international format: +1234567890"

    return True, cleaned


def parse_channel_input(text: str) -> ChannelInput:
    """Parse channel/group input into structured format."""
    text = text.strip()

    # Handle t.me/+hash format (private invite)
    private_match = re.match(r"(?:https?://)?t\.me/\+([a-zA-Z0-9_-]+)", text)
    if private_match:
        return ChannelInput(
            original=text,
            channel_type=ChannelType.INVITE_LINK,
            value=private_match.group(1),
        )

    # Handle t.me/joinchat/hash format (legacy private invite)
    joinchat_match = re.match(r"(?:https?://)?t\.me/joinchat/([a-zA-Z0-9_-]+)", text)
    if joinchat_match:
        return ChannelInput(
            original=text,
            channel_type=ChannelType.INVITE_LINK,
            value=joinchat_match.group(1),
        )

    # Handle t.me/username format (public channel)
    public_match = re.match(r"(?:https?://)?t\.me/([a-zA-Z][a-zA-Z0-9_]{3,30}[a-zA-Z0-9])$", text)
    if public_match:
        return ChannelInput(
            original=text,
            channel_type=ChannelType.USERNAME,
            value=public_match.group(1),
        )

    # Handle @username format
    at_match = re.match(r"^@([a-zA-Z][a-zA-Z0-9_]{3,30}[a-zA-Z0-9])$", text)
    if at_match:
        return ChannelInput(
            original=text,
            channel_type=ChannelType.USERNAME,
            value=at_match.group(1),
        )

    # Handle plain username
    plain_match = re.match(r"^([a-zA-Z][a-zA-Z0-9_]{3,30}[a-zA-Z0-9])$", text)
    if plain_match:
        return ChannelInput(
            original=text,
            channel_type=ChannelType.USERNAME,
            value=plain_match.group(1),
        )

    return ChannelInput(original=text, channel_type=ChannelType.INVALID, value="")
