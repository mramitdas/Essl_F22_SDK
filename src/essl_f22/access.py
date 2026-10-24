"""Non-destructive user blocking through access timezones."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from essl_f22.errors import (
    CommandError,
    DeviceVerificationError,
    NoFreeTimeZoneSlotError,
)
from essl_f22.models import (
    DayInterval,
    GroupInfo,
    TimeZone,
    User,
    UserTimeZone,
)
from essl_f22.storage import BlockStateStore


class AccessDevice(Protocol):
    """Device reads and writes required for access blocking."""

    def get_serial_number(self) -> str: ...

    def get_user(self, uid: int) -> User: ...

    def list_users(self) -> list[User]: ...

    def list_groups(self) -> list[GroupInfo]: ...

    def list_timezones(self) -> dict[int, TimeZone]: ...

    def get_timezone(self, slot: int) -> TimeZone: ...

    def get_user_timezone(self, uid: int) -> UserTimeZone: ...

    def set_timezone(self, timezone: TimeZone) -> None: ...

    def set_user_timezone(self, uid: int, timezone: UserTimeZone) -> None: ...


@dataclass(frozen=True, slots=True)
class BlockResult:
    uid: int
    user_id: str
    already_blocked: bool
    block_timezone_slot: int
    original: UserTimeZone


@dataclass(frozen=True, slots=True)
class UnblockResult:
    uid: int
    user_id: str
    restored: UserTimeZone
    state_found: bool


def _deny_all(slot: int) -> TimeZone:
    return TimeZone(slot, (DayInterval(0, 0, 0, 0),) * 7)


def _is_blocked(timezone: UserTimeZone, slot: int) -> bool:
    return (
        timezone.use_personal
        and timezone.tz1 == slot
        and timezone.tz2 == 0
        and timezone.tz3 == 0
    )


class BlockManager:
    """Blocks and unblocks users without modifying user or fingerprint records."""

    def __init__(self, device: AccessDevice, state: BlockStateStore) -> None:
        self._device = device
        self._state = state

    def block_user(self, uid: int) -> BlockResult:
        serial = self._device.get_serial_number()
        user = self._device.get_user(uid)
        original = self._device.get_user_timezone(uid)
        slot = self._ensure_block_slot(serial)

        if _is_blocked(original, slot):
            saved = self._state.get_original_user_timezone(serial, uid)
            return BlockResult(
                uid=uid,
                user_id=user.user_id,
                already_blocked=True,
                block_timezone_slot=slot,
                original=saved or original,
            )

        self._state.save_original_user_timezone(serial, uid, original)
        blocked = UserTimeZone(uid=uid, use_personal=True, tz1=slot)
        self._device.set_user_timezone(uid, blocked)
        actual = self._device.get_user_timezone(uid)
        if actual != blocked:
            try:
                self._device.set_user_timezone(uid, original)
            except Exception as exc:
                raise DeviceVerificationError(
                    f"user {uid} block could not be verified and the original "
                    "timezone could not be restored"
                ) from exc
            self._state.delete_original_user_timezone(serial, uid)
            raise DeviceVerificationError(
                f"user {uid} block could not be verified; original timezone restored"
            )

        return BlockResult(
            uid=uid,
            user_id=user.user_id,
            already_blocked=False,
            block_timezone_slot=slot,
            original=original,
        )

    def unblock_user(self, uid: int) -> UnblockResult:
        serial = self._device.get_serial_number()
        user = self._device.get_user(uid)
        original = self._state.get_original_user_timezone(serial, uid)
        target = (
            original.canonical()
            if original is not None
            else UserTimeZone(uid=uid, use_personal=False)
        )

        self._device.set_user_timezone(uid, target)
        actual = self._device.get_user_timezone(uid)
        if actual != target:
            raise DeviceVerificationError(f"user {uid} unblock could not be verified")

        if original is not None:
            self._state.delete_original_user_timezone(serial, uid)
        return UnblockResult(
            uid=uid,
            user_id=user.user_id,
            restored=target,
            state_found=original is not None,
        )

    def is_user_blocked(self, uid: int) -> bool:
        assignment = self._device.get_user_timezone(uid)
        slot = self._state.get_block_timezone(self._device.get_serial_number())
        if slot is None:
            return False
        return _is_blocked(assignment, slot.slot)

    def get_blocked_users(self) -> list[int]:
        return self._state.list_blocked_uids(self._device.get_serial_number())

    def _ensure_block_slot(self, serial: str) -> int:
        saved = self._state.get_block_timezone(serial)
        if saved is not None:
            try:
                timezone = self._device.get_timezone(saved.slot)
            except CommandError as exc:
                if exc.code != 0x1381:
                    raise
            else:
                if timezone.is_deny_all():
                    return saved.slot

        slot = self._find_block_slot()
        self._device.set_timezone(_deny_all(slot))
        self._state.save_block_timezone(serial, slot)
        return slot

    def _find_block_slot(self) -> int:
        users = self._device.list_users()
        groups = self._device.list_groups()
        timezones = self._device.list_timezones()

        referenced: set[int] = set()
        for group in groups:
            referenced.update(
                slot for slot in (group.tz1, group.tz2, group.tz3) if slot
            )
        for user in users:
            if user.timezone_flag:
                referenced.update(
                    slot for slot in (user.tz1, user.tz2, user.tz3) if slot
                )

        eligible = [
            timezone
            for timezone in timezones.values()
            if timezone.slot not in referenced and timezone.is_default_allow_all()
        ]
        if not eligible:
            raise NoFreeTimeZoneSlotError(
                "no free default-allow-all timezone slot is available"
            )
        return max(timezone.slot for timezone in eligible)
