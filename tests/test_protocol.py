import pytest

from essl_f22.errors import ProtocolError
from essl_f22.protocol import build_frame, checksum, make_comm_key, parse_frame


def test_checksum_matches_device_compatible_variant() -> None:
    header = bytes.fromhex("e80300000000feff")
    assert checksum(header) == 0xFC17


def test_make_comm_key_for_zero_key_and_session() -> None:
    assert make_comm_key(0, 0) == bytes.fromhex("617d3279")


def test_build_connect_frame_matches_validated_device_packet() -> None:
    frame, next_reply_id = build_frame(1000, b"", 0, 65534)
    assert frame.hex() == "5050827d08000000e80317fc00000000"
    assert next_reply_id == 0


def test_parse_frame_round_trips() -> None:
    frame, _ = build_frame(2000, b"ok", 12, 3)
    response = parse_frame(frame)
    assert response.command == 2000
    assert response.data == b"ok"
    assert response.session_id == 12
    assert response.reply_id == 4


def test_parse_frame_rejects_bad_magic() -> None:
    with pytest.raises(ProtocolError):
        parse_frame(b"\x00" * 16)
