# Models

## Why this matters

The models are the typed boundary between binary device records and your
application. If you know which fields exist, which are mutable, and which are
validated only at write time, you can avoid both silent field loss and invalid
device records.

Most models are frozen value objects. `User` is the important exception: it is
mutable so you can read, modify, and write it back.

## `User`

```python
@dataclass(slots=True)
class User:
    uid: int
    user_id: str
    name: str = ""
    privilege: int = 0
    password: str = ""
    card: int = 0
    group_id: int = 1
    timezone_flag: int = 0
    tz1: int = 0
    tz2: int = 0
    tz3: int = 0
```

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `uid` | `int` | required | Internal slot; `0`–`65535` enforced by `set_user()` and `delete_user()`. |
| `user_id` | `str` | required | Up to 23 encoded bytes. |
| `name` | `str` | `""` | Up to 23 encoded bytes. |
| `privilege` | `int` | `0` | Device-specific. |
| `password` | `str` | `""` | Up to 7 encoded bytes. |
| `card` | `int` | `0` | Unsigned 32-bit field. |
| `group_id` | `int` | `1` | Group membership. |
| `timezone_flag` | `int` | `0` | Personal schedule flag in the user record. |
| `tz1`–`tz3` | `int` | `0` | Personal timezone slots in the user record. |

`User` is **mutable**. It is not frozen.

### `User.from_record(data: bytes, encoding: str = "utf-8") -> User`

Decodes exactly 72 bytes. Raises `ProtocolError` if the length is not 72.

### `User.to_record(encoding: str = "utf-8") -> bytes`

Encodes exactly 72 bytes. Raises `ValueError` if an encoded string does not fit
its fixed field.

The wire layout is `<HB8s24sIBHHHH24s`:

```text
uid, privilege, password, name, card, group_id,
timezone_flag, tz1, tz2, tz3, user_id
```

The total is 72 bytes.

### Validation timing

`User(uid=70000, ...)` can be constructed. The UID range is checked when you call
`set_user()` or `delete_user()`. String length is checked when `to_record()` is
called, which `set_user()` does.

Do not confuse “the object was constructed” with “the record is valid for the
device”.

## `AttendanceRecord`

```python
@dataclass(frozen=True, slots=True)
class AttendanceRecord:
    uid: int
    user_id: str
    timestamp: datetime
    status: int
    punch: int
```

Frozen. The device record is 40 bytes.

| Field | Meaning |
| --- | --- |
| `uid` | Internal user slot at punch time. |
| `user_id` | User identifier at punch time. |
| `timestamp` | Naive device-local time. |
| `status` | Device status code; not interpreted by the SDK. |
| `punch` | Device punch/verify value; not interpreted by the SDK. |

There is no timezone attached to `timestamp`.

## `FingerprintTemplate`

```python
@dataclass(frozen=True, slots=True)
class FingerprintTemplate:
    uid: int
    fid: int
    flag: int
    template: bytes

    @property
    def size(self) -> int:
        return len(self.template) + 6
```

Frozen. `size` includes the 6-byte device entry header. The `template` bytes are
sensitive and proprietary; the SDK does not decode them.

## `DayInterval`

```python
@dataclass(frozen=True, slots=True)
class DayInterval:
    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int
```

`allows(value: datetime) -> bool`:

- returns `False` if `(start_hour, start_minute) >= (end_hour, end_minute)`;
- otherwise compares the value's hour/minute, with **inclusive** start and end.

Examples:

```python
DayInterval(9, 0, 17, 0).allows(datetime(2026, 10, 24, 9, 0))  # True
DayInterval(9, 0, 17, 0).allows(datetime(2026, 10, 24, 17, 0))  # True
DayInterval(9, 0, 17, 0).allows(datetime(2026, 10, 24, 17, 1))  # False
DayInterval(0, 0, 0, 0).allows(datetime(2026, 10, 24, 12, 0))  # False
```

The model does not support an interval that crosses midnight. A start at or
after the end is treated as deny-all for that day.

## `TimeZone`

```python
@dataclass(frozen=True, slots=True)
class TimeZone:
    slot: int
    days: tuple[DayInterval, ...]
```

Frozen. `days` holds seven intervals, one per weekday.

### `TimeZone.from_response(data: bytes) -> TimeZone`

