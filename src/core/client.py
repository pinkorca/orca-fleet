"""Telethon client wrapper with connection management and error handling."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from telethon import TelegramClient as TelethonClient
from telethon.errors import (
    AuthKeyUnregisteredError,
    FloodWaitError,
    InviteHashExpiredError,
    InviteHashInvalidError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    PhoneNumberBannedError,
    PhoneNumberInvalidError,
    SessionPasswordNeededError,
    UserAlreadyParticipantError,
    UserDeactivatedBanError,
)
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest

from src.config import get_config
from src.core.exceptions import (
    AccountBannedError,
    AuthenticationError,
    EntityNotFoundError,
    PhoneCodeError,
    RateLimitError,
    TwoFactorError,
)
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from telethon.tl.types import User


class TelegramClient:
    """Wrapper around Telethon client with enhanced error handling."""

    def __init__(self, session_path: str, phone: str) -> None:
        self.config = get_config()
        self.phone = phone
        self.session_path = session_path
        self.logger = get_logger(__name__)

        self._client = TelethonClient(
            session_path,
            self.config.api_id,
            self.config.api_hash,
            device_model="Desktop",
            system_version="Windows 10",
            app_version="4.16.8",
            lang_code="en",
            system_lang_code="en-US",
        )

    async def __aenter__(self) -> TelegramClient:
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.disconnect()

    async def connect(self) -> None:
        """Connect to Telegram."""
        await self._client.connect()

    async def disconnect(self) -> None:
        """Disconnect from Telegram."""
        await self._client.disconnect()

    async def is_authorized(self) -> bool:
        """Check if the client is authorized."""
        try:
            return await self._client.is_user_authorized()
        except AuthKeyUnregisteredError:
            return False

    async def send_code(self) -> str:
        """Send login code to phone. Returns phone_code_hash."""
        try:
            result = await self._client.send_code_request(self.phone)
            return result.phone_code_hash
        except PhoneNumberInvalidError as e:
            raise AuthenticationError(
                f"Invalid phone number: {self.phone}", original_error=e
            ) from e
        except PhoneNumberBannedError as e:
            raise AccountBannedError(
                f"Phone number {self.phone} is banned", original_error=e
            ) from e
        except FloodWaitError as e:
            raise RateLimitError(
                f"Too many requests. Wait {e.seconds} seconds.", wait_seconds=e.seconds
            ) from e

    async def sign_in(
        self,
        phone_code_hash: str,
        code: str,
        password: str | None = None,
    ) -> User:
        """Sign in with code and optional 2FA password."""
        try:
            user = await self._client.sign_in(
                phone=self.phone, code=code, phone_code_hash=phone_code_hash
            )
            return user
        except SessionPasswordNeededError as e:
            if not password:
                raise TwoFactorError("2FA password required but not provided") from e
            return await self._sign_in_2fa(password)
        except PhoneCodeInvalidError as e:
            raise PhoneCodeError("Invalid verification code", original_error=e) from e
        except PhoneCodeExpiredError as e:
            raise PhoneCodeError("Verification code expired", original_error=e) from e
        except FloodWaitError as e:
            raise RateLimitError(
                f"Too many attempts. Wait {e.seconds} seconds.", wait_seconds=e.seconds
            ) from e

    async def _sign_in_2fa(self, password: str) -> User:
        """Complete 2FA sign in."""
        try:
            return await self._client.sign_in(password=password)
        except Exception as e:
            raise TwoFactorError(f"2FA authentication failed: {e}", original_error=e) from e

    async def get_me(self) -> User | None:
        """Get current user info."""
        try:
            return await self._client.get_me()
        except (AuthKeyUnregisteredError, UserDeactivatedBanError):
            return None

    async def check_session_valid(self) -> tuple[bool, str]:
        """Check if session is valid. Returns (is_valid, status_message)."""
        try:
            me = await self.get_me()
            if me is None:
                return False, "Session expired or account banned"
            name = f"{me.first_name or ''} {me.last_name or ''}".strip() or "Unknown"
            return True, f"Active ({name})"
        except AuthKeyUnregisteredError:
            return False, "Session expired"
        except UserDeactivatedBanError:
            return False, "Account banned"
        except Exception as e:
            return False, f"Error: {e}"

    async def join_channel(self, channel: str) -> tuple[bool, str]:
        """Join a public channel by username."""
        try:
            entity = await self._client.get_entity(channel)
            await self._client(JoinChannelRequest(entity))
            return True, "Joined successfully"
        except UserAlreadyParticipantError:
            return True, "Already a member"
        except FloodWaitError as e:
            return False, f"Rate limited: wait {e.seconds}s"
        except Exception as e:
            self.logger.debug(f"Join channel error: {e}")
            return False, str(e)

    async def join_by_invite(self, invite_hash: str) -> tuple[bool, str]:
        """Join a channel/group by invite hash."""
        try:
            await self._client(ImportChatInviteRequest(invite_hash))
            return True, "Joined successfully"
        except UserAlreadyParticipantError:
            return True, "Already a member"
        except InviteHashExpiredError:
            return False, "Invite link expired"
        except InviteHashInvalidError:
            return False, "Invalid invite link"
        except FloodWaitError as e:
            return False, f"Rate limited: wait {e.seconds}s"
        except Exception as e:
            self.logger.debug(f"Join invite error: {e}")
            return False, str(e)

    async def resolve_entity(self, target: str) -> Any:
        """Resolve a username, link, or ID to an entity."""
        try:
            return await self._client.get_entity(target)
        except Exception as e:
            raise EntityNotFoundError(f"Could not resolve: {target}", original_error=e) from e
