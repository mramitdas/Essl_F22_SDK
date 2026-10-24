import pytest

from essl_f22.errors import ProtocolError
from essl_f22.models import (
    DayInterval,
    GroupInfo,
    TimeZone,
    User,
    UserTimeZone,
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


def test_timezone_parses_default_allow_all() -> None:
    data = bytes.fromhex(
        "01000000173b0000173b0000173b0000173b0000173b0000173b0000173b0000"
    )
    tz = TimeZone.from_response(data)
    assert tz.slot == 1
    assert len(tz.days) == 7
    assert tz.is_default_allow_all()
    assert not tz.is_deny_all()


def test_timezone_encodes_deny_all_request() -> None:
    tz = TimeZone(
        slot=6,
        days=(DayInterval(23, 59, 0, 0),) * 7,
    )
    assert tz.is_deny_all()
    assert tz.to_request().hex() == "06000000" + "173b0000" * 7


def test_timezone_rejects_truncated_response() -> None:
    with pytest.raises(ProtocolError):
        TimeZone.from_response(b"\x01" * 31)


def test_group_info_parses_and_encodes() -> None:
    group = GroupInfo.from_response(bytes.fromhex("0101000000000000"))
    assert group.group_id == 1
    assert (group.tz1, group.tz2, group.tz3) == (1, 0, 0)
    assert group.verify_style == 0
    assert group.holiday_enabled is False
    assert group.to_request() == bytes.fromhex("0101000000000000")


def test_user_timezone_parses_personal_and_canonicalizes_group() -> None:
    tz = UserTimeZone.from_response(295, bytes.fromhex("0100060000000000"))
    assert tz.use_personal is True
    assert (tz.tz1, tz.tz2, tz.tz3) == (6, 0, 0)
    assert tz.to_request() == bytes.fromhex("2701000001000000060000000000000000000000")

    group_tz = UserTimeZone.from_response(295, b"\x00" * 8)
    assert group_tz.canonical() == UserTimeZone(295, False, 0, 0, 0)


def test_group_info_rejects_invalid_length() -> None:
    for size in (7, 9):
        with pytest.raises(ProtocolError):
            GroupInfo.from_response(b"\x00" * size)


def test_user_timezone_rejects_invalid_length() -> None:
    for size in (7, 9):
        with pytest.raises(ProtocolError):
            UserTimeZone.from_response(295, b"\x00" * size)
