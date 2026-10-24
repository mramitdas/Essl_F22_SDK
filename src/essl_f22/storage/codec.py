"""JSON-compatible codecs for storage records."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from essl_f22.errors import StateStoreError
from essl_f22.models import (
    AttendanceRecord,
    DayInterval,
    DeviceInfo,
    GroupInfo,
    TimeZone,
    User,
    UserTimeZone,
)
from essl_f22.storage.models import (
    BlockTimeZoneState,
    FingerprintMetadata,
    SyncMode,
    SyncState,
)

Document = dict[str, Any]


def _as_document(value: object) -> Document:
    if not isinstance(value, dict):
        raise StateStoreError("storage document must be a JSON object")
    return value


def _as_str(document: Document, key: str) -> str:
    value = document.get(key)
    if not isinstance(value, str):
        raise StateStoreError(f"document field {key!r} must be a string")
    return value


def _as_int(document: Document, key: str) -> int:
    value = document.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise StateStoreError(f"document field {key!r} must be an integer")
    return value


def _as_bool(document: Document, key: str) -> bool:
    value = document.get(key)
    if not isinstance(value, bool):
        raise StateStoreError(f"document field {key!r} must be a boolean")
    return value


def _as_datetime(document: Document, key: str) -> datetime:
    value = _as_str(document, key)
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise StateStoreError(f"document field {key!r} is not a timestamp") from exc


def _datetime_document(value: datetime) -> str:
    return value.isoformat()


def _as_mode(document: Document, key: str) -> SyncMode:
    value = _as_str(document, key)
    if value not in {"full", "incremental"}:
        raise StateStoreError(f"document field {key!r} is not a sync mode")
    return value  # type: ignore[return-value]


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def user_document(user: User) -> Document:
    return {
        "uid": user.uid,
        "user_id": user.user_id,
        "name": user.name,
        "privilege": user.privilege,
        "password": user.password,
        "card": user.card,
        "group_id": user.group_id,
        "timezone_flag": user.timezone_flag,
        "tz1": user.tz1,
        "tz2": user.tz2,
        "tz3": user.tz3,
    }


def user_from_document(document: Document) -> User:
    return User(
        uid=_as_int(document, "uid"),
        user_id=_as_str(document, "user_id"),
        name=_as_str(document, "name"),
        privilege=_as_int(document, "privilege"),
        password=_as_str(document, "password"),
        card=_as_int(document, "card"),
        group_id=_as_int(document, "group_id"),
        timezone_flag=_as_int(document, "timezone_flag"),
        tz1=_as_int(document, "tz1"),
        tz2=_as_int(document, "tz2"),
        tz3=_as_int(document, "tz3"),
    )


def group_document(group: GroupInfo) -> Document:
    return {
        "group_id": group.group_id,
        "tz1": group.tz1,
        "tz2": group.tz2,
        "tz3": group.tz3,
        "verify_style": group.verify_style,
        "holiday_enabled": group.holiday_enabled,
    }


def group_from_document(document: Document) -> GroupInfo:
    return GroupInfo(
        group_id=_as_int(document, "group_id"),
        tz1=_as_int(document, "tz1"),
        tz2=_as_int(document, "tz2"),
        tz3=_as_int(document, "tz3"),
        verify_style=_as_int(document, "verify_style"),
        holiday_enabled=_as_bool(document, "holiday_enabled"),
    )


def timezone_document(timezone: TimeZone) -> Document:
    return {
        "slot": timezone.slot,
        "days": [
            [day.start_hour, day.start_minute, day.end_hour, day.end_minute]
            for day in timezone.days
        ],
    }


def timezone_from_document(document: Document) -> TimeZone:
    raw_days = document.get("days")
    if not isinstance(raw_days, list) or len(raw_days) != 7:
        raise StateStoreError("timezone document must contain seven days")
    days: list[DayInterval] = []
    for raw_day in raw_days:
        if not isinstance(raw_day, list) or len(raw_day) != 4:
            raise StateStoreError("timezone day must contain four integers")
        if not all(
            isinstance(value, int) and not isinstance(value, bool) for value in raw_day
        ):
            raise StateStoreError("timezone day values must be integers")
        days.append(DayInterval(*raw_day))
    return TimeZone(slot=_as_int(document, "slot"), days=tuple(days))


def user_timezone_document(timezone: UserTimeZone) -> Document:
    return {
        "uid": timezone.uid,
        "use_personal": timezone.use_personal,
        "tz1": timezone.tz1,
        "tz2": timezone.tz2,
        "tz3": timezone.tz3,
    }


def user_timezone_from_document(document: Document) -> UserTimeZone:
    return UserTimeZone(
        uid=_as_int(document, "uid"),
        use_personal=_as_bool(document, "use_personal"),
        tz1=_as_int(document, "tz1"),
        tz2=_as_int(document, "tz2"),
        tz3=_as_int(document, "tz3"),
    )


def device_info_document(info: DeviceInfo) -> Document:
    return {
        "platform": info.platform,
        "device_name": info.device_name,
        "serial_number": info.serial_number,
        "firmware_version": info.firmware_version,
    }


def device_info_from_document(document: Document) -> DeviceInfo:
    return DeviceInfo(
        platform=_as_str(document, "platform"),
        device_name=_as_str(document, "device_name"),
        serial_number=_as_str(document, "serial_number"),
        firmware_version=_as_str(document, "firmware_version"),
    )


def fingerprint_metadata_document(fingerprint: FingerprintMetadata) -> Document:
    return {
        "uid": fingerprint.uid,
        "fid": fingerprint.fid,
        "flag": fingerprint.flag,
        "size": fingerprint.size,
    }


def fingerprint_metadata_from_document(document: Document) -> FingerprintMetadata:
    return FingerprintMetadata(
        uid=_as_int(document, "uid"),
        fid=_as_int(document, "fid"),
        flag=_as_int(document, "flag"),
        size=_as_int(document, "size"),
    )


def attendance_record_document(record: AttendanceRecord) -> Document:
    return {
        "uid": record.uid,
        "user_id": record.user_id,
        "timestamp": _datetime_document(record.timestamp),
        "status": record.status,
        "punch": record.punch,
    }


def attendance_record_from_document(document: Document) -> AttendanceRecord:
    return AttendanceRecord(
        uid=_as_int(document, "uid"),
        user_id=_as_str(document, "user_id"),
        timestamp=_as_datetime(document, "timestamp"),
        status=_as_int(document, "status"),
        punch=_as_int(document, "punch"),
    )


def attendance_record_key(record: AttendanceRecord) -> str:
    payload = _canonical_json(attendance_record_document(record))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def sync_state_document(state: SyncState) -> Document:
    return {
        "device_serial": state.device_serial,
        "synced_at": _datetime_document(state.synced_at),
        "mode": state.mode,
        "users": state.users,
        "groups": state.groups,
        "timezones": state.timezones,
        "fingerprints": state.fingerprints,
        "attendance": state.attendance,
    }


def sync_state_from_document(document: Document) -> SyncState:
    return SyncState(
        device_serial=_as_str(document, "device_serial"),
        synced_at=_as_datetime(document, "synced_at"),
        mode=_as_mode(document, "mode"),
        users=_as_int(document, "users"),
        groups=_as_int(document, "groups"),
        timezones=_as_int(document, "timezones"),
        fingerprints=_as_int(document, "fingerprints"),
        attendance=_as_int(document, "attendance"),
    )


def block_timezone_document(state: BlockTimeZoneState) -> Document:
    return {"slot": state.slot}


def block_timezone_from_document(document: Document) -> BlockTimeZoneState:
    return BlockTimeZoneState(slot=_as_int(document, "slot"))


def document_from_json(payload: str) -> Document:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise StateStoreError("stored document is not valid JSON") from exc
    return _as_document(value)


def document_to_json(document: Document) -> str:
    try:
        return json.dumps(document, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise StateStoreError("document is not JSON serializable") from exc
