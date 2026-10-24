"""Storage protocols consumed by device, blocking, and mirror APIs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Protocol

from essl_f22.models import (
    AttendanceRecord,
    DeviceInfo,
    GroupInfo,
    TimeZone,
    User,
    UserTimeZone,
)
from essl_f22.storage.models import (
    AttendanceEntry,
    BlockTimeZoneState,
    FingerprintMetadata,
    SyncState,
)


class BlockStateStore(Protocol):
    """Persistence required for non-destructive user blocking."""

    def get_original_user_timezone(
        self, device_serial: str, uid: int
    ) -> UserTimeZone | None: ...

    def save_original_user_timezone(
        self, device_serial: str, uid: int, timezone: UserTimeZone
    ) -> None: ...

    def delete_original_user_timezone(self, device_serial: str, uid: int) -> None: ...

    def list_blocked_uids(self, device_serial: str) -> list[int]: ...

    def get_block_timezone(self, device_serial: str) -> BlockTimeZoneState | None: ...

    def save_block_timezone(self, device_serial: str, slot: int) -> None: ...


class MirrorStore(Protocol):
    """Read-only offline mirror of device data."""

    def save_device_info(self, device_serial: str, info: DeviceInfo) -> None: ...

    def get_device_info(self, device_serial: str) -> DeviceInfo | None: ...

    def replace_users(self, device_serial: str, users: Iterable[User]) -> None: ...

    def list_users(self, device_serial: str) -> list[User]: ...

    def get_user(self, device_serial: str, uid: int) -> User | None: ...

    def replace_groups(
        self, device_serial: str, groups: Iterable[GroupInfo]
    ) -> None: ...

    def list_groups(self, device_serial: str) -> list[GroupInfo]: ...

    def get_group(self, device_serial: str, group_id: int) -> GroupInfo | None: ...

    def replace_timezones(
        self, device_serial: str, timezones: Mapping[int, TimeZone]
    ) -> None: ...

    def list_timezones(self, device_serial: str) -> dict[int, TimeZone]: ...

    def get_timezone(self, device_serial: str, slot: int) -> TimeZone | None: ...

    def replace_fingerprints(
        self, device_serial: str, fingerprints: Iterable[FingerprintMetadata]
    ) -> None: ...

    def list_fingerprints(self, device_serial: str) -> list[FingerprintMetadata]: ...

    def upsert_attendance(
        self, device_serial: str, entries: Iterable[AttendanceEntry]
    ) -> int: ...

    def replace_attendance(
        self, device_serial: str, entries: Iterable[AttendanceEntry]
    ) -> None: ...

    def list_attendance(
        self,
        device_serial: str,
        *,
        uid: int | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
    ) -> list[AttendanceRecord]: ...

    def attendance_count(self, device_serial: str) -> int: ...

    def save_sync_state(self, device_serial: str, state: SyncState) -> None: ...

    def get_sync_state(self, device_serial: str) -> SyncState | None: ...

    def clear_device(self, device_serial: str) -> None: ...


class StorageBackend(BlockStateStore, MirrorStore, Protocol):
    """A complete local storage backend."""

    def close(self) -> None: ...
