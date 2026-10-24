# Handle errors

## Why this matters

A device integration fails in more ways than a normal function call: the network
drops, the key is wrong, the device rejects a command, a response is malformed,
a database is unavailable, or a write succeeds on the device but the
acknowledgement never arrives. Treating all of these as “something went wrong”
makes recovery dangerous.

This guide shows which errors to catch, which to retry, and which to stop on.

## The error tree

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

All SDK errors inherit from `ESSL22Error`. That gives you a clean outer catch
without catching programming mistakes such as `TypeError` or `AttributeError`.

## What each error means

| Error | Meaning | Typical action |
| --- | --- | --- |
| `DeviceConnectionError` | The socket could not open, closed, or is not usable. | Check network and device power; retry a read with backoff. |
| `DeviceTimeoutError` | A connect or command exceeded the timeout. | Check network; retry reads cautiously. For writes, verify state first. |
| `DeviceAuthenticationError` | The communication key was rejected or the connect response was unexpected. | Ask for the correct key; do not brute force. |
| `ProtocolError` | The response was malformed, truncated, or unsupported. | Capture model/firmware; do not loop retries. |
| `CommandError` | The device returned a non-success command code. | Inspect `exc.code`; fix the request or device state. |
| `DeviceVerificationError` | A block/unblock read-back did not match. | Re-read the user's assignment; do not assume success. |
| `UserNotFoundError` | The requested UID or user ID does not exist. | Confirm the identifier; create the user if intended. |
| `NoFreeTimeZoneSlotError` | No eligible timezone slot is available for blocking. | Free a slot or use another access-control method. |
| `StorageError` | Base for storage failures. | Handle the specific subclass where possible. |
| `StorageConfigurationError` | Unknown backend, missing driver, or missing connection value. | Install the extra or fix the DSN/URI/URL. |
| `MirrorRecordNotFoundError` | A mirror timezone or group record is absent. | Re-sync or check the slot/group ID. |
| `SyncError` | Unsupported sync mode or serial mismatch. | Fix the mode or use the correct mirror. |
| `StateStoreError` | Block state could not be read or written. | Check permissions, disk, and database availability. |

`CommandError` exposes the device code:

```python
from essl_f22 import CommandError

try:
    ...
except CommandError as exc:
    print(f"device rejected command with 0x{exc.code:04X}")
```

## A basic read pattern

```python
from essl_f22 import (
    Device,
    DeviceAuthenticationError,
    DeviceConnectionError,
    DeviceTimeoutError,
    ESSL22Error,
)

try:
    with Device("192.168.1.50", comm_key=0, timeout=10.0) as device:
        users = device.list_users()
        print("users:", len(users))
except DeviceAuthenticationError:
    print("The communication key was rejected. Ask the administrator.")
except DeviceTimeoutError:
    print("The device did not answer in time. Check the network and address.")
except DeviceConnectionError as exc:
    print("Connection failed:", exc)
except ESSL22Error as exc:
    print("SDK error:", type(exc).__name__, exc)
```

Why this order:

- authentication is a configuration/security problem, not a transient network
  problem;
- timeout and connection failures are infrastructure problems;
- the outer `ESSL22Error` catches anything else from the SDK;
- programming errors are not swallowed.

## Retrying reads

Reads are usually safe to retry because they do not change the device. Use a
small, bounded retry with a delay:

```python
import time

from essl_f22 import Device, DeviceConnectionError, DeviceTimeoutError


def read_users(host: str, comm_key: int, attempts: int = 3) -> list:
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            with Device(host, comm_key=comm_key, timeout=10.0) as device:
                return device.list_users()
        except (DeviceConnectionError, DeviceTimeoutError) as exc:
            last_error = exc
            print(f"read attempt {attempt} failed: {exc}")
            if attempt < attempts:
                time.sleep(2**attempt)

    raise RuntimeError("device read failed after retries") from last_error
```

Do not retry:

- `DeviceAuthenticationError`;
- `ProtocolError`;
- `StorageConfigurationError`;
- `UserNotFoundError` when the absence is expected and meaningful;
- `CommandError` without changing the request or device state.

