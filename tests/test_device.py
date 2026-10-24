import struct
from datetime import datetime

import pytest

from essl_f22.device import Device
from essl_f22.errors import ProtocolError
from essl_f22.protocol import (
    CMD_GET_FREE_SIZES,
    CMD_GET_TIME,
    CMD_GET_VERSION,
    CMD_OPTIONS_RRQ,
    CMD_SET_TIME,
    Response,
    decode_device_time,
    encode_device_time,
)
from tests.fakes import FakeSession


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
