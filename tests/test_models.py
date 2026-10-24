import pytest

from essl_f22.errors import ProtocolError
from essl_f22.models import User, parse_user_records

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
