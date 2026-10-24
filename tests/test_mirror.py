from datetime import datetime
from typing import cast

import pytest

from essl_f22.errors import (
    MirrorRecordNotFoundError,
    SyncError,
    UserNotFoundError,
)
from essl_f22.mirror import Mirror, MirrorSnapshot
from essl_f22.models import (
    AttendanceRecord,
    DayInterval,
    DeviceInfo,
    FingerprintTemplate,
    GroupInfo,
    TimeZone,
    User,
)
from essl_f22.storage import (
    FingerprintMetadata,
    MemoryStorage,
    StorageBackend,
    SyncMode,
    SyncState,
)

DEVICE = "JJA1242200334"
NOW = datetime(2026, 10, 24, 12, 0, 0)


class FakeDevice:
    def __init__(self) -> None:
        self.serial = DEVICE
        self.info = DeviceInfo("ZLM60_TFT", "x 2008", DEVICE, "Ver 6.60")
        self.users = [
            User(uid=1, user_id="a", name="Alpha", group_id=1),
            User(uid=2, user_id="b", name="Beta", group_id=1),
        ]
        self.groups = [GroupInfo(1, 1, 0, 0, 0, False)]
        self.timezones = {
            1: TimeZone(1, (DayInterval(0, 0, 23, 59),) * 7),
        }
        self.fingerprints = [
            FingerprintTemplate(uid=1, fid=1, flag=1, template=b"abc"),
        ]
        self.attendance = [
            AttendanceRecord(1, "a", datetime(2026, 10, 24, 9, 0, 0), 1, 0),
        ]

    def get_serial_number(self) -> str:
        return self.serial

    def get_device_info(self) -> DeviceInfo:
        return self.info

    def list_users(self) -> list[User]:
        return list(self.users)

    def list_groups(self) -> list[GroupInfo]:
        return list(self.groups)

    def list_timezones(self) -> dict[int, TimeZone]:
        return dict(self.timezones)

    def list_fingerprints(self) -> list[FingerprintTemplate]:
        return list(self.fingerprints)

    def list_attendance(self) -> list[AttendanceRecord]:
        return list(self.attendance)


def _mirror(storage: StorageBackend) -> Mirror:
    return Mirror(storage, DEVICE, clock=lambda: NOW)


def test_full_sync_persists_records_and_metadata() -> None:
    storage = MemoryStorage()
    mirror = _mirror(storage)
    device = FakeDevice()

    result = mirror.sync(device, mode="full")

    assert result.device_serial == DEVICE
    assert result.mode == "full"
    assert result.synced_at == NOW
    assert result.users == 2
    assert result.groups == 1
    assert result.timezones == 1
    assert result.fingerprints == 1
    assert result.attendance == 1
    assert result.new_attendance == 1
    assert result.attendance_replaced is True
    assert mirror.device_serial == DEVICE
    assert mirror.get_device_info() == device.info
    assert mirror.list_users() == device.users
    assert mirror.get_user(1) == device.users[0]
    assert mirror.get_user_by_user_id("b") == device.users[1]
    assert mirror.list_groups() == device.groups
    assert mirror.get_group(1) == device.groups[0]
    assert mirror.list_timezones() == device.timezones
    assert mirror.get_timezone(1) == device.timezones[1]
    assert mirror.list_fingerprints() == [
        FingerprintMetadata(uid=1, fid=1, flag=1, size=9)
    ]
    assert mirror.get_user_fingerprints(1) == [
        FingerprintMetadata(uid=1, fid=1, flag=1, size=9)
    ]
    assert mirror.list_attendance() == device.attendance
    assert mirror.get_sync_state() == SyncState(
        device_serial=DEVICE,
        synced_at=NOW,
        mode="full",
        users=2,
        groups=1,
        timezones=1,
        fingerprints=1,
        attendance=1,
    )


def test_snapshot_returns_all_mirrored_records() -> None:
    storage = MemoryStorage()
    mirror = _mirror(storage)
    device = FakeDevice()
    mirror.sync(device, mode="full")

    snapshot = mirror.snapshot()

    assert isinstance(snapshot, MirrorSnapshot)
    assert snapshot.device_info == device.info
    assert snapshot.users == tuple(device.users)
    assert snapshot.groups == tuple(device.groups)
    assert snapshot.timezones == device.timezones
    assert snapshot.fingerprints == (FingerprintMetadata(uid=1, fid=1, flag=1, size=9),)
    assert snapshot.attendance == tuple(device.attendance)
    assert snapshot.sync_state is not None


