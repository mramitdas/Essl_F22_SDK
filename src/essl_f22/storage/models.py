"""Typed records persisted by storage backends."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from essl_f22.models import AttendanceRecord

SyncMode = Literal["full", "incremental"]


@dataclass(frozen=True, slots=True)
class BlockTimeZoneState:
    slot: int


@dataclass(frozen=True, slots=True)
class FingerprintMetadata:
    uid: int
    fid: int
    flag: int
    size: int


@dataclass(frozen=True, slots=True)
class AttendanceEntry:
    record_key: str
    record: AttendanceRecord


@dataclass(frozen=True, slots=True)
class SyncState:
    device_serial: str
    synced_at: datetime
    mode: SyncMode
    users: int
    groups: int
    timezones: int
    fingerprints: int
    attendance: int


@dataclass(frozen=True, slots=True)
class SyncResult:
    device_serial: str
    mode: SyncMode
    synced_at: datetime
    users: int
    groups: int
    timezones: int
    fingerprints: int
    attendance: int
    new_attendance: int
    attendance_replaced: bool
