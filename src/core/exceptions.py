"""Custom exceptions for orca-fleet."""
from __future__ import annotations


class OrcaFleetError(Exception):
    """Base exception for all orca-fleet errors."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error


class ConfigurationError(OrcaFleetError):
    """Raised when configuration is invalid or missing."""


class SessionError(OrcaFleetError):
    """Raised for session-related errors."""


class SessionNotFoundError(SessionError):
    """Raised when a requested session does not exist."""


class SessionExpiredError(SessionError):
    """Raised when a session has expired or been revoked."""


class AuthenticationError(OrcaFleetError):
    """Raised for authentication failures."""


class PhoneCodeError(AuthenticationError):
    """Raised when phone code verification fails."""


class TwoFactorError(AuthenticationError):
    """Raised when 2FA password is incorrect."""


class AccountBannedError(OrcaFleetError):
    """Raised when an account has been banned or restricted."""


class RateLimitError(OrcaFleetError):
    """Raised when hitting Telegram rate limits."""

    def __init__(self, message: str, wait_seconds: int) -> None:
        super().__init__(message)
        self.wait_seconds = wait_seconds


class EntityNotFoundError(OrcaFleetError):
    """Raised when a channel/group/user cannot be resolved."""


class JoinError(OrcaFleetError):
    """Raised when joining a channel/group fails."""
