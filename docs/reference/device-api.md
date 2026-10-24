# Device API

## Why this matters

This is the exact surface most programs use. The signatures, return types, and
write behaviour matter because a small misunderstanding can turn a read-only
script into a device change.

All examples assume:

```python
from essl_f22 import Device
```

## Constructor

```text
Device(
    host: str,
    port: int = 4370,
    *,
    timeout: float = 10.0,
    comm_key: int = 0,
    encoding: str = "utf-8",
    transport: Transport | None = None,
    session: SessionLike | None = None,
    storage: StorageBackend | None = None,
    storage_backend: str = "sqlite",
    storage_path: Path | str | None = None,
    storage_options: Mapping[str, Any] | None = None,
    max_timezone_slots: int = 50,
    max_groups: int = 100,
)
```

| Argument | Meaning |
| --- | --- |
| `host` | Device IP or hostname. |
| `port` | TCP port, default `4370`. |
| `timeout` | Socket timeout in seconds. |
| `comm_key` | Device communication key. |
| `encoding` | Text encoding for names and IDs. |
| `transport` | Low-level transport override, mainly for tests. |
| `session` | Low-level session override, mainly for tests. |
| `storage` | Injected storage object; caller owns it. |
| `storage_backend` | Backend name used when storage is created lazily. |
| `storage_path` | File path or connection value for the backend. |
| `storage_options` | Backend options, such as `{"dsn": ...}`. |
| `max_timezone_slots` | Upper bound for `list_timezones()` scanning. |
| `max_groups` | Upper bound for `list_groups()` scanning. |

The constructor does **not** connect. It creates a `Session` unless you inject
one. `host`, `port`, `timeout`, and `comm_key` are used to construct that
session.

## Lifecycle

| Method | Returns | Notes |
| --- | --- | --- |
| `connect()` | `self` | Opens the socket and authenticates if required. Idempotent while connected. |
| `close()` | `None` | Closes the session and owned storage. Safe to call more than once. |
| `__enter__()` | `Device` | Calls `connect()`. |
| `__exit__()` | `None` | Calls `close()` even on error. |

```python
with Device("192.168.1.50", comm_key=0) as device:
    print(device.get_serial_number())
```

Manual lifecycle:

```python
device = Device("192.168.1.50", comm_key=0)
try:
    device.connect()
    print(device.get_device_info())
finally:
    device.close()
```

Do not share one `Device` across threads without external locking. The session
has mutable request and receive-buffer state.

## Device information

### `get_option(name: str) -> str`

Reads a device option. The SDK sends the option name followed by a NUL byte and
expects a `name=value` response. It returns the value after the first `=`.

```python
print(device.get_option("~Platform"))
print(device.get_option("~DeviceName"))
```

Option names are device-specific. The SDK uses `~Platform`, `~DeviceName`, and
`~SerialNumber` internally.

Raises `CommandError` if the device rejects the option, or `ProtocolError` if the
response has no value.

### `get_device_info() -> DeviceInfo`

Reads platform, device name, serial number, and firmware version. It performs
several commands: platform option, device name option, serial option, and
version.

```python
info = device.get_device_info()
print(info.platform, info.device_name, info.serial_number, info.firmware_version)
```

### `get_serial_number() -> str`

Reads the device serial through the `~SerialNumber` option and caches it on the
`Device` instance. Later calls return the cached value.

```python
serial = device.get_serial_number()
```

The serial scopes the mirror and block state. If the hardware changes, create a
new `Device` or clear the cached value by reconnecting a new instance.

## Users

### `list_users() -> list[User]`

Reads the full user buffer and parses 72-byte records. Returns an empty list if
the device returns no data. Device order is not guaranteed.

```python
users = device.list_users()
```

### `get_user(uid: int) -> User`

Reads all users and returns the one whose `uid` matches. Raises
`UserNotFoundError` if absent.

```python
user = device.get_user(295)
```

### `get_user_by_user_id(user_id: str) -> User`

Reads all users and returns the first whose `user_id` matches. Linear scan; not
an indexed lookup. Raises `UserNotFoundError` if absent.

```python
user = device.get_user_by_user_id("1001")
```

### `set_user(user: User) -> None`

Creates or replaces the user with `user.uid`. Sends the full 72-byte record.

