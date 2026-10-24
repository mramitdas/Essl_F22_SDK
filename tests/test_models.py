import pytest

from essl_f22.errors import ProtocolError
from essl_f22.models import (
    User,
    parse_attendance_records,
    parse_fingerprint_templates,
    parse_user_records,
)

RECORD_HEX = (
    "2701000000000000000000000000000000000000000000000000000000000000"
    "0000000000000001000001000000000031330000000000000000000000000000"
    "0000000000000000"
)


def test_user_record_parses_validated_user_295() -> None:
    user = User.from_record(bytes.fromhex(RECORD_HEX))
    assert user.uid == 295
    assert user.user_id == "13"
    assert user.name == ""
    assert user.privilege == 0
    assert user.group_id == 1
    assert user.timezone_flag == 0
    assert (user.tz1, user.tz2, user.tz3) == (1, 0, 0)
    assert user.to_record().hex() == RECORD_HEX


def test_user_record_rejects_truncated_data() -> None:
    with pytest.raises(ProtocolError):
        User.from_record(b"\x00" * 71)


def test_parse_user_records_reads_total_size_prefix() -> None:
    record = bytes.fromhex(RECORD_HEX)
    blob = (72).to_bytes(4, "little") + record
    users = parse_user_records(blob)
    assert users[0].uid == 295


def test_parse_user_records_rejects_non_multiple_size() -> None:
    blob = (73).to_bytes(4, "little") + b"\x00" * 73
    with pytest.raises(ProtocolError):
        parse_user_records(blob)


def test_parse_attendance_record() -> None:
    timestamp = (26 * 12 * 31 + 9 * 31 + 24 - 1) * 86400 + (15 * 60 + 25) * 60 + 50
    record = (
        (295).to_bytes(2, "little")
        + b"13".ljust(24, b"\x00")
        + b"\x01"
        + timestamp.to_bytes(4, "little")
        + b"\x00"
        + b"\x00" * 8
    )
    blob = (40).to_bytes(4, "little") + record
    records = parse_attendance_records(blob, 1)
    assert records[0].uid == 295
    assert records[0].user_id == "13"
    assert records[0].status == 1
    assert records[0].punch == 0
    assert records[0].timestamp.isoformat() == "2026-10-24T15:25:50"


def test_parse_fingerprint_template() -> None:
    template = b"\xab" * 952
    entry = (
        (958).to_bytes(2, "little")
        + (295).to_bytes(2, "little")
        + b"\x09"
        + b"\x01"
        + template
    )
    blob = (len(entry)).to_bytes(4, "little") + entry
    templates = parse_fingerprint_templates(blob)
    assert templates[0].uid == 295
    assert templates[0].fid == 9
    assert templates[0].flag == 1
    assert templates[0].size == 958
    assert templates[0].template == template


def test_parse_attendance_rejects_truncated_record() -> None:
    blob = (40).to_bytes(4, "little") + b"\x00" * 39
    with pytest.raises(ProtocolError):
        parse_attendance_records(blob, 1)


def test_parse_attendance_rejects_indivisible_total_size() -> None:
    blob = (41).to_bytes(4, "little") + b"\x00" * 41
    with pytest.raises(ProtocolError):
        parse_attendance_records(blob, 2)


def test_parse_fingerprint_rejects_too_small_entry() -> None:
    entry = (5).to_bytes(2, "little") + b"\x00" * 5
    blob = (len(entry)).to_bytes(4, "little") + entry
    with pytest.raises(ProtocolError):
        parse_fingerprint_templates(blob)


def test_parse_fingerprint_rejects_truncated_template() -> None:
    entry = (20).to_bytes(2, "little") + b"\x00" * 10
    blob = (len(entry)).to_bytes(4, "little") + entry
    with pytest.raises(ProtocolError):
        parse_fingerprint_templates(blob)
