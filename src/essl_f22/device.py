"""High-level device APIs."""

from __future__ import annotations

import struct
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, Self

from essl_f22.access import BlockManager, BlockResult, UnblockResult
from essl_f22.errors import CommandError, ProtocolError, UserNotFoundError
from essl_f22.mirror import Mirror
from essl_f22.models import (
    AttendanceRecord,
    DeviceInfo,
    FingerprintTemplate,
    FreeSizes,
    GroupInfo,
    TimeZone,
    User,
    UserTimeZone,
    parse_attendance_records,
    parse_fingerprint_templates,
    parse_user_records,
)
from essl_f22.protocol import (
    CMD_ACK_OK,
    CMD_ATTLOG_RRQ,
    CMD_DELETE_USER,
    CMD_GET_FREE_SIZES,
    CMD_GET_TIME,
    CMD_GET_VERSION,
    CMD_GRPTZ_RRQ,
    CMD_GRPTZ_WRQ,
    CMD_OPTIONS_RRQ,
    CMD_SET_TIME,
    CMD_TZ_RRQ,
    CMD_TZ_WRQ,
    CMD_USER_WRQ,
    CMD_USERTEMP_RRQ,
    CMD_USERTZ_RRQ,
    CMD_USERTZ_WRQ,
    Response,
    decode_device_time,
    encode_device_time,
)
from essl_f22.session import Session, SessionLike
from essl_f22.storage import (
    StorageBackend,
    SyncMode,
    SyncResult,
    create_storage,
)
from essl_f22.transport import Transport


