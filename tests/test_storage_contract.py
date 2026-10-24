import os
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import pytest

from essl_f22.errors import StateStoreError
from essl_f22.models import (
    AttendanceRecord,
    DayInterval,
    DeviceInfo,
    GroupInfo,
    TimeZone,
    User,
    UserTimeZone,
)
from essl_f22.storage import (
    AttendanceEntry,
    BlockTimeZoneState,
    FingerprintMetadata,
    JsonFileStorage,
    MemoryStorage,
    SqliteStorage,
    StorageBackend,
    SyncState,
    create_storage,
)
from essl_f22.storage.codec import attendance_record_key

DEVICE = "JJA1242200334"
OTHER_DEVICE = "OTHER123"


@pytest.fixture(params=["memory", "json", "sqlite", "postgres", "mysql"])
def storage(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[StorageBackend]:
    if request.param == "memory":
        store: StorageBackend = MemoryStorage()
    elif request.param == "json":
        store = JsonFileStorage(tmp_path / "mirror.json")
    elif request.param == "sqlite":
        store = SqliteStorage(tmp_path / "state.db")
    elif request.param == "postgres":
        dsn = os.environ.get("ESSL_F22_POSTGRES_DSN")
        if not dsn:
            pytest.skip("ESSL_F22_POSTGRES_DSN is not set")
        store = create_storage("postgres", options={"dsn": dsn})
    else:
        dsn = os.environ.get("ESSL_F22_MYSQL_DSN")
        if not dsn:
            pytest.skip("ESSL_F22_MYSQL_DSN is not set")
        store = create_storage("mysql", options={"dsn": dsn})
    store.clear_device(DEVICE)
    store.clear_device(OTHER_DEVICE)
    yield store
    store.clear_device(DEVICE)
    store.clear_device(OTHER_DEVICE)
    store.close()


def _user(uid: int, user_id: str, name: str = "") -> User:
    return User(uid=uid, user_id=user_id, name=name)


def _attendance(
    uid: int, user_id: str, timestamp: datetime, status: int = 1, punch: int = 0
) -> AttendanceRecord:
    return AttendanceRecord(
        uid=uid,
        user_id=user_id,
        timestamp=timestamp,
        status=status,
        punch=punch,
    )


def _entry(record: AttendanceRecord) -> AttendanceEntry:
    return AttendanceEntry(attendance_record_key(record), record)


def test_original_user_timezone_round_trips(storage: StorageBackend) -> None:
    original = UserTimeZone(295, False, 0, 0, 0)

    storage.save_original_user_timezone(DEVICE, 295, original)

    assert storage.get_original_user_timezone(DEVICE, 295) == original
    assert storage.list_blocked_uids(DEVICE) == [295]


def test_missing_original_user_timezone_is_none(storage: StorageBackend) -> None:
    assert storage.get_original_user_timezone(DEVICE, 999) is None


def test_delete_original_user_timezone(storage: StorageBackend) -> None:
    storage.save_original_user_timezone(DEVICE, 295, UserTimeZone(295, False, 0, 0, 0))

    storage.delete_original_user_timezone(DEVICE, 295)

    assert storage.get_original_user_timezone(DEVICE, 295) is None
    assert storage.list_blocked_uids(DEVICE) == []


def test_save_original_user_timezone_rejects_mismatched_uid(
    storage: StorageBackend,
) -> None:
    with pytest.raises(StateStoreError):
        storage.save_original_user_timezone(
            DEVICE, 295, UserTimeZone(999, False, 0, 0, 0)
        )


def test_block_timezone_round_trips(storage: StorageBackend) -> None:
    assert storage.get_block_timezone(DEVICE) is None

    storage.save_block_timezone(DEVICE, 50)

    assert storage.get_block_timezone(DEVICE) == BlockTimeZoneState(50)


def test_device_info_round_trips(storage: StorageBackend) -> None:
    info = DeviceInfo("ZLM60_TFT", "x 2008", DEVICE, "Ver 6.60")
    assert storage.get_device_info(DEVICE) is None

    storage.save_device_info(DEVICE, info)

    assert storage.get_device_info(DEVICE) == info


def test_users_replace_list_and_get(storage: StorageBackend) -> None:
    users = [_user(2, "b", "Beta"), _user(1, "a", "Alpha")]

    storage.replace_users(DEVICE, users)

    assert storage.list_users(DEVICE) == [users[1], users[0]]
    assert storage.get_user(DEVICE, 1) == users[1]
    assert storage.get_user(DEVICE, 999) is None


def test_replacing_users_with_empty_list_clears_them(storage: StorageBackend) -> None:
    storage.replace_users(DEVICE, [_user(1, "a")])

    storage.replace_users(DEVICE, [])

    assert storage.list_users(DEVICE) == []


def test_groups_replace_list_and_get(storage: StorageBackend) -> None:
    groups = [
        GroupInfo(2, 2, 0, 0, 14, False),
        GroupInfo(1, 1, 0, 0, 0, True),
    ]

    storage.replace_groups(DEVICE, groups)

    assert storage.list_groups(DEVICE) == [groups[1], groups[0]]
    assert storage.get_group(DEVICE, 2) == groups[0]
    assert storage.get_group(DEVICE, 99) is None


def test_timezones_replace_list_and_get(storage: StorageBackend) -> None:
    allow_all = TimeZone(1, (DayInterval(0, 0, 23, 59),) * 7)
    deny_all = TimeZone(6, (DayInterval(23, 59, 0, 0),) * 7)

    storage.replace_timezones(DEVICE, {6: deny_all, 1: allow_all})

    assert storage.list_timezones(DEVICE) == {1: allow_all, 6: deny_all}
    assert storage.get_timezone(DEVICE, 6) == deny_all
    assert storage.get_timezone(DEVICE, 99) is None


def test_fingerprints_replace_and_list(storage: StorageBackend) -> None:
    fingerprints = [
        FingerprintMetadata(uid=2, fid=1, flag=1, size=900),
        FingerprintMetadata(uid=1, fid=2, flag=1, size=800),
        FingerprintMetadata(uid=1, fid=1, flag=1, size=700),
    ]

    storage.replace_fingerprints(DEVICE, fingerprints)

    assert storage.list_fingerprints(DEVICE) == [
        fingerprints[2],
        fingerprints[1],
        fingerprints[0],
    ]


def test_attendance_replace_list_count_and_filters(storage: StorageBackend) -> None:
    first = _attendance(1, "a", datetime(2026, 10, 24, 10, 0, 0))
    second = _attendance(2, "b", datetime(2026, 10, 24, 11, 0, 0))
    third = _attendance(1, "a", datetime(2026, 10, 24, 12, 0, 0))

    storage.replace_attendance(
        DEVICE,
        [_entry(second), _entry(third), _entry(first)],
    )

    assert storage.attendance_count(DEVICE) == 3
    assert storage.list_attendance(DEVICE) == [first, second, third]
    assert storage.list_attendance(DEVICE, uid=1) == [first, third]
    assert storage.list_attendance(
        DEVICE,
        since=datetime(2026, 10, 24, 11, 0, 0),
        until=datetime(2026, 10, 24, 12, 0, 0),
    ) == [second, third]
    assert storage.list_attendance(DEVICE, limit=2) == [first, second]


def test_attendance_upsert_is_idempotent_and_returns_new_count(
    storage: StorageBackend,
) -> None:
    first = _attendance(1, "a", datetime(2026, 10, 24, 10, 0, 0))
    second = _attendance(1, "a", datetime(2026, 10, 24, 11, 0, 0))
    storage.replace_attendance(DEVICE, [_entry(first)])

    new_count = storage.upsert_attendance(
        DEVICE,
        [_entry(first), _entry(second), _entry(second)],
    )

    assert new_count == 1
    assert storage.attendance_count(DEVICE) == 2
    assert storage.list_attendance(DEVICE) == [first, second]


def test_replacing_attendance_with_empty_list_clears_it(
    storage: StorageBackend,
) -> None:
    storage.replace_attendance(
        DEVICE,
        [_entry(_attendance(1, "a", datetime(2026, 10, 24, 10, 0, 0)))],
    )

    storage.replace_attendance(DEVICE, [])

    assert storage.attendance_count(DEVICE) == 0
    assert storage.list_attendance(DEVICE) == []


def test_sync_state_round_trips(storage: StorageBackend) -> None:
    state = SyncState(
        device_serial=DEVICE,
        synced_at=datetime(2026, 10, 24, 12, 0, 0),
        mode="incremental",
        users=295,
        groups=1,
        timezones=2,
        fingerprints=266,
        attendance=100,
    )
    assert storage.get_sync_state(DEVICE) is None

    storage.save_sync_state(DEVICE, state)

    assert storage.get_sync_state(DEVICE) == state


def test_clear_device_clears_only_that_device(storage: StorageBackend) -> None:
    storage.save_device_info(DEVICE, DeviceInfo("a", "b", DEVICE, "c"))
    storage.replace_users(DEVICE, [_user(1, "a")])
    storage.replace_users(OTHER_DEVICE, [_user(2, "b")])
    storage.save_original_user_timezone(DEVICE, 1, UserTimeZone(1, False, 0, 0, 0))
    storage.save_block_timezone(DEVICE, 50)
    storage.save_block_timezone(OTHER_DEVICE, 49)
    storage.save_sync_state(
        DEVICE,
        SyncState(
            device_serial=DEVICE,
            synced_at=datetime(2026, 10, 24, 12, 0, 0),
            mode="full",
            users=1,
            groups=0,
            timezones=0,
            fingerprints=0,
            attendance=0,
        ),
    )

    storage.clear_device(DEVICE)

    assert storage.get_device_info(DEVICE) is None
    assert storage.list_users(DEVICE) == []
    assert storage.list_users(OTHER_DEVICE) == [_user(2, "b")]
    assert storage.list_blocked_uids(DEVICE) == []
    assert storage.get_block_timezone(DEVICE) is None
    assert storage.get_block_timezone(OTHER_DEVICE) == BlockTimeZoneState(49)
    assert storage.get_sync_state(DEVICE) is None


def test_json_file_persists_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "mirror.json"
    first = JsonFileStorage(path)
    first.save_block_timezone(DEVICE, 50)
    first.close()

    second = JsonFileStorage(path)

    assert second.get_block_timezone(DEVICE) == BlockTimeZoneState(50)
    second.close()
