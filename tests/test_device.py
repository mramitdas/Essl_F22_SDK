import struct
from datetime import datetime

import pytest

from essl_f22.device import Device
from essl_f22.errors import ProtocolError, UserNotFoundError
from essl_f22.protocol import (
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
from tests.fakes import FakeSession
from tests.test_models import RECORD_HEX


def test_get_option_parses_name_value() -> None:
    session = FakeSession({11: Response(2000, b"~DeviceName=x 2008\x00", 0, 0)})
    device = Device("127.0.0.1", session=session)
    assert device.get_option("~DeviceName") == "x 2008"
    assert session.calls == [(CMD_OPTIONS_RRQ, b"~DeviceName\x00")]


def test_get_option_rejects_missing_equals() -> None:
    session = FakeSession({11: Response(2000, b"~DeviceName\x00", 0, 0)})
    device = Device("127.0.0.1", session=session)
    with pytest.raises(ProtocolError):
        device.get_option("~DeviceName")


def test_get_device_info_combines_options_and_version() -> None:
    session = FakeSession(
        {
            11: Response(2000, b"~Platform=ZLM60_TFT\x00", 0, 0),
            1100: Response(2000, b"Ver 6.60 Apr 13 2022\x00", 0, 0),
        }
    )
    device = Device("127.0.0.1", session=session)
    info = device.get_device_info()
    assert info.platform == "ZLM60_TFT"
    assert info.firmware_version == "Ver 6.60 Apr 13 2022"
    assert (CMD_GET_VERSION, b"") in session.calls


def test_get_serial_number_is_cached() -> None:
    session = FakeSession(
        {11: Response(2000, b"~SerialNumber=JJA1242200334\x00", 0, 0)}
    )
    device = Device("127.0.0.1", session=session)
    assert device.get_serial_number() == "JJA1242200334"
    assert device.get_serial_number() == "JJA1242200334"
    assert len([call for call in session.calls if call[0] == CMD_OPTIONS_RRQ]) == 1


def test_get_free_sizes_maps_device_fields() -> None:
    fields = [0] * 20
    fields[4] = 295
    fields[6] = 266
    fields[8] = 11895
    fields[14] = 3000
    fields[15] = 4000
    fields[16] = 100000
    payload = struct.pack("<20i", *fields)
    session = FakeSession({50: Response(2000, payload, 0, 0)})
    device = Device("127.0.0.1", session=session)
    sizes = device.get_free_sizes()
    assert sizes.users == 295
    assert sizes.fingerprints == 266
    assert sizes.attendance == 11895
    assert sizes.users_capacity == 4000
    assert sizes.fingerprints_capacity == 3000
    assert sizes.attendance_capacity == 100000
    assert session.calls == [(CMD_GET_FREE_SIZES, b"")]


def test_get_time_decodes_device_timestamp() -> None:
    value = datetime(2026, 10, 24, 15, 25, 50)
    payload = struct.pack("<I", encode_device_time(value))
    session = FakeSession({201: Response(2000, payload, 0, 0)})
    device = Device("127.0.0.1", session=session)
    assert device.get_time() == value
    assert session.calls == [(CMD_GET_TIME, b"")]


def test_set_time_encodes_device_timestamp() -> None:
    value = datetime(2026, 10, 24, 15, 25, 50)
    session = FakeSession({202: Response(2000, b"", 0, 0)})
    device = Device("127.0.0.1", session=session)
    device.set_time(value)
    expected = struct.pack("<I", encode_device_time(value))
    assert session.calls == [(CMD_SET_TIME, expected)]


def test_refresh_data_uses_session() -> None:
    session = FakeSession({})
    device = Device("127.0.0.1", session=session)
    device.refresh_data()
    assert session.calls == [(1013, b"")]


def test_device_time_round_trip() -> None:
    value = datetime(2026, 10, 24, 15, 25, 50)
    assert decode_device_time(encode_device_time(value)) == value


def _user_blob() -> bytes:
    record = bytes.fromhex(RECORD_HEX)
    return (72).to_bytes(4, "little") + record


def _fingerprint_blob() -> bytes:
    template = b"\xab" * 952
    entry = (
        (958).to_bytes(2, "little")
        + (295).to_bytes(2, "little")
        + b"\x09"
        + b"\x01"
        + template
    )
    return (len(entry)).to_bytes(4, "little") + entry


def _attendance_blob() -> bytes:
    timestamp = (26 * 12 * 31 + 9 * 31 + 24 - 1) * 86400 + (15 * 60 + 25) * 60 + 50
    record = (
        (295).to_bytes(2, "little")
        + b"13".ljust(24, b"\x00")
        + b"\x01"
        + timestamp.to_bytes(4, "little")
        + b"\x00"
        + b"\x00" * 8
    )
    return (40).to_bytes(4, "little") + record


def test_list_users_parses_buffer() -> None:
    session = FakeSession({}, buffers={(CMD_USERTEMP_RRQ, 5): _user_blob()})
    device = Device("127.0.0.1", session=session)
    users = device.list_users()
    assert len(users) == 1
    assert users[0].uid == 295
    assert session.calls == [(CMD_USERTEMP_RRQ, b"\x05\x00")]


def test_list_users_returns_empty_for_empty_buffer() -> None:
    session = FakeSession({}, buffers={(CMD_USERTEMP_RRQ, 5): b""})
    device = Device("127.0.0.1", session=session)
    assert device.list_users() == []


def test_get_user_raises_when_absent() -> None:
    session = FakeSession({}, buffers={(CMD_USERTEMP_RRQ, 5): _user_blob()})
    device = Device("127.0.0.1", session=session)
    with pytest.raises(UserNotFoundError):
        device.get_user(999)


def test_get_user_by_user_id_returns_match() -> None:
    session = FakeSession({}, buffers={(CMD_USERTEMP_RRQ, 5): _user_blob()})
    device = Device("127.0.0.1", session=session)
    assert device.get_user_by_user_id("13").uid == 295


def test_list_fingerprints_parses_buffer() -> None:
    session = FakeSession({}, buffers={(CMD_USERTEMP_RRQ, 2): _fingerprint_blob()})
    device = Device("127.0.0.1", session=session)
    templates = device.list_fingerprints()
    assert len(templates) == 1
    assert templates[0].fid == 9
    assert templates[0].flag == 1
    assert templates[0].size == 958
    assert session.calls == [(CMD_USERTEMP_RRQ, b"\x02\x00")]


def test_get_user_fingerprints_filters_by_uid() -> None:
    session = FakeSession({}, buffers={(CMD_USERTEMP_RRQ, 2): _fingerprint_blob()})
    device = Device("127.0.0.1", session=session)
    assert len(device.get_user_fingerprints(295)) == 1
    assert device.get_user_fingerprints(999) == []


def test_list_attendance_uses_free_size_count() -> None:
    fields = [0] * 20
    fields[8] = 1
    free_sizes = struct.pack("<20i", *fields)
    session = FakeSession(
        {CMD_GET_FREE_SIZES: Response(2000, free_sizes, 0, 0)},
        buffers={(CMD_ATTLOG_RRQ, 0): _attendance_blob()},
    )
    device = Device("127.0.0.1", session=session)
    records = device.list_attendance()
    assert len(records) == 1
    assert records[0].uid == 295
    assert records[0].user_id == "13"
    assert records[0].timestamp.isoformat() == "2026-10-24T15:25:50"
    assert session.calls == [
        (CMD_GET_FREE_SIZES, b""),
        (CMD_ATTLOG_RRQ, b"\x00\x00"),
    ]


def test_list_attendance_skips_read_when_count_is_zero() -> None:
    free_sizes = struct.pack("<20i", *([0] * 20))
    session = FakeSession({CMD_GET_FREE_SIZES: Response(2000, free_sizes, 0, 0)})
    device = Device("127.0.0.1", session=session)
    assert device.list_attendance() == []
    assert session.calls == [(CMD_GET_FREE_SIZES, b"")]
