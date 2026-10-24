from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

import essl_f22
from essl_f22 import (
    BlockResult,
    Device,
    SyncResult,
    UnblockResult,
    UserTimeZone,
)
from essl_f22.protocol import CMD_OPTIONS_RRQ, Response
from essl_f22.storage import MemoryStorage, StorageBackend
from tests.fakes import FakeSession

PUBLIC_NAMES = [
    "AccessDevice",
    "AttendanceEntry",
    "AttendanceRecord",
    "BlockManager",
    "BlockResult",
    "BlockStateStore",
    "BlockTimeZoneState",
    "CommandError",
    "DayInterval",
    "Device",
    "DeviceAuthenticationError",
    "DeviceConnectionError",
    "DeviceInfo",
    "DeviceLike",
    "DeviceTimeoutError",
    "DeviceVerificationError",
    "ESSL22Error",
    "FingerprintMetadata",
    "FingerprintTemplate",
    "FreeSizes",
    "GroupInfo",
    "JsonFileStorage",
    "MemoryStorage",
    "Mirror",
    "MirrorRecordNotFoundError",
    "MirrorSnapshot",
    "MirrorStore",
    "NoFreeTimeZoneSlotError",
    "ProtocolError",
    "SqliteBlockStateStore",
    "SqliteStorage",
    "StateStoreError",
    "StorageBackend",
    "StorageConfigurationError",
    "StorageError",
    "SyncError",
    "SyncMode",
    "SyncResult",
    "SyncState",
    "TimeZone",
    "UnblockResult",
    "User",
    "UserNotFoundError",
    "UserTimeZone",
    "create_storage",
    "default_data_dir",
    "default_mirror_path",
    "default_state_path",
]


class TrackingStorage(MemoryStorage):
    def __init__(self) -> None:
        super().__init__()
        self.closed = False

    def close(self) -> None:
        self.closed = True


def _serial_session() -> FakeSession:
    return FakeSession(
        {CMD_OPTIONS_RRQ: Response(2000, b"~SerialNumber=JJA1242200334\x00", 0, 0)}
    )


def test_public_exports_are_importable() -> None:
    assert essl_f22.__version__ == "0.1.0"
    assert hasattr(essl_f22, "__version__")
    assert not hasattr(essl_f22, "add")
    assert "add" not in essl_f22.__all__
    for name in PUBLIC_NAMES:
        assert hasattr(essl_f22, name), name
    assert set(PUBLIC_NAMES).issubset(essl_f22.__all__)


def test_construction_does_not_create_storage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[tuple[str, Path | str | None, dict[str, Any] | None]] = []
    storage = TrackingStorage()

    def fake_create(
        backend: str = "sqlite",
        *,
        path: Path | str | None = None,
        options: dict[str, Any] | None = None,
    ) -> StorageBackend:
        created.append((backend, path, options))
        return storage

    monkeypatch.setattr("essl_f22.device.create_storage", fake_create)
    device = Device("127.0.0.1", session=FakeSession({}), storage_backend="memory")

    assert created == []

    device.close()

    assert created == []


def test_injected_storage_wins_and_is_not_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = TrackingStorage()

    def fail_create(*args: object, **kwargs: object) -> StorageBackend:
        raise AssertionError("create_storage must not be called")

    monkeypatch.setattr("essl_f22.device.create_storage", fail_create)
    device = Device(
        "127.0.0.1",
        session=FakeSession({}),
        storage=storage,
        storage_backend="json",
        storage_path="/tmp/unused.json",
        storage_options={"unused": True},
    )

    assert device._get_storage() is storage

    device.close()

    assert storage.closed is False


def test_convenience_storage_is_created_lazily(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    storage = TrackingStorage()
    created: list[tuple[str, Path | str | None, dict[str, Any] | None]] = []
    path = tmp_path / "mirror.json"
    options = {"timeout": 5}

    def fake_create(
        backend: str = "sqlite",
        *,
        path: Path | str | None = None,
        options: dict[str, Any] | None = None,
    ) -> StorageBackend:
        created.append((backend, path, options))
        return storage

    monkeypatch.setattr("essl_f22.device.create_storage", fake_create)
    device = Device(
        "127.0.0.1",
        session=FakeSession({}),
        storage_backend="json",
        storage_path=path,
        storage_options=options,
    )

    assert created == []
    assert device._get_storage() is storage
    assert created == [("json", path, options)]
    assert device._get_storage() is storage
    assert len(created) == 1

    device.close()

    assert storage.closed is True


def test_block_methods_delegate_to_block_manager(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = TrackingStorage()
    block_result = BlockResult(1, "a", False, 4, UserTimeZone(1, False))
    unblock_result = UnblockResult(1, "a", UserTimeZone(1, False), True)
    instances: list[Any] = []

    class FakeBlockManager:
        def __init__(self, device: Device, state: StorageBackend) -> None:
            self.device = device
            self.state = state
            self.block_uids: list[int] = []
            self.unblock_uids: list[int] = []
            self.blocked_checks: list[int] = []
            instances.append(self)

        def block_user(self, uid: int) -> BlockResult:
            self.block_uids.append(uid)
            return block_result

        def unblock_user(self, uid: int) -> UnblockResult:
            self.unblock_uids.append(uid)
            return unblock_result

        def is_user_blocked(self, uid: int) -> bool:
            self.blocked_checks.append(uid)
            return True

        def get_blocked_users(self) -> list[int]:
            return [1]

    monkeypatch.setattr("essl_f22.device.BlockManager", FakeBlockManager)
    device = Device("127.0.0.1", session=FakeSession({}), storage=storage)

    assert device.block_user(1) == block_result
    assert device.unblock_user(1) == unblock_result
    assert device.is_user_blocked(1) is True
    assert device.get_blocked_users() == [1]

    assert len(instances) == 4
    assert all(instance.device is device for instance in instances)
    assert all(instance.state is storage for instance in instances)
    assert instances[0].block_uids == [1]
    assert instances[1].unblock_uids == [1]
    assert instances[2].blocked_checks == [1]


def test_mirror_and_sync_delegate_to_mirror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = TrackingStorage()
    sync_result = SyncResult(
        device_serial="JJA1242200334",
        mode="full",
        synced_at=datetime(2026, 10, 24, 12, 0, 0),
        users=1,
        groups=1,
        timezones=1,
        fingerprints=0,
        attendance=0,
        new_attendance=0,
        attendance_replaced=True,
    )
    instances: list[Any] = []

    class FakeMirror:
        def __init__(self, backend: StorageBackend, device_serial: str) -> None:
            self.storage = backend
            self.device_serial = device_serial
            self.sync_calls: list[tuple[Device, str]] = []
            instances.append(self)

        def sync(self, device: Device, mode: str) -> SyncResult:
            self.sync_calls.append((device, mode))
            return sync_result

    monkeypatch.setattr("essl_f22.device.Mirror", FakeMirror)
    device = Device("127.0.0.1", session=_serial_session(), storage=storage)

    returned = device.mirror()
    first = instances[0]
    assert first.storage is storage
    assert first.device_serial == "JJA1242200334"
    assert returned is first

    result = device.sync("full")
    second = instances[1]
    assert second.storage is storage
    assert second.device_serial == "JJA1242200334"
    assert second.sync_calls == [(device, "full")]
    assert result is sync_result
