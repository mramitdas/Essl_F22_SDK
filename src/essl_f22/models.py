"""Dataclasses and binary codecs for device records."""

from __future__ import annotations

import struct
from dataclasses import dataclass

from essl_f22.errors import ProtocolError

USER_RECORD_SIZE = 72
USER_RECORD_FORMAT = "<HB8s24sIBHHHH24s"


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
