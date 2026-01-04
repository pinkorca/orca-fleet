"""Account management feature."""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from src.config import get_config
from src.core.client import TelegramClient
from src.core.exceptions import (
    AuthenticationError,
    PhoneCodeError,
    RateLimitError,
    TwoFactorError,
)
from src.core.session_manager import SessionManager
from src.utils.logger import get_logger
from src.utils.validators import validate_phone

if TYPE_CHECKING:
    pass


class AccountManager:
    """Manages Telegram account operations."""

    def __init__(self) -> None:
        self.config = get_config()
        self.session_manager = SessionManager()
        self.logger = get_logger(__name__)

    async def add_account(
        self,
        phone: str,
        get_code: Callable[[], str],
        get_2fa_password: Callable[[], str] | None = None,
    ) -> tuple[bool, str]:
        """
        Add a new account with interactive authentication.

        Args:
            phone: Phone number in international format
            get_code: Callback to get verification code from user
            get_2fa_password: Optional callback to get 2FA password

        Returns:
            Tuple of (success, message)
        """
        # Validate phone number
        is_valid, result = validate_phone(phone)
        if not is_valid:
            return False, result
        phone = result

        # Check if session already exists
        if self.session_manager.session_exists(phone):
            return False, f"Account {phone} already exists"

        session_path = self.session_manager.get_session_path(phone)
        client = TelegramClient(session_path, phone)

        try:
            await client.connect()

            # Check if already authorized (resuming session)
            if await client.is_authorized():
                me = await client.get_me()
                name = f"{me.first_name or ''} {me.last_name or ''}".strip() if me else "Unknown"
                return True, f"Account {phone} ({name}) already authorized"

            # Send verification code
            self.logger.info(f"Sending code to {phone}")
            phone_code_hash = await client.send_code()

            # Get code from user
            code = get_code()
            if not code:
                return False, "No verification code provided"

            # Try to sign in
            try:
                user = await client.sign_in(phone_code_hash, code)
                name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                return True, f"Successfully added {phone} ({name})"

            except TwoFactorError:
                # 2FA required
                if not get_2fa_password:
                    return False, "2FA password required but no callback provided"

                password = get_2fa_password()
                if not password:
                    return False, "No 2FA password provided"

                user = await client.sign_in(phone_code_hash, code, password)
                name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                return True, f"Successfully added {phone} ({name})"

        except RateLimitError as e:
            return False, f"Rate limited. Please wait {e.wait_seconds} seconds"
        except PhoneCodeError as e:
            return False, str(e)
        except AuthenticationError as e:
            return False, str(e)
        except Exception as e:
            self.logger.exception(f"Failed to add account {phone}")
            return False, f"Unexpected error: {e}"
        finally:
            await client.disconnect()

    async def remove_account(self, phone: str) -> tuple[bool, str]:
        """Remove an account and delete its session."""
        try:
            self.session_manager.delete_session(phone)
            return True, f"Removed account {phone}"
        except Exception as e:
            return False, str(e)

    def list_accounts(self) -> list[str]:
        """Get list of all account phone numbers."""
        return self.session_manager.get_all_phones()

    def get_account_count(self) -> int:
        """Get total number of accounts."""
        return self.session_manager.get_session_count()
