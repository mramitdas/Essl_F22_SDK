from dataclasses import replace

import pytest

from essl_f22.access import BlockManager
from essl_f22.errors import (
    CommandError,
    DeviceVerificationError,
    NoFreeTimeZoneSlotError,
    UserNotFoundError,
)
from essl_f22.models import (
    DayInterval,
    GroupInfo,
    TimeZone,
    User,
    UserTimeZone,
)
from essl_f22.storage import (
    BlockTimeZoneState,
    MemoryStorage,
    StorageBackend,
)

DEVICE = "JJA1242200334"


def _allow_all(slot: int) -> TimeZone:
    return TimeZone(slot, (DayInterval(0, 0, 23, 59),) * 7)


def _deny_all(slot: int) -> TimeZone:
    return TimeZone(slot, (DayInterval(0, 0, 0, 0),) * 7)


def _custom(slot: int) -> TimeZone:
    return TimeZone(slot, (DayInterval(1, 0, 2, 0),) * 7)


class FakeAccessDevice:
    def __init__(self) -> None:
        self.serial = DEVICE
        self.users = {
            1: User(
                uid=1,
                user_id="a",
                name="Alpha",
                privilege=3,
                group_id=1,
                timezone_flag=0,
            ),
            2: User(
                uid=2,
                user_id="b",
                name="Beta",
                group_id=1,
                timezone_flag=1,
                tz1=2,
            ),
        }
        self.groups = [GroupInfo(1, 1, 0, 0, 0, False)]
        self.timezones = _default_timezones()
        self.user_timezones = {
            1: UserTimeZone(1, use_personal=False),
            2: UserTimeZone(2, use_personal=True, tz1=2),
        }
        self.timezone_writes: list[TimeZone] = []
        self.user_timezone_writes: list[tuple[int, UserTimeZone]] = []
        self.corrupt_user_timezone_read: UserTimeZone | None = None
        self.corrupt_user_timezone_reads = 0
        self.user_timezone_write_count = 0
        self.fail_user_timezone_write_on_call: int | None = None
        self.timezone_error_slot: int | None = None

    def get_serial_number(self) -> str:
        return self.serial

    def get_user(self, uid: int) -> User:
        try:
            return self.users[uid]
        except KeyError:
            raise UserNotFoundError(f"user uid {uid} was not found") from None

    def list_users(self) -> list[User]:
        return list(self.users.values())

    def list_groups(self) -> list[GroupInfo]:
        return list(self.groups)

    def list_timezones(self) -> dict[int, TimeZone]:
        return dict(self.timezones)

    def get_timezone(self, slot: int) -> TimeZone:
        if self.timezone_error_slot == slot:
            raise CommandError(0x1234)
        try:
            return self.timezones[slot]
        except KeyError:
            raise CommandError(0x1381) from None

    def get_user_timezone(self, uid: int) -> UserTimeZone:
        if uid not in self.user_timezones:
            raise UserNotFoundError(f"user uid {uid} was not found")
        if (
            self.corrupt_user_timezone_reads > 0
            and self.corrupt_user_timezone_read is not None
        ):
            self.corrupt_user_timezone_reads -= 1
            return self.corrupt_user_timezone_read
        return self.user_timezones[uid]

    def set_timezone(self, timezone: TimeZone) -> None:
        self.timezone_writes.append(timezone)
        self.timezones[timezone.slot] = timezone

    def set_user_timezone(self, uid: int, timezone: UserTimeZone) -> None:
        self.user_timezone_write_count += 1
        if self.fail_user_timezone_write_on_call == self.user_timezone_write_count:
            raise CommandError(0x1381)
        self.user_timezone_writes.append((uid, timezone))
        self.user_timezones[uid] = timezone.canonical()


def _default_timezones() -> dict[int, TimeZone]:
    timezones = {slot: _allow_all(slot) for slot in range(1, 6)}
    timezones[5] = _custom(5)
    return timezones


def _manager(
    device: FakeAccessDevice | None = None,
    storage: StorageBackend | None = None,
) -> tuple[BlockManager, FakeAccessDevice, StorageBackend]:
    fake = device if device is not None else FakeAccessDevice()
    store = storage if storage is not None else MemoryStorage()
    return BlockManager(fake, store), fake, store


def test_block_chooses_highest_free_default_allow_all_slot() -> None:
    manager, device, store = _manager()

    result = manager.block_user(1)

    assert result.uid == 1
    assert result.user_id == "a"
    assert result.already_blocked is False
    assert result.block_timezone_slot == 4
    assert result.original == UserTimeZone(1, use_personal=False)
    assert device.timezones[4].is_deny_all()
    assert device.timezone_writes == [_deny_all(4)]
    assert device.user_timezones[1] == UserTimeZone(1, True, 4, 0, 0)
    assert store.get_block_timezone(DEVICE) == BlockTimeZoneState(4)
    assert store.get_original_user_timezone(DEVICE, 1) == UserTimeZone(
        1, use_personal=False
    )
    assert device.users[1] == User(
        uid=1,
        user_id="a",
        name="Alpha",
        privilege=3,
        group_id=1,
        timezone_flag=0,
    )


def test_block_reuses_existing_deny_all_slot() -> None:
    manager, device, store = _manager()
    store.save_block_timezone(DEVICE, 7)
    device.timezones[7] = _deny_all(7)

    result = manager.block_user(1)

    assert result.block_timezone_slot == 7
    assert device.timezone_writes == []
    assert device.user_timezones[1] == UserTimeZone(1, True, 7, 0, 0)
    assert store.get_block_timezone(DEVICE) == BlockTimeZoneState(7)


