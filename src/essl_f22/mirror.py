"""Read-only offline mirror and synchronization."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from essl_f22.errors import (
    MirrorRecordNotFoundError,
    SyncError,
    UserNotFoundError,
)
from essl_f22.models import (
    AttendanceRecord,
    DeviceInfo,
    FingerprintTemplate,
    GroupInfo,
    TimeZone,
    User,
)
from essl_f22.storage import (
    AttendanceEntry,
    FingerprintMetadata,
    StorageBackend,
    SyncMode,
    SyncResult,
    SyncState,
)
from essl_f22.storage.codec import attendance_record_key


class DeviceLike(Protocol):
    """Device reads consumed by the offline mirror."""

    def get_serial_number(self) -> str: ...

    def get_device_info(self) -> DeviceInfo: ...

    def list_users(self) -> list[User]: ...

    def list_groups(self) -> list[GroupInfo]: ...

    def list_timezones(self) -> dict[int, TimeZone]: ...

    def list_fingerprints(self) -> list[FingerprintTemplate]: ...

    def list_attendance(self) -> list[AttendanceRecord]: ...


@dataclass(frozen=True, slots=True)
class MirrorSnapshot:
    device_info: DeviceInfo | None
    users: tuple[User, ...]
    groups: tuple[GroupInfo, ...]
    timezones: dict[int, TimeZone]
    fingerprints: tuple[FingerprintMetadata, ...]
    attendance: tuple[AttendanceRecord, ...]
    sync_state: SyncState | None


class Mirror:
    """Read-only offline view of a single device."""

    def __init__(
        self,
        storage: StorageBackend,
        device_serial: str,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._storage = storage
        self._device_serial = device_serial
        self._clock = clock if clock is not None else lambda: datetime.now()

    @property
    def device_serial(self) -> str:
        return self._device_serial

    def sync(self, device: DeviceLike, mode: SyncMode = "incremental") -> SyncResult:
        if mode not in ("full", "incremental"):
            raise SyncError(f"unsupported sync mode {mode!r}")
        if device.get_serial_number() != self._device_serial:
            raise SyncError(
                f"device serial {device.get_serial_number()!r} does not match "
                f"mirror serial {self._device_serial!r}"
            )

        info = device.get_device_info()
        users = device.list_users()
        groups = device.list_groups()
        timezones = device.list_timezones()
        fingerprints = [
            FingerprintMetadata(
                uid=template.uid,
                fid=template.fid,
                flag=template.flag,
                size=template.size,
            )
            for template in device.list_fingerprints()
        ]
        entries = [
            AttendanceEntry(attendance_record_key(record), record)
            for record in device.list_attendance()
        ]

        self._storage.save_device_info(self._device_serial, info)
        self._storage.replace_users(self._device_serial, users)
        self._storage.replace_groups(self._device_serial, groups)
        self._storage.replace_timezones(self._device_serial, timezones)
        self._storage.replace_fingerprints(self._device_serial, fingerprints)

        if mode == "full":
            self._storage.replace_attendance(self._device_serial, entries)
            new_attendance = len(entries)
            attendance_replaced = True
        else:
            current_count = self._storage.attendance_count(self._device_serial)
            if len(entries) < current_count:
                self._storage.replace_attendance(self._device_serial, entries)
                new_attendance = len(entries)
                attendance_replaced = True
            else:
                new_attendance = self._storage.upsert_attendance(
                    self._device_serial, entries
                )
                attendance_replaced = False

        synced_at = self._clock()
        attendance = self._storage.attendance_count(self._device_serial)
        state = SyncState(
            device_serial=self._device_serial,
            synced_at=synced_at,
            mode=mode,
            users=len(users),
            groups=len(groups),
            timezones=len(timezones),
            fingerprints=len(fingerprints),
            attendance=attendance,
        )
        self._storage.save_sync_state(self._device_serial, state)
        return SyncResult(
            device_serial=self._device_serial,
            mode=mode,
            synced_at=synced_at,
            users=len(users),
            groups=len(groups),
            timezones=len(timezones),
            fingerprints=len(fingerprints),
            attendance=attendance,
            new_attendance=new_attendance,
            attendance_replaced=attendance_replaced,
        )

    def get_device_info(self) -> DeviceInfo | None:
        return self._storage.get_device_info(self._device_serial)

    def list_users(self) -> list[User]:
        return self._storage.list_users(self._device_serial)

    def get_user(self, uid: int) -> User:
        user = self._storage.get_user(self._device_serial, uid)
        if user is None:
            raise UserNotFoundError(f"user uid {uid} was not found in the mirror")
        return user

    def get_user_by_user_id(self, user_id: str) -> User:
        for user in self.list_users():
            if user.user_id == user_id:
                return user
        raise UserNotFoundError(f"user id {user_id!r} was not found in the mirror")

    def list_fingerprints(self) -> list[FingerprintMetadata]:
        return self._storage.list_fingerprints(self._device_serial)

    def get_user_fingerprints(self, uid: int) -> list[FingerprintMetadata]:
        return [
            fingerprint
            for fingerprint in self.list_fingerprints()
            if fingerprint.uid == uid
        ]

    def list_attendance(
        self,
        *,
        uid: int | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
    ) -> list[AttendanceRecord]:
        return self._storage.list_attendance(
            self._device_serial,
            uid=uid,
            since=since,
            until=until,
            limit=limit,
        )

    def attendance_count(self) -> int:
        return self._storage.attendance_count(self._device_serial)

    def list_timezones(self) -> dict[int, TimeZone]:
        return self._storage.list_timezones(self._device_serial)

    def get_timezone(self, slot: int) -> TimeZone:
        timezone = self._storage.get_timezone(self._device_serial, slot)
        if timezone is None:
            raise MirrorRecordNotFoundError(
                f"timezone slot {slot} was not found in the mirror"
            )
        return timezone

    def list_groups(self) -> list[GroupInfo]:
        return self._storage.list_groups(self._device_serial)

    def get_group(self, group_id: int) -> GroupInfo:
        group = self._storage.get_group(self._device_serial, group_id)
        if group is None:
            raise MirrorRecordNotFoundError(
                f"group {group_id} was not found in the mirror"
            )
        return group

    def get_sync_state(self) -> SyncState | None:
        return self._storage.get_sync_state(self._device_serial)

    def snapshot(self) -> MirrorSnapshot:
        return MirrorSnapshot(
            device_info=self.get_device_info(),
            users=tuple(self.list_users()),
            groups=tuple(self.list_groups()),
            timezones=self.list_timezones(),
            fingerprints=tuple(self.list_fingerprints()),
            attendance=tuple(self.list_attendance()),
            sync_state=self.get_sync_state(),
        )
