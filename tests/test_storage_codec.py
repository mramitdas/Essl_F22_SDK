from datetime import datetime

from essl_f22.models import (
    AttendanceRecord,
    DayInterval,
    DeviceInfo,
    GroupInfo,
    TimeZone,
    User,
    UserTimeZone,
)
from essl_f22.storage.codec import (
    attendance_record_document,
    attendance_record_from_document,
    attendance_record_key,
    device_info_document,
    device_info_from_document,
    group_document,
    group_from_document,
    timezone_document,
    timezone_from_document,
    user_document,
    user_from_document,
    user_timezone_document,
    user_timezone_from_document,
)


def test_user_document_round_trips() -> None:
    user = User(
        uid=295,
        user_id="13",
        name="Amit",
        privilege=14,
        password="1234",
        card=99,
        group_id=2,
        timezone_flag=1,
        tz1=6,
        tz2=7,
        tz3=8,
    )

    assert user_from_document(user_document(user)) == user


def test_group_document_round_trips() -> None:
    group = GroupInfo(2, 3, 4, 5, 14, True)

    assert group_from_document(group_document(group)) == group


def test_timezone_document_round_trips() -> None:
    timezone = TimeZone(
        slot=6,
        days=(DayInterval(23, 59, 0, 0),) * 7,
    )

    assert timezone_from_document(timezone_document(timezone)) == timezone


def test_user_timezone_document_round_trips() -> None:
    timezone = UserTimeZone(295, True, 6, 7, 8)

    assert user_timezone_from_document(user_timezone_document(timezone)) == timezone


def test_device_info_document_round_trips() -> None:
    info = DeviceInfo("ZLM60_TFT", "x 2008", "JJA1242200334", "Ver 6.60")

    assert device_info_from_document(device_info_document(info)) == info


def test_attendance_document_round_trips() -> None:
    record = AttendanceRecord(
        uid=295,
        user_id="13",
        timestamp=datetime(2026, 10, 24, 16, 59, 24),
        status=1,
        punch=0,
    )

    assert attendance_record_from_document(attendance_record_document(record)) == record


def test_attendance_record_key_is_stable_and_field_sensitive() -> None:
    first = AttendanceRecord(
        uid=295,
        user_id="13",
        timestamp=datetime(2026, 10, 24, 16, 59, 24),
        status=1,
        punch=0,
    )
    same = AttendanceRecord(
        uid=295,
        user_id="13",
        timestamp=datetime(2026, 10, 24, 16, 59, 24),
        status=1,
        punch=0,
    )
    changed = AttendanceRecord(
        uid=295,
        user_id="13",
        timestamp=datetime(2026, 10, 24, 16, 59, 25),
        status=1,
        punch=0,
    )

    assert attendance_record_key(first) == attendance_record_key(same)
    assert attendance_record_key(first) != attendance_record_key(changed)
    assert len(attendance_record_key(first)) == 64