class Device:
    """A high-level client for an eSSL F22 terminal."""

    def __init__(
        self,
        host: str,
        port: int = 4370,
        *,
        timeout: float = 10.0,
        comm_key: int = 0,
        encoding: str = "utf-8",
        transport: Transport | None = None,
        session: SessionLike | None = None,
        storage: StorageBackend | None = None,
        storage_backend: str = "sqlite",
        storage_path: Path | str | None = None,
        storage_options: Mapping[str, Any] | None = None,
        max_timezone_slots: int = 50,
        max_groups: int = 100,
    ) -> None:
        self._encoding = encoding
        self._max_timezone_slots = max_timezone_slots
        self._max_groups = max_groups
        self._session: SessionLike = (
            session
            if session is not None
            else Session(host, port, timeout, comm_key, transport)
        )
        self._serial_number: str | None = None
        self._storage = storage
        self._storage_backend = storage_backend
        self._storage_path = storage_path
        self._storage_options = storage_options
        self._owns_storage = storage is None

    def connect(self) -> Self:
        self._session.connect()
        return self

    def close(self) -> None:
        self._session.close()
        if self._owns_storage and self._storage is not None:
            self._storage.close()

    def __enter__(self) -> Self:
        return self.connect()

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def get_option(self, name: str) -> str:
        response = self._session.send_command(
            CMD_OPTIONS_RRQ, name.encode(self._encoding) + b"\x00"
        )
        self._require_ack(response, f"option {name}")
        text = response.data.split(b"\x00", 1)[0].decode(
            self._encoding, errors="replace"
        )
        if "=" not in text:
            raise ProtocolError(f"option response for {name} has no value")
        return text.split("=", 1)[1]

    def get_device_info(self) -> DeviceInfo:
        platform = self.get_option("~Platform")
        device_name = self.get_option("~DeviceName")
        serial_number = self.get_serial_number()

        response = self._session.send_command(CMD_GET_VERSION)
        self._require_ack(response, "version")
        firmware_version = response.data.split(b"\x00", 1)[0].decode(
            self._encoding, errors="replace"
        )
        return DeviceInfo(
            platform=platform,
            device_name=device_name,
            serial_number=serial_number,
            firmware_version=firmware_version,
        )

    def get_serial_number(self) -> str:
        if self._serial_number is None:
            self._serial_number = self.get_option("~SerialNumber")
        return self._serial_number

    def list_users(self) -> list[User]:
        blob = self._session.read_buffer(CMD_USERTEMP_RRQ, 5)
        if not blob:
            return []
        return parse_user_records(blob, self._encoding)

    def get_user(self, uid: int) -> User:
        for user in self.list_users():
            if user.uid == uid:
                return user
        raise UserNotFoundError(f"user uid {uid} was not found")

    def get_user_by_user_id(self, user_id: str) -> User:
        for user in self.list_users():
            if user.user_id == user_id:
                return user
        raise UserNotFoundError(f"user id {user_id!r} was not found")

    def set_user(self, user: User) -> None:
        if not 0 <= user.uid <= 0xFFFF:
            raise ValueError(
                f"user uid must fit in an unsigned 16-bit field, got {user.uid}"
            )
        response = self._session.send_command(
            CMD_USER_WRQ, user.to_record(self._encoding)
        )
        self._require_ack(response, f"set user {user.uid}")
        self.refresh_data()

    def delete_user(self, uid: int) -> None:
        if not 0 <= uid <= 0xFFFF:
            raise ValueError(
                f"user uid must fit in an unsigned 16-bit field, got {uid}"
            )
        response = self._session.send_command(CMD_DELETE_USER, struct.pack("<H", uid))
        self._require_ack(response, f"delete user {uid}")
        self.refresh_data()

    def list_fingerprints(self) -> list[FingerprintTemplate]:
        blob = self._session.read_buffer(CMD_USERTEMP_RRQ, 2)
        if not blob:
            return []
        return parse_fingerprint_templates(blob)

    def get_user_fingerprints(self, uid: int) -> list[FingerprintTemplate]:
        return [
            template for template in self.list_fingerprints() if template.uid == uid
        ]

    def list_attendance(self) -> list[AttendanceRecord]:
        sizes = self.get_free_sizes()
        if sizes.attendance == 0:
            return []
        blob = self._session.read_buffer(CMD_ATTLOG_RRQ)
        if not blob:
            return []
        return parse_attendance_records(blob, sizes.attendance)

    def get_timezone(self, slot: int) -> TimeZone:
        response = self._session.send_command(CMD_TZ_RRQ, struct.pack("<I", slot))
        self._require_ack(response, f"timezone {slot}")
        return TimeZone.from_response(response.data)

    def list_timezones(self) -> dict[int, TimeZone]:
        timezones: dict[int, TimeZone] = {}
        for slot in range(1, self._max_timezone_slots + 1):
            try:
                timezone = self.get_timezone(slot)
            except CommandError as exc:
                if exc.code == 0x1381:
                    continue
                raise
            timezones[timezone.slot] = timezone
        return timezones

    def set_timezone(self, timezone: TimeZone) -> None:
        response = self._session.send_command(CMD_TZ_WRQ, timezone.to_request())
        self._require_ack(response, "set timezone")
        self.refresh_data()

    def get_group(self, group_id: int) -> GroupInfo:
        request = bytes([group_id]) + b"\x00" * 7
        response = self._session.send_command(CMD_GRPTZ_RRQ, request)
        self._require_ack(response, f"group {group_id}")
        return GroupInfo.from_response(response.data)

    def list_groups(self) -> list[GroupInfo]:
        groups: dict[int, GroupInfo] = {}
        for group_id in range(1, self._max_groups + 1):
            try:
                group = self.get_group(group_id)
            except CommandError as exc:
                if exc.code == 0x1381:
                    continue
                raise
            groups[group.group_id] = group
        return list(groups.values())

    def set_group(self, group: GroupInfo) -> None:
        response = self._session.send_command(CMD_GRPTZ_WRQ, group.to_request())
        self._require_ack(response, "set group")
        self.refresh_data()

    def get_user_timezone(self, uid: int) -> UserTimeZone:
        response = self._session.send_command(CMD_USERTZ_RRQ, struct.pack("<I", uid))
        self._require_ack(response, f"user timezone {uid}")
        return UserTimeZone.from_response(uid, response.data)

    def set_user_timezone(self, uid: int, timezone: UserTimeZone) -> None:
        response = self._session.send_command(
            CMD_USERTZ_WRQ, timezone.canonical().to_request()
        )
        self._require_ack(response, f"set user timezone {uid}")
        self.refresh_data()

    def get_free_sizes(self) -> FreeSizes:
        response = self._session.send_command(CMD_GET_FREE_SIZES)
        self._require_ack(response, "free sizes")
        if len(response.data) < 80:
            length = len(response.data)
            raise ProtocolError(
                f"free-size response must be at least 80 bytes, got {length}"
            )
        fields = struct.unpack_from("<20i", response.data)
        return FreeSizes(
            users=fields[4],
            fingerprints=fields[6],
            attendance=fields[8],
            users_capacity=fields[15],
            fingerprints_capacity=fields[14],
            attendance_capacity=fields[16],
        )

    def get_time(self) -> datetime:
        response = self._session.send_command(CMD_GET_TIME)
        self._require_ack(response, "time")
        if len(response.data) < 4:
            raise ProtocolError(
                f"time response must be at least 4 bytes, got {len(response.data)}"
            )
        return decode_device_time(struct.unpack_from("<I", response.data)[0])

    def set_time(self, value: datetime) -> None:
        response = self._session.send_command(
            CMD_SET_TIME, struct.pack("<I", encode_device_time(value))
        )
        self._require_ack(response, "set time")

    def refresh_data(self) -> None:
        self._session.refresh_data()

    def block_user(self, uid: int) -> BlockResult:
        return BlockManager(self, self._get_storage()).block_user(uid)

    def unblock_user(self, uid: int) -> UnblockResult:
        return BlockManager(self, self._get_storage()).unblock_user(uid)

    def is_user_blocked(self, uid: int) -> bool:
        return BlockManager(self, self._get_storage()).is_user_blocked(uid)

    def get_blocked_users(self) -> list[int]:
        return BlockManager(self, self._get_storage()).get_blocked_users()

    def mirror(self) -> Mirror:
        return Mirror(self._get_storage(), self.get_serial_number())

    def sync(self, mode: SyncMode = "incremental") -> SyncResult:
        return self.mirror().sync(self, mode)

    def _get_storage(self) -> StorageBackend:
        if self._storage is None:
            self._storage = create_storage(
                self._storage_backend,
                path=self._storage_path,
                options=self._storage_options,
            )
        return self._storage

    def _require_ack(self, response: Response, action: str) -> None:
        if response.command != CMD_ACK_OK:
            raise CommandError(
                response.command,
                f"device rejected {action} with 0x{response.command:04X}",
            )