def test_incremental_sync_upserts_only_new_attendance() -> None:
    storage = MemoryStorage()
    mirror = _mirror(storage)
    device = FakeDevice()
    mirror.sync(device, mode="full")
    device.attendance.append(
        AttendanceRecord(2, "b", datetime(2026, 10, 24, 10, 0, 0), 1, 0)
    )

    result = mirror.sync(device, mode="incremental")

    assert result.attendance == 2
    assert result.new_attendance == 1
    assert result.attendance_replaced is False
    assert mirror.list_attendance() == device.attendance

    repeated = mirror.sync(device, mode="incremental")

    assert repeated.new_attendance == 0
    assert mirror.attendance_count() == 2


def test_incremental_sync_replaces_attendance_when_device_count_drops() -> None:
    storage = MemoryStorage()
    mirror = _mirror(storage)
    device = FakeDevice()
    device.attendance.append(
        AttendanceRecord(2, "b", datetime(2026, 10, 24, 10, 0, 0), 1, 0)
    )
    mirror.sync(device, mode="full")
    device.attendance.pop()

    result = mirror.sync(device, mode="incremental")

    assert result.attendance == 1
    assert result.new_attendance == 1
    assert result.attendance_replaced is True
    assert mirror.list_attendance() == device.attendance


def test_incremental_sync_replaces_stale_users() -> None:
    storage = MemoryStorage()
    mirror = _mirror(storage)
    device = FakeDevice()
    mirror.sync(device, mode="full")
    device.users = [device.users[0]]

    mirror.sync(device, mode="incremental")

    assert mirror.list_users() == [device.users[0]]


def test_attendance_filters_are_applied_offline() -> None:
    storage = MemoryStorage()
    mirror = _mirror(storage)
    device = FakeDevice()
    device.attendance = [
        AttendanceRecord(1, "a", datetime(2026, 10, 24, 9, 0, 0), 1, 0),
        AttendanceRecord(2, "b", datetime(2026, 10, 24, 10, 0, 0), 1, 0),
        AttendanceRecord(1, "a", datetime(2026, 10, 24, 11, 0, 0), 1, 0),
    ]
    mirror.sync(device, mode="full")

    assert mirror.list_attendance(uid=1) == [device.attendance[0], device.attendance[2]]
    assert mirror.list_attendance(
        since=datetime(2026, 10, 24, 10, 0, 0),
        until=datetime(2026, 10, 24, 11, 0, 0),
    ) == [device.attendance[1], device.attendance[2]]
    assert mirror.list_attendance(limit=2) == device.attendance[:2]


def test_sync_rejects_mismatched_device_serial() -> None:
    storage = MemoryStorage()
    mirror = Mirror(storage, "OTHER", clock=lambda: NOW)

    with pytest.raises(SyncError):
        mirror.sync(FakeDevice(), mode="full")

    assert mirror.list_users() == []


def test_sync_rejects_unknown_mode() -> None:
    storage = MemoryStorage()
    mirror = _mirror(storage)

    with pytest.raises(SyncError):
        mirror.sync(FakeDevice(), mode=cast(SyncMode, "bogus"))


def test_missing_single_records_raise_typed_errors() -> None:
    storage = MemoryStorage()
    mirror = _mirror(storage)

    with pytest.raises(UserNotFoundError):
        mirror.get_user(99)
    with pytest.raises(UserNotFoundError):
        mirror.get_user_by_user_id("missing")
    with pytest.raises(MirrorRecordNotFoundError):
        mirror.get_group(99)
    with pytest.raises(MirrorRecordNotFoundError):
        mirror.get_timezone(99)


def test_empty_device_full_sync_clears_previous_data() -> None:
    storage = MemoryStorage()
    mirror = _mirror(storage)
    device = FakeDevice()
    mirror.sync(device, mode="full")
    device.users = []
    device.groups = []
    device.timezones = {}
    device.fingerprints = []
    device.attendance = []

    result = mirror.sync(device, mode="full")

    assert result.users == 0
    assert result.attendance == 0
    assert mirror.list_users() == []
    assert mirror.list_attendance() == []
    assert mirror.list_fingerprints() == []