- Raises `ValueError` if `uid` is outside `0`–`65535`.
- Create/read/delete have been exercised on hardware. Updating an existing
  user has not yet been hardware-validated; test it on a non-production device
  first.
- Raises `ValueError` if a string does not fit its fixed field.
- Raises `CommandError` if the device rejects the write.
- Calls `refresh_data()` after a successful acknowledgement.
- Does not read the record back to compare fields.

```python
user = device.get_user(295)
user.name = "Asha Rao"
device.set_user(user)
```

### `delete_user(uid: int) -> None`

Deletes the user with that UID.

- Raises `ValueError` if `uid` is outside `0`–`65535`.
- Raises `CommandError` if the device rejects the delete.
- Calls `refresh_data()` after success.
- Destructive; the SDK cannot undo it.

```python
device.delete_user(295)
```

## Fingerprints

### `list_fingerprints() -> list[FingerprintTemplate]`

Reads all fingerprint templates. Each item includes raw template bytes. This is
sensitive data.

```python
templates = device.list_fingerprints()
for item in templates:
    print(item.uid, item.fid, item.flag, item.size)
```

### `get_user_fingerprints(uid: int) -> list[FingerprintTemplate]`

Calls `list_fingerprints()` and filters by `uid` in Python.

```python
items = device.get_user_fingerprints(295)
```

There is no public enrollment or template-write API.

## Attendance

### `list_attendance() -> list[AttendanceRecord]`

Reads the device attendance count, then reads and parses the full attendance
buffer. Returns `[]` when the count is zero. Raises `ProtocolError` if the
record layout is not the expected 40-byte format.

```python
records = device.list_attendance()
```

There is no device-side date filter or pagination. The returned list is in
device order, not guaranteed chronological.

## Timezones

### `get_timezone(slot: int) -> TimeZone`

Reads one timezone slot. Raises `CommandError` if the device rejects the request;
the “not found” code is `0x1381`.

```python
timezone = device.get_timezone(1)
```

### `list_timezones() -> dict[int, TimeZone]`

Scans slots from `1` through `max_timezone_slots` (default `50`), skipping
`CommandError` with code `0x1381`. Other command errors propagate.

```python
timezones = device.list_timezones()
print(sorted(timezones))
```

### `set_timezone(timezone: TimeZone) -> None`

Writes a timezone slot, requires acknowledgement, and refreshes device data.

```python
from essl_f22 import DayInterval, TimeZone

timezone = TimeZone(
    slot=10,
    days=(DayInterval(9, 0, 17, 0),) * 7,
)
device.set_timezone(timezone)
```

## Groups

### `get_group(group_id: int) -> GroupInfo`

Reads one group. Raises `CommandError` if the device rejects the request.

```python
group = device.get_group(1)
```

### `list_groups() -> list[GroupInfo]`

Scans group IDs from `1` through `max_groups` (default `100`), skipping the
device's not-found code `0x1381`. Other command errors propagate.

```python
groups = device.list_groups()
```

### `set_group(group: GroupInfo) -> None`

Writes a group, requires acknowledgement, and refreshes device data.

```python
from essl_f22 import GroupInfo

device.set_group(
    GroupInfo(
        group_id=1,
        tz1=1,
        tz2=0,
        tz3=0,
        verify_style=0,
        holiday_enabled=False,
    )
)
```

## User timezone assignment

### `get_user_timezone(uid: int) -> UserTimeZone`

Reads the device's per-user assignment.

```python
assignment = device.get_user_timezone(295)
print(assignment.use_personal, assignment.tz1, assignment.tz2, assignment.tz3)
```

### `set_user_timezone(uid: int, timezone: UserTimeZone) -> None`

Writes the per-user assignment, requires acknowledgement, and refreshes data.
The SDK canonicalizes the assignment first: when `use_personal` is false, the
timezone fields are cleared. It does not read the record back for comparison;
call `get_user_timezone()` if you need verification.

```python
from essl_f22 import UserTimeZone

device.set_user_timezone(
    295,
    UserTimeZone(uid=295, use_personal=True, tz1=10),
)
```

## Capacity and time

### `get_free_sizes() -> FreeSizes`

Reads device counts and capacities.

