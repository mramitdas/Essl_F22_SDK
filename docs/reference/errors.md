# Errors

## Why this matters

The exception type tells you whether to retry, ask for credentials, fix a
configuration, or stop before making the situation worse. Catching the base
class is useful at the outermost boundary; catching only the base class inside
recovery code hides the information you need.

## Hierarchy

```text
ESSL22Error
├── DeviceConnectionError
├── DeviceAuthenticationError
├── DeviceTimeoutError
├── ProtocolError
├── CommandError
├── DeviceVerificationError
├── UserNotFoundError
├── NoFreeTimeZoneSlotError
└── StorageError
    ├── StorageConfigurationError
    ├── MirrorRecordNotFoundError
    ├── SyncError
    └── StateStoreError
```

## `ESSL22Error`

Base class for every SDK-defined error.

```python
from essl_f22 import ESSL22Error

try:
    ...
except ESSL22Error as exc:
    log.error("SDK failure: %s: %s", type(exc).__name__, exc)
```

Use this at a process or request boundary. Do not use it as a substitute for
handling known failures where the correct action differs.

## Device errors

### `DeviceConnectionError`

The socket could not be opened, the connection was lost, or the transport is not
usable.

Typical causes:

- wrong host or port;
- device powered off;
- firewall or VLAN block;
- connection closed by the device;
- using a closed transport.

Retryable for reads, with a bounded policy. Investigate before retrying writes.

### `DeviceTimeoutError`

A connect or command exceeded the socket timeout.

A timeout is ambiguous for writes: the device may have received and applied the
command before the response was lost. Read the current state before retrying.

### `DeviceAuthenticationError`

The device rejected the communication key or returned an unexpected connect
response.

Do not brute force the key. Ask the device administrator. Repeated failures can
be a security event.

### `ProtocolError`

A response was malformed, truncated, had invalid framing, or did not match the
expected record layout.

Common causes:

- unsupported firmware;
- a non-F22 device speaking a different dialect;
- a dropped or interleaved connection;
- an unexpected buffer size.

Capture the device model and firmware. Do not loop retries; a deterministic
protocol mismatch will not heal.

### `CommandError`

The device returned a non-success command status.

```python
from essl_f22 import CommandError

try:
    device.delete_user(295)
except CommandError as exc:
    print(f"device code: 0x{exc.code:04X}")
    print("message:", exc)
```

Attributes:

| Attribute | Meaning |
| --- | --- |
| `code` | Integer command/status code returned by the device. |
| `args[0]` | Human-readable message, if supplied. |

The not-found code `0x1381` is handled internally by `list_timezones()` and
`list_groups()`, which skip it. A direct `get_timezone()` or `get_group()` call
can still raise `CommandError` with that code.

### `DeviceVerificationError`

A block or unblock read-back did not match the intended assignment.

For a block, the manager attempts to restore the original assignment before
raising. If that restore also fails, the error message says so. For an unblock,
the manager raises without a second automatic change.

Always re-read the user's assignment after catching this error.

### `UserNotFoundError`

The requested UID or user ID does not exist.

```python
from essl_f22 import UserNotFoundError

try:
    user = device.get_user(295)
except UserNotFoundError:
    print("no such user")
```

`Mirror.get_user()` also raises `UserNotFoundError` when the mirror has no such
user.

### `NoFreeTimeZoneSlotError`

The blocking manager could not find a free default-allow-all timezone slot that
is unreferenced by groups and personal schedules.

This is a capacity/configuration problem, not a transient network problem.
Free a slot or choose another access-control method.

## Storage errors

### `StorageError`

Base class for storage failures. Catch a subclass when the response differs.

### `StorageConfigurationError`

The backend name is unknown, a required driver is missing, or a connection
value is missing/invalid.

Examples:

- `storage_backend="postgres"` without the `postgres` extra;
- an external backend without a DSN/URI/URL;
- a MySQL DSN without a database;
- a MongoDB URI without a database;
- an invalid Redis URL.

This is a configuration error. Fix it; do not retry the same call unchanged.

### `StateStoreError`

Block state could not be read or written, or a local SQLite/JSON store could not
be initialized.

Typical causes:

- permissions;
- disk full;
- corrupt JSON;
- unsupported JSON format version;
- SQLite open failure;
- closed external storage.

A `StateStoreError` during blocking is serious: the device may have changed even
though the state was not saved. Stop and inspect.

### `MirrorRecordNotFoundError`

A mirror timezone or group record is absent.

```python
from essl_f22 import MirrorRecordNotFoundError

try:
    timezone = mirror.get_timezone(99)
except MirrorRecordNotFoundError:
    print("slot 99 is not in the mirror")
```

`Mirror.get_user()` uses `UserNotFoundError` instead.

### `SyncError`

A sync could not be performed:

- unsupported mode (anything other than `"full"` or `"incremental"`);
- the device serial does not match the mirror serial.

This is usually a programming or targeting error. Fix the mode or use the
correct mirror.

## Non-SDK exceptions

The SDK can also raise standard Python exceptions:

| Exception | Cause |
| --- | --- |
| `ValueError` | UID outside `0`–`65535`, or an encoded user field does not fit. |
| `TypeError` | Wrong argument type or unsupported value. |
| `OSError` | Underlying socket/file problem not wrapped by the SDK. |

Do not catch `ValueError` as if it were a device failure. It usually means the
input is invalid.

## Retry matrix

| Error | Retry reads? | Retry writes? |
| --- | --- | --- |
| `DeviceConnectionError` | Yes, bounded backoff | Verify first; then decide |
| `DeviceTimeoutError` | Yes, bounded backoff | Verify first; then decide |
| `DeviceAuthenticationError` | No | No |
| `ProtocolError` | No | No |
| `CommandError` | No, unless the request/state changed | No, unless the request/state changed |
| `DeviceVerificationError` | Re-read state | Only after re-reading state |
| `UserNotFoundError` | No | No |
| `NoFreeTimeZoneSlotError` | No | Free a slot first |
| `StorageConfigurationError` | No | No |
| `StateStoreError` | Fix storage first | Fix storage first |
| `MirrorRecordNotFoundError` | Re-sync or use another slot | Not a write path |
| `SyncError` | Fix mode/serial | Not a write path |

## Logging exceptions

Log the type, message, and operation. For `CommandError`, log the code. Do not
log:

- the communication key;
- database passwords or full DSNs;
- fingerprint template bytes;
- full user or attendance records unless approved.

```python
import logging

from essl_f22 import CommandError, ESSL22Error

log = logging.getLogger(__name__)

try:
    ...
except CommandError as exc:
    log.error("device command failed code=0x%04X", exc.code)
except ESSL22Error as exc:
    log.error("sdk failure type=%s message=%s", type(exc).__name__, exc)
```

## Next

- [Handle errors](../guides/handle-errors.md)
- [Troubleshooting](../help/troubleshooting.md)
- [Device API](device-api.md)