Decodes exactly 32 bytes: a 2-byte slot plus seven 4-byte day intervals. Raises
`ProtocolError` if the length is not 32.

### `TimeZone.to_request() -> bytes`

Encodes the slot and seven intervals into 32 bytes.

### `is_default_allow_all() -> bool`

True when every day is exactly `00:00–23:59`.

### `is_deny_all() -> bool`

True when every day has start greater than or equal to end.

The blocking manager uses these helpers to choose and validate slots.

## `GroupInfo`

```python
@dataclass(frozen=True, slots=True)
class GroupInfo:
    group_id: int
    tz1: int
    tz2: int
    tz3: int
    verify_style: int
    holiday_enabled: bool
```

Frozen. Encodes to 8 bytes.

- `verify_style` is `flags & 0x7F` on decode.
- `holiday_enabled` is bit `0x80` of the same flags byte.
- `tz1`–`tz3` are timezone slot references.

## `UserTimeZone`

```python
@dataclass(frozen=True, slots=True)
class UserTimeZone:
    uid: int
    use_personal: bool
    tz1: int = 0
    tz2: int = 0
    tz3: int = 0
```

Frozen. Represents the device's per-user timezone assignment, separate from the
`User` record fields.

### `canonical() -> UserTimeZone`

- if `use_personal` is true, returns `self`;
- if false, returns a copy with `use_personal=False` and all timezone fields
  cleared.

`unblock_user()` uses this to avoid restoring meaningless timezone values when
personal scheduling is disabled.

## `DeviceInfo`

```python
@dataclass(frozen=True, slots=True)
class DeviceInfo:
    platform: str
    device_name: str
    serial_number: str
    firmware_version: str
```

Frozen. Values come from device options and the version command.

## `FreeSizes`

```python
@dataclass(frozen=True, slots=True)
class FreeSizes:
    users: int
    fingerprints: int
    attendance: int
    users_capacity: int
    fingerprints_capacity: int
    attendance_capacity: int
```

Frozen. `users`, `fingerprints`, and `attendance` are current counts; the
`*_capacity` fields are device limits.

## Blocking result models

### `BlockResult`

```python
@dataclass(frozen=True, slots=True)
class BlockResult:
    uid: int
    user_id: str
    already_blocked: bool
    block_timezone_slot: int
    original: UserTimeZone
```

`original` is the assignment the SDK intended to save. On an idempotent block,
it is the saved original when available.

### `UnblockResult`

```python
@dataclass(frozen=True, slots=True)
class UnblockResult:
    uid: int
    user_id: str
    restored: UserTimeZone
    state_found: bool
```

`state_found=False` means the SDK had no saved original and used the fallback
non-personal assignment.

## Storage models

### `FingerprintMetadata`

```python
@dataclass(frozen=True, slots=True)
class FingerprintMetadata:
    uid: int
    fid: int
    flag: int
    size: int
```

The mirror stores this instead of template bytes.

### `BlockTimeZoneState`

```python
@dataclass(frozen=True, slots=True)
class BlockTimeZoneState:
    slot: int
```

The saved deny-all slot for a device serial.

### `AttendanceEntry`

```python
@dataclass(frozen=True, slots=True)
class AttendanceEntry:
    record_key: str
    record: AttendanceRecord
```

Used when writing attendance to storage. `record_key` is normally the stable
SHA-256 hash.

### `SyncMode`

```python
SyncMode = Literal["full", "incremental"]
```

### `SyncState`

```python
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
```

Stored after a sync. `synced_at` is local time, not device time.

### `SyncResult`

```python
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
```

Returned by `Device.sync()` and `Mirror.sync()`.

### `MirrorSnapshot`

```python
@dataclass(frozen=True, slots=True)
class MirrorSnapshot:
    device_info: DeviceInfo | None
    users: tuple[User, ...]
    groups: tuple[GroupInfo, ...]
    timezones: dict[int, TimeZone]
    fingerprints: tuple[FingerprintMetadata, ...]
    attendance: tuple[AttendanceRecord, ...]
    sync_state: SyncState | None
```

Loaded by `Mirror.snapshot()`. This can be large because it includes all
attendance.

## Next

- [Device API](device-api.md)
- [Errors](errors.md)
- [Storage](storage.md)