```python
sizes = device.get_free_sizes()
print(sizes.users, sizes.users_capacity)
print(sizes.fingerprints, sizes.fingerprints_capacity)
print(sizes.attendance, sizes.attendance_capacity)
```

The device response is parsed with a 20-integer layout; a response shorter than
80 bytes raises `ProtocolError`.

### `get_time() -> datetime`

Returns the device's local time as a naive `datetime`.

```python
print(device.get_time())
```

### `set_time(value: datetime) -> None`

Writes the device time. This is a write and can affect attendance and schedules.

```python
from datetime import datetime

device.set_time(datetime(2026, 10, 24, 9, 30, 0))
```

### `refresh_data() -> None`

Asks the device to refresh its internal data. Called automatically after
successful writes.

```python
device.refresh_data()
```

## Blocking

### `block_user(uid: int) -> BlockResult`

Blocks a user by assigning a deny-all timezone. Non-destructive: the user and
templates remain. Unit-tested with fake transports; not yet validated against a
physical door or production access policy.

```python
result = device.block_user(295)
print(result.already_blocked, result.block_timezone_slot, result.original)
```

Raises:

- `UserNotFoundError` if the user is absent;
- `NoFreeTimeZoneSlotError` if no eligible slot exists;
- `DeviceVerificationError` if the read-back fails;
- `CommandError` or storage errors from underlying operations.

See [Access control and blocking](../concepts/access-control.md).

### `unblock_user(uid: int) -> UnblockResult`

Restores the saved assignment, or disables personal scheduling if no state is
saved.

```python
result = device.unblock_user(295)
print(result.restored, result.state_found)
```

### `is_user_blocked(uid: int) -> bool`

Reads the current user assignment and compares it with the saved block slot.
Returns `False` if no block slot is recorded for the device.

```python
print(device.is_user_blocked(295))
```

### `get_blocked_users() -> list[int]`

Lists UIDs from the **state store**, not a device scan.

```python
print(device.get_blocked_users())
```

## Mirror and sync

### `mirror() -> Mirror`

Returns a read-only mirror for the current device serial. Creates storage lazily.

```python
mirror = device.mirror()
```

### `sync(mode: SyncMode = "incremental") -> SyncResult`

Syncs the device into the mirror. `mode` is `"full"` or `"incremental"`.

```python
result = device.sync("full")
print(result.attendance, result.new_attendance, result.attendance_replaced)
```

`"full"` replaces all collections and attendance. `"incremental"` replaces
non-attendance collections, inserts new attendance keys, and replaces attendance
if the device count dropped.

Raises `SyncError` for an unsupported mode or a serial mismatch.

## Method summary

| Method | Kind | Returns |
| --- | --- | --- |
| `connect` | lifecycle | `Device` |
| `close` | lifecycle | `None` |
| `get_option` | read | `str` |
| `get_device_info` | read | `DeviceInfo` |
| `get_serial_number` | read/cached | `str` |
| `list_users` | read | `list[User]` |
| `get_user` | read | `User` |
| `get_user_by_user_id` | read | `User` |
| `set_user` | write | `None` |
| `delete_user` | destructive write | `None` |
| `list_fingerprints` | read | `list[FingerprintTemplate]` |
| `get_user_fingerprints` | read | `list[FingerprintTemplate]` |
| `list_attendance` | read | `list[AttendanceRecord]` |
| `get_timezone` | read | `TimeZone` |
| `list_timezones` | read scan | `dict[int, TimeZone]` |
| `set_timezone` | write | `None` |
| `get_group` | read | `GroupInfo` |
| `list_groups` | read scan | `list[GroupInfo]` |
| `set_group` | write | `None` |
| `get_user_timezone` | read | `UserTimeZone` |
| `set_user_timezone` | write | `None` |
| `get_free_sizes` | read | `FreeSizes` |
| `get_time` | read | `datetime` |
| `set_time` | write | `None` |
| `refresh_data` | device command | `None` |
| `block_user` | reversible write | `BlockResult` |
| `unblock_user` | reversible write | `UnblockResult` |
| `is_user_blocked` | read | `bool` |
| `get_blocked_users` | state read | `list[int]` |
| `mirror` | local read | `Mirror` |
| `sync` | read + storage write | `SyncResult` |

## Next

- [Models](models.md)
- [Errors](errors.md)
- [Storage](storage.md)
