"""High-level device APIs."""

from __future__ import annotations

import struct
from datetime import datetime
from typing import Self

from essl_f22.errors import CommandError, ProtocolError, UserNotFoundError
from essl_f22.models import (
    AttendanceRecord,
    DeviceInfo,
    FingerprintTemplate,
    FreeSizes,
    User,
    parse_attendance_records,
    parse_fingerprint_templates,
    parse_user_records,
)
from essl_f22.protocol import (
    CMD_ACK_OK,
    CMD_ATTLOG_RRQ,
    CMD_GET_FREE_SIZES,
    CMD_GET_TIME,
    CMD_GET_VERSION,
    CMD_OPTIONS_RRQ,
    CMD_SET_TIME,
    CMD_USERTEMP_RRQ,
    Response,
    decode_device_time,
    encode_device_time,
)
from essl_f22.session import Session, SessionLike
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
    ) -> None:
        self._encoding = encoding
        self._session: SessionLike = (
            session
            if session is not None
            else Session(host, port, timeout, comm_key, transport)
        )
        self._serial_number: str | None = None

    def connect(self) -> Self:
        self._session.connect()
        return self

    def close(self) -> None:
        self._session.close()

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

    def _require_ack(self, response: Response, action: str) -> None:
        if response.command != CMD_ACK_OK:
            raise CommandError(
                response.command,
                f"device rejected {action} with 0x{response.command:04X}",
            )