For large attendance reads, a timeout may simply mean “increase the timeout or
run off-peak”, not “retry immediately”.

## Writes and ambiguous outcomes

A write is different. A timeout can occur after the device received the command
but before the SDK read the acknowledgement. The write may have succeeded.

```python
from essl_f22 import Device, DeviceTimeoutError

try:
    with Device("192.168.1.50", comm_key=0) as device:
        device.set_user(user)
except DeviceTimeoutError:
    print("Outcome unknown. Reconnect and read the record before retrying.")
    # Do not blindly call set_user() again.
```

Recovery pattern:

1. Reconnect with a new `Device`.
2. Read the target record.
3. Compare it with the intended state.
4. If it matches, treat the write as successful.
5. If it does not match, decide whether to retry.
6. Record what you observed.

Never retry a delete or a timezone write just because the first call timed out.

## CommandError

`CommandError` means the device responded, but rejected the operation. Retrying
the same bytes usually produces the same rejection.

Common causes:

- the UID does not exist;
- a timezone slot is absent;
- the device is in a mode that rejects writes;
- the record is invalid for that firmware;
- a prerequisite command was not performed.

Inspect the code and the operation. For `list_timezones()` and `list_groups()`,
the SDK internally skips the device's “not found” code `0x1381`; other command
errors propagate.

## Verification errors

`DeviceVerificationError` is specific to blocking/unblocking. When a block
read-back does not match, the manager attempts to restore the original schedule
before raising. When an unblock read-back does not match, it raises without a
second automatic change.

After catching it:

1. reconnect;
2. read `get_user_timezone(uid)`;
3. compare with the intended state;
4. restore deliberately if needed;
5. do not report success to the operator until the device matches.

## Storage errors

### Missing driver or connection value

```python
from essl_f22 import StorageConfigurationError

try:
    device = Device(
        "192.168.1.50",
        storage_backend="postgres",
        storage_options={},
    )
    device.sync("full")
except StorageConfigurationError as exc:
    print("Fix storage configuration:", exc)
```

The backend is created lazily, so the error appears at the first storage
operation, not at `Device(...)` construction.

### State store failure during blocking

A `StateStoreError` during `block_user()` is serious: the SDK may have changed
the device but failed to save the original assignment. Stop, inspect the user's
current schedule, and restore from backup or a recorded value.

### Partial sync

A storage error during `sync()` can leave some collections updated and others
not. The sync is not atomic across collections. Re-run a full sync after fixing
the storage problem, and verify counts before trusting reports.

## Logging safely

Log:

- operation name;
- device serial or a non-secret device label;
- UID/user ID only if your privacy policy allows it;
- exception type and message;
- command code for `CommandError`;
- timestamps and retry counts.

Do not log:

- communication keys;
- database passwords or full DSNs;
- fingerprint template bytes;
- full attendance exports;
- names and other personal data unless necessary and approved.

A useful log line:

```text
sync failed serial=ABC123 mode=incremental error=StateStoreError retry=2
```

## Cleanup

Use the context manager so the socket and owned storage are closed even on
failure:

```python
with Device("192.168.1.50", comm_key=0) as device:
    device.list_users()
```

If you manage the lifecycle manually, use `try/finally`:

```python
device = Device("192.168.1.50", comm_key=0)
try:
    device.connect()
    device.list_users()
finally:
    device.close()
```

If you injected `storage=`, close it yourself after all users of that object are
done.

## When to stop and escalate

Stop and involve the device/access-control owner when:

- authentication fails repeatedly;
- a write's outcome is unknown and cannot be verified;
- blocking state is missing or inconsistent;
- a timezone or group change could affect a group of people;
- the device reports a protocol response the SDK does not understand;
- the device clock or access behaviour differs from the expected model.

Guessing is more dangerous than pausing.

## Next

- [Troubleshooting](../help/troubleshooting.md)
- [Production checklist](production-checklist.md)
- [Errors reference](../reference/errors.md)