def test_block_replaces_stale_block_slot() -> None:
    manager, device, store = _manager()
    store.save_block_timezone(DEVICE, 7)
    device.timezones[7] = _custom(7)

    result = manager.block_user(1)

    assert result.block_timezone_slot == 4
    assert device.timezone_writes == [_deny_all(4)]
    assert store.get_block_timezone(DEVICE) == BlockTimeZoneState(4)


def test_block_does_not_reuse_referenced_slots() -> None:
    manager, device, _ = _manager()
    device.groups = [GroupInfo(1, 1, 3, 0, 0, False)]
    device.users[2] = replace(device.users[2], tz1=2, tz2=4)
    device.user_timezones[2] = UserTimeZone(2, True, 2, 4, 0)
    device.timezones[6] = _allow_all(6)

    result = manager.block_user(1)

    assert result.block_timezone_slot == 6


def test_block_is_idempotent() -> None:
    manager, device, store = _manager()
    first = manager.block_user(1)
    device.user_timezone_writes.clear()

    second = manager.block_user(1)

    assert second.already_blocked is True
    assert second.block_timezone_slot == first.block_timezone_slot
    assert second.original == first.original
    assert device.user_timezone_writes == []
    assert store.get_original_user_timezone(DEVICE, 1) == first.original


def test_block_raises_when_no_free_slot_exists() -> None:
    manager, device, store = _manager()
    device.groups = [GroupInfo(1, 1, 0, 0, 0, False)]
    device.users[2] = replace(device.users[2], tz1=2)
    device.timezones = {1: _allow_all(1), 2: _allow_all(2), 3: _custom(3)}

    with pytest.raises(NoFreeTimeZoneSlotError):
        manager.block_user(1)

    assert device.user_timezone_writes == []
    assert store.get_original_user_timezone(DEVICE, 1) is None


def test_block_verification_failure_restores_original_and_clears_state() -> None:
    manager, device, store = _manager()
    original = device.user_timezones[1]
    device.corrupt_user_timezone_read = original
    device.corrupt_user_timezone_reads = 2

    with pytest.raises(DeviceVerificationError):
        manager.block_user(1)

    assert device.user_timezones[1] == original
    assert device.user_timezone_writes == [
        (1, UserTimeZone(1, True, 4, 0, 0)),
        (1, original),
    ]
    assert store.get_original_user_timezone(DEVICE, 1) is None


def test_block_does_not_hide_unexpected_timezone_errors() -> None:
    manager, device, store = _manager()
    store.save_block_timezone(DEVICE, 7)
    device.timezone_error_slot = 7

    with pytest.raises(CommandError):
        manager.block_user(1)

    assert store.get_original_user_timezone(DEVICE, 1) is None


def test_block_reports_when_original_restore_also_fails() -> None:
    manager, device, store = _manager()
    original = device.user_timezones[1]
    device.corrupt_user_timezone_read = original
    device.corrupt_user_timezone_reads = 2
    device.fail_user_timezone_write_on_call = 2

    with pytest.raises(DeviceVerificationError, match="could not be restored"):
        manager.block_user(1)

    assert store.get_original_user_timezone(DEVICE, 1) == original


def test_unblock_restores_saved_original() -> None:
    manager, device, store = _manager()
    blocked = manager.block_user(1)

    result = manager.unblock_user(1)

    assert result.uid == 1
    assert result.user_id == "a"
    assert result.restored == blocked.original
    assert result.state_found is True
    assert device.user_timezones[1] == blocked.original
    assert store.get_original_user_timezone(DEVICE, 1) is None
    assert store.get_block_timezone(DEVICE) == BlockTimeZoneState(
        blocked.block_timezone_slot
    )


def test_unblock_falls_back_to_group_timezone_without_state() -> None:
    manager, device, store = _manager()

    result = manager.unblock_user(1)

    assert result.restored == UserTimeZone(1, use_personal=False)
    assert result.state_found is False
    assert device.user_timezones[1] == UserTimeZone(1, use_personal=False)
    assert store.get_original_user_timezone(DEVICE, 1) is None


def test_unblock_is_idempotent() -> None:
    manager, _, _ = _manager()
    manager.block_user(1)
    manager.unblock_user(1)

    result = manager.unblock_user(1)

    assert result.state_found is False
    assert result.restored == UserTimeZone(1, use_personal=False)


def test_unblock_verification_failure_keeps_saved_state() -> None:
    manager, device, store = _manager()
    blocked = manager.block_user(1)
    original = blocked.original
    device.corrupt_user_timezone_read = UserTimeZone(1, True, 4, 0, 0)
    device.corrupt_user_timezone_reads = 1

    with pytest.raises(DeviceVerificationError):
        manager.unblock_user(1)

    assert store.get_original_user_timezone(DEVICE, 1) == original
    assert device.user_timezones[1] == original


def test_is_user_blocked_and_get_blocked_users() -> None:
    manager, _, _ = _manager()

    assert manager.is_user_blocked(1) is False
    assert manager.get_blocked_users() == []

    manager.block_user(1)

    assert manager.is_user_blocked(1) is True
    assert manager.get_blocked_users() == [1]

    manager.unblock_user(1)

    assert manager.is_user_blocked(1) is False
    assert manager.get_blocked_users() == []


def test_missing_user_raises_typed_error() -> None:
    manager, _, _ = _manager()

    with pytest.raises(UserNotFoundError):
        manager.block_user(99)
    with pytest.raises(UserNotFoundError):
        manager.unblock_user(99)
    with pytest.raises(UserNotFoundError):
        manager.is_user_blocked(99)
