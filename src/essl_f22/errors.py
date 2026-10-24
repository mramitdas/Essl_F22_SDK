"""Exceptions raised by the eSSL F22 SDK."""


class ESSL22Error(Exception):
    """Base class for all SDK errors."""


class DeviceConnectionError(ESSL22Error):
    """Raised when the device connection cannot be opened or is lost."""


class DeviceAuthenticationError(ESSL22Error):
    """Raised when the device rejects authentication."""


class DeviceTimeoutError(ESSL22Error):
    """Raised when a device operation times out."""


class ProtocolError(ESSL22Error):
    """Raised when a device response is malformed or truncated."""


class CommandError(ESSL22Error):
    """Raised when the device rejects a command."""

    def __init__(self, code: int, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or f"device returned error code 0x{code:04X}")


class DeviceVerificationError(ESSL22Error):
    """Raised when a device write cannot be verified."""


class UserNotFoundError(ESSL22Error):
    """Raised when a requested user does not exist on the device."""


class NoFreeTimeZoneSlotError(ESSL22Error):
    """Raised when no timezone slot is available for blocking."""


class StorageError(ESSL22Error):
    """Raised when local storage cannot be read or written."""


class StorageConfigurationError(StorageError):
    """Raised when a storage backend is unknown or misconfigured."""


class MirrorRecordNotFoundError(StorageError):
    """Raised when an offline mirror record does not exist."""


class SyncError(StorageError):
    """Raised when a mirror synchronization cannot be completed."""


class StateStoreError(StorageError):
    """Raised when local block state cannot be read or written."""
