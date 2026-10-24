"""ZKTeco protocol primitives for the eSSL F22 SDK."""

from __future__ import annotations

import struct
from dataclasses import dataclass

MACHINE_PREPARE_DATA_1 = 0x5050
MACHINE_PREPARE_DATA_2 = 0x7D82
MAX_CHUNK = 0xFFC0

CMD_USER_WRQ = 8
CMD_USERTEMP_RRQ = 9
CMD_OPTIONS_RRQ = 11
CMD_ATTLOG_RRQ = 13
CMD_DELETE_USER = 18
CMD_USERGRP_RRQ = 21
CMD_USERGRP_WRQ = 22
CMD_USERTZ_RRQ = 23
CMD_USERTZ_WRQ = 24
CMD_GRPTZ_RRQ = 25
CMD_GRPTZ_WRQ = 26
CMD_TZ_RRQ = 27
CMD_TZ_WRQ = 28
CMD_GET_FREE_SIZES = 50
CMD_VERIFY_RRQ = 80
CMD_GET_TIME = 201
CMD_SET_TIME = 202
CMD_CONNECT = 1000
CMD_EXIT = 1001
CMD_ENABLEDEVICE = 1002
CMD_DISABLEDEVICE = 1003
CMD_REFRESHDATA = 1013
CMD_GET_VERSION = 1100
CMD_AUTH = 1102
CMD_PREPARE_DATA = 1500
CMD_DATA = 1501
CMD_FREE_DATA = 1502
CMD_DATA_WRRQ = 1503
CMD_DATA_RDY = 1504
CMD_ACK_OK = 2000
CMD_ACK_ERROR = 2001
CMD_ACK_UNAUTH = 2005


@dataclass(frozen=True, slots=True)
class Response:
    """A decoded device command response."""

    command: int
    data: bytes
    session_id: int
    reply_id: int


def checksum(payload: bytes) -> int:
    """Return the ZKTeco-compatible one's-complement checksum."""

    total = 0
    for index in range(0, len(payload) - 1, 2):
        total += payload[index] | (payload[index + 1] << 8)
        if total > 0xFFFF:
            total -= 0xFFFF

    if len(payload) % 2:
        total += payload[-1]

    while total > 0xFFFF:
        total -= 0xFFFF

    total = ~total
    while total < 0:
        total += 0xFFFF

    return total


def make_comm_key(key: int, session_id: int, ticks: int = 50) -> bytes:
    """Reproduce the device firmware's communication-key encoding."""

    scrambled = 0
    for bit in range(32):
        if key & (1 << bit):
            scrambled = (scrambled << 1) | 1
        else:
            scrambled <<= 1
    scrambled += session_id

    scrambled_bytes = struct.unpack("BBBB", struct.pack("I", scrambled))
    scrambled_bytes = (
        scrambled_bytes[0] ^ ord("Z"),
        scrambled_bytes[1] ^ ord("K"),
        scrambled_bytes[2] ^ ord("S"),
        scrambled_bytes[3] ^ ord("O"),
    )
    words = struct.unpack("HH", struct.pack("BBBB", *scrambled_bytes))
    swapped = struct.unpack("BBBB", struct.pack("HH", words[1], words[0]))

    tick_byte = 0xFF & ticks
    final = (
        swapped[0] ^ tick_byte,
        swapped[1] ^ tick_byte,
        tick_byte,
        swapped[3] ^ tick_byte,
    )
    return struct.pack("BBBB", *final)
