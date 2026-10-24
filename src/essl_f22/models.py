"""Dataclasses and binary codecs for device records."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from datetime import datetime

from essl_f22.errors import ProtocolError

USER_RECORD_SIZE = 72
USER_RECORD_FORMAT = "<HB8s24sIBHHHH24s"
ATTENDANCE_RECORD_SIZE = 40
ATTENDANCE_PREFIX = b"\xff255\x00\x00\x00\x00\x00"
FINGERPRINT_HEADER_SIZE = 6


def _decode_fixed(data: bytes, encoding: str) -> str:
    return data.split(b"\x00", 1)[0].decode(encoding, errors="replace").rstrip("\x00")


def _encode_fixed(value: str, field_size: int, encoding: str) -> bytes:
    encoded = value.encode(encoding, errors="strict")
    if len(encoded) > field_size - 1:
        raise ValueError(
            f"value of {len(encoded)} bytes does not fit in {field_size} bytes"
        )
    return encoded.ljust(field_size, b"\x00")


@dataclass(slots=True)
class User:
    uid: int
    user_id: str
    name: str = ""
    privilege: int = 0
    password: str = ""
    card: int = 0
    group_id: int = 1
    timezone_flag: int = 0
    tz1: int = 0
    tz2: int = 0
    tz3: int = 0

    @classmethod
    def from_record(cls, data: bytes, encoding: str = "utf-8") -> User:
        if len(data) != USER_RECORD_SIZE:
            raise ProtocolError(
                f"user record must be {USER_RECORD_SIZE} bytes, got {len(data)}"
            )
        (
            uid,
            privilege,
            password,
            name,
            card,
            group_id,
            timezone_flag,
            tz1,
            tz2,
            tz3,
            user_id,
        ) = struct.unpack(USER_RECORD_FORMAT, data)
        return cls(
            uid=uid,
            user_id=_decode_fixed(user_id, encoding),
            name=_decode_fixed(name, encoding),
            privilege=privilege,
            password=_decode_fixed(password, encoding),
            card=card,
            group_id=group_id,
            timezone_flag=timezone_flag,
            tz1=tz1,
            tz2=tz2,
            tz3=tz3,
        )

    def to_record(self, encoding: str = "utf-8") -> bytes:
        return struct.pack(
            USER_RECORD_FORMAT,
            self.uid,
            self.privilege,
            _encode_fixed(self.password, 8, encoding),
            _encode_fixed(self.name, 24, encoding),
            self.card,
            self.group_id,
            self.timezone_flag,
            self.tz1,
            self.tz2,
            self.tz3,
            _encode_fixed(self.user_id, 24, encoding),
        )


def parse_user_records(blob: bytes, encoding: str = "utf-8") -> list[User]:
    if len(blob) < 4:
        raise ProtocolError("user data is missing its size prefix")
    total_size = int.from_bytes(blob[:4], "little")
    payload = blob[4:]
    if total_size == 0:
        return []
    if len(payload) % USER_RECORD_SIZE != 0:
        raise ProtocolError("user data length is not a multiple of 72")
    return [
        User.from_record(payload[offset : offset + USER_RECORD_SIZE], encoding)
        for offset in range(0, len(payload), USER_RECORD_SIZE)
    ]


@dataclass(frozen=True, slots=True)
class AttendanceRecord:
    uid: int
    user_id: str
    timestamp: datetime
    status: int
    punch: int


def decode_attendance_timestamp(raw: bytes) -> datetime:
    value = int.from_bytes(raw, "little")
    second = value % 60
    value //= 60
    minute = value % 60
    value //= 60
    hour = value % 24
    value //= 24
    day = value % 31 + 1
    value //= 31
    month = value % 12 + 1
    value //= 12
    year = value + 2000
    return datetime(year, month, day, hour, minute, second)


def parse_attendance_records(blob: bytes, record_count: int) -> list[AttendanceRecord]:
    if len(blob) < 4:
        raise ProtocolError("attendance data is missing its size prefix")
    total_size = int.from_bytes(blob[:4], "little")
    if record_count == 0 or total_size == 0:
        return []
    if total_size % record_count != 0:
        raise ProtocolError("attendance total size is not divisible by record count")
    record_size = total_size // record_count
    if record_size != ATTENDANCE_RECORD_SIZE:
        raise ProtocolError(
            f"unsupported attendance record size {record_size}; expected 40"
        )

    payload = blob[4:]
    if payload.startswith(ATTENDANCE_PREFIX):
        payload = payload[len(ATTENDANCE_PREFIX) :]
    if len(payload) != total_size:
        raise ProtocolError("attendance data length does not match its size prefix")

    records: list[AttendanceRecord] = []
    for offset in range(0, total_size, ATTENDANCE_RECORD_SIZE):
        uid, user_id, status, raw_timestamp, punch, _reserved = struct.unpack_from(
            "<H24sB4sB8s", payload, offset
        )
        records.append(
            AttendanceRecord(
                uid=uid,
                user_id=_decode_fixed(user_id, "utf-8"),
                timestamp=decode_attendance_timestamp(raw_timestamp),
                status=status,
                punch=punch,
            )
        )
    return records


@dataclass(frozen=True, slots=True)
class FingerprintTemplate:
    uid: int
    fid: int
    flag: int
    template: bytes

    @property
    def size(self) -> int:
        return len(self.template) + FINGERPRINT_HEADER_SIZE


def parse_fingerprint_templates(blob: bytes) -> list[FingerprintTemplate]:
    if len(blob) < 4:
        raise ProtocolError("fingerprint data is missing its size prefix")
    total_size = int.from_bytes(blob[:4], "little")
    payload = blob[4:]
    if total_size == 0:
        return []
    if len(payload) != total_size:
        raise ProtocolError("fingerprint data length does not match its size prefix")

    templates: list[FingerprintTemplate] = []
    offset = 0
    while offset < total_size:
        if total_size - offset < FINGERPRINT_HEADER_SIZE:
            raise ProtocolError("fingerprint entry is truncated")
        size, uid, fid, flag = struct.unpack_from("<HHBB", payload, offset)
        if size < FINGERPRINT_HEADER_SIZE:
            raise ProtocolError(f"fingerprint entry size {size} is too small")
        end = offset + size
        if end > total_size:
            raise ProtocolError("fingerprint entry is truncated")
        templates.append(
            FingerprintTemplate(
                uid=uid,
                fid=fid,
                flag=flag,
                template=payload[offset + FINGERPRINT_HEADER_SIZE : end],
            )
        )
        offset = end
    return templates


@dataclass(frozen=True, slots=True)
class DayInterval:
    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int

    def allows(self, value: datetime) -> bool:
        if (self.start_hour, self.start_minute) >= (self.end_hour, self.end_minute):
            return False
        current = value.hour * 60 + value.minute
        start = self.start_hour * 60 + self.start_minute
        end = self.end_hour * 60 + self.end_minute
        return start <= current <= end


@dataclass(frozen=True, slots=True)
class TimeZone:
    slot: int
    days: tuple[DayInterval, ...]

    @classmethod
    def from_response(cls, data: bytes) -> TimeZone:
        if len(data) != 32:
            raise ProtocolError(f"timezone response must be 32 bytes, got {len(data)}")
        slot = struct.unpack_from("<H", data, 0)[0]
        days = tuple(
            DayInterval(*struct.unpack_from("<BBBB", data, 2 + index * 4))
            for index in range(7)
        )
        return cls(slot=slot, days=days)

    def to_request(self) -> bytes:
        intervals = b"".join(
            struct.pack(
                "<BBBB",
                day.start_hour,
                day.start_minute,
                day.end_hour,
                day.end_minute,
            )
            for day in self.days
        )
        return struct.pack("<I", self.slot) + intervals

    def is_default_allow_all(self) -> bool:
        return all(
            (day.start_hour, day.start_minute, day.end_hour, day.end_minute)
            == (0, 0, 23, 59)
            for day in self.days
        )

    def is_deny_all(self) -> bool:
        return all(
            (day.start_hour, day.start_minute) >= (day.end_hour, day.end_minute)
            for day in self.days
        )


@dataclass(frozen=True, slots=True)
class GroupInfo:
    group_id: int
    tz1: int
    tz2: int
    tz3: int
    verify_style: int
    holiday_enabled: bool

    @classmethod
    def from_response(cls, data: bytes) -> GroupInfo:
        if len(data) != 8:
            raise ProtocolError(f"group response must be 8 bytes, got {len(data)}")
        group_id, tz1, tz2, tz3, flags = struct.unpack("<BHHHB", data)
        return cls(
            group_id=group_id,
            tz1=tz1,
            tz2=tz2,
            tz3=tz3,
            verify_style=flags & 0x7F,
            holiday_enabled=bool(flags & 0x80),
        )

    def to_request(self) -> bytes:
        flags = self.verify_style & 0x7F
        if self.holiday_enabled:
            flags |= 0x80
        return struct.pack("<BHHHB", self.group_id, self.tz1, self.tz2, self.tz3, flags)


@dataclass(frozen=True, slots=True)
class UserTimeZone:
    uid: int
    use_personal: bool
    tz1: int = 0
    tz2: int = 0
    tz3: int = 0

    @classmethod
    def from_response(cls, uid: int, data: bytes) -> UserTimeZone:
        if len(data) != 8:
            raise ProtocolError(
                f"user-timezone response must be 8 bytes, got {len(data)}"
            )
        flag, tz1, tz2, tz3 = struct.unpack("<HHHH", data)
        return cls(
            uid=uid,
            use_personal=flag == 1,
            tz1=tz1,
            tz2=tz2,
            tz3=tz3,
        )

    def to_request(self) -> bytes:
        return struct.pack(
            "<IIIII",
            self.uid,
            1 if self.use_personal else 0,
            self.tz1,
            self.tz2,
            self.tz3,
        )

    def canonical(self) -> UserTimeZone:
        if self.use_personal:
            return self
        return UserTimeZone(uid=self.uid, use_personal=False)


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    platform: str
    device_name: str
    serial_number: str
    firmware_version: str


@dataclass(frozen=True, slots=True)
class FreeSizes:
    users: int
    fingerprints: int
    attendance: int
    users_capacity: int
    fingerprints_capacity: int
    attendance_capacity: int
