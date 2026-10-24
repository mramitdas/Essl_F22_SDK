# Essl F22 SDK

**A synchronous Python SDK for eSSL/ZKTeco F22 attendance and access terminals.**

[![CI](https://github.com/mramitdas/Essl_F22_SDK/actions/workflows/ci.yml/badge.svg)](https://github.com/mramitdas/Essl_F22_SDK/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://github.com/mramitdas/Essl_F22_SDK)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

The Essl F22 SDK talks directly to an F22-compatible attendance and access
terminal over TCP. It reads the records that already exist on the device,
supports selected writes, and keeps a read-only offline mirror in a local file
or an external database.

It is a Python library, not a command-line application or a replacement for the
vendor's device software. Fingerprint enrollment and matching still happen on
the device.

## What you can do

- Read device information, serial number, firmware version, and capacity.
- Read users, attendance records, fingerprint metadata and templates, groups,
  timezones, and per-user access assignments.
- Create, update, and delete users.
- Write groups, timezones, and user-timezone assignments.
- Block and unblock a user by changing their access schedule without deleting
  the user or their fingerprint templates.
- Sync the device into a read-only mirror backed by SQLite, JSON, memory,
  PostgreSQL, MySQL, MongoDB, or Redis.
- Use the SDK on Python 3.12 or newer with no required runtime dependencies
  beyond the standard library.

## Requirements

- Python 3.12 or newer.
- Network access to the device on TCP port `4370`, or the port configured on
  the device.
- The device communication key, if one is configured.
- An F22-compatible terminal. Compatibility varies by firmware and OEM build;
  validate a new device before relying on writes.

Optional storage drivers are installed only when needed. The core package and
the default test suite do not import them.

## Installation

```bash
pip install Essl_F22_SDK
```

With uv:

```bash
uv add Essl_F22_SDK
```

Optional extras:

```bash
pip install "Essl_F22_SDK[postgres]"
pip install "Essl_F22_SDK[mysql]"
pip install "Essl_F22_SDK[mongo]"
pip install "Essl_F22_SDK[redis]"
pip install "Essl_F22_SDK[docs]"
```

The same extras work with uv:

```bash
uv add "Essl_F22_SDK[postgres]"
```

`pipx` and `uvx` are application runners. They do not make a library importable
in another project. For a one-off run with `uvx`:

```bash
uvx --from Essl_F22_SDK python -c "from essl_f22 import Device; print(Device)"
```

The distribution name is `Essl_F22_SDK`. Some package tools display the
normalized spelling `essl-f22-sdk`; that is the same package. The import name is
`essl_f22`.

## Quick start

```python
from essl_f22 import Device

with Device("192.168.1.27", comm_key=0) as device:
    info = device.get_device_info()
    print(info.device_name, info.serial_number, info.firmware_version)

    sizes = device.get_free_sizes()
    print("users:", sizes.users, "attendance:", sizes.attendance)

    for user in device.list_users()[:5]:
        print(user.uid, user.user_id, user.name)
```

`Device(...)` does not open the connection by itself. The `with` block calls
`connect()` on entry and `close()` on exit. The default port is `4370`; the
default communication key is `0`. A key of `0` is a default, not a guarantee
that the device accepts it.

Manual lifecycle:

```python
from essl_f22 import Device

device = Device("192.168.1.27", comm_key=0)
try:
    device.connect()
    print(device.get_serial_number())
finally:
    device.close()
```

Do not share one `Device` across threads without external locking. The session
keeps mutable request and receive-buffer state.

## How it works

| Concept | SDK representation | Notes |
| --- | --- | --- |
| Device | `Device` | TCP client and high-level API. |
| User | `User` | A 72-byte device record keyed by `uid`. |
| Attendance | `AttendanceRecord` | A 40-byte punch record. |
| Fingerprint | `FingerprintTemplate` | Raw template bytes plus `uid`, `fid`, and `flag`. |
| Access schedule | `TimeZone`, `GroupInfo`, `UserTimeZone` | Timezone slots and assignments. |
| Mirror | `Mirror` | Read-only local copy scoped by device serial. |
| Block state | `BlockStateStore` | Saved original assignment needed for unblocking. |

The device serial scopes both the mirror and block state. If the hardware
changes, create a new `Device` instance.

## Common tasks

### Read device information

```python
from essl_f22 import Device

with Device("192.168.1.27", comm_key=0) as device:
    info = device.get_device_info()
    print("platform:", info.platform)
    print("name:", info.device_name)
    print("serial:", info.serial_number)
    print("firmware:", info.firmware_version)
```

`get_serial_number()` caches the serial on the `Device` instance.

### Read users

```python
users = device.list_users()
user = device.get_user(295)
same_user = device.get_user_by_user_id("1001")
```

`list_users()` reads the full user buffer. Device order is not guaranteed.
`get_user()` and `get_user_by_user_id()` scan that list and raise
`UserNotFoundError` when no match exists.

### Create, update, and delete users

`set_user()` creates or replaces the user with the same `uid`. It sends the full
72-byte record, so read an existing user first and change only the fields you
intend to write.

```python
from essl_f22 import Device, User

with Device("192.168.1.27", comm_key=0) as device:
    user = device.get_user(295)
    user.name = "Updated Name"
    device.set_user(user)

    test_user = User(uid=296, user_id="sdk-296", name="SDK Test User")
    device.set_user(test_user)
    device.delete_user(test_user.uid)
```

- Create and delete have been exercised on hardware.
- Updating an existing user is implemented but has not been hardware-validated;
  test it on a non-production device first.
- `delete_user()` is destructive and cannot be undone by the SDK.

### Read attendance

```python
from essl_f22 import Device

with Device("192.168.1.27", comm_key=0) as device:
    records = device.list_attendance()
    for record in records[:10]:
        print(
            record.uid,
            record.user_id,
            record.timestamp,
            record.status,
            record.punch,
        )
```

The SDK reads the full attendance buffer. There is no device-side date filter or
pagination. Filter in Python after the read, or use the mirror for repeated
queries.

### Read fingerprints

```python
from essl_f22 import Device

with Device("192.168.1.27", comm_key=0) as device:
    templates = device.get_user_fingerprints(295)
    for item in templates:
        print(item.uid, item.fid, item.flag, item.size)
```

`list_fingerprints()` returns raw template bytes. Treat them like passwords or
identity documents. Do not log them, commit them, or copy them into a mirror.
The built-in mirror stores only fingerprint metadata.

There is no public enrollment or template-write API.

### Work with groups and timezones

```python
from essl_f22 import Device

with Device("192.168.1.27", comm_key=0) as device:
    groups = device.list_groups()
    timezones = device.list_timezones()
    assignment = device.get_user_timezone(295)

    print("groups:", [(group.group_id, group.tz1) for group in groups])
    print("timezone slots:", sorted(timezones))
    print("personal:", assignment.use_personal, assignment.tz1)
```

`list_groups()` and `list_timezones()` scan their configured ranges and skip the
device's not-found response. `set_group()`, `set_timezone()`, and
`set_user_timezone()` are real device writes.

### Block and unblock

Blocking assigns a deny-all timezone. It does not delete the user or their
fingerprint templates. The original assignment is saved in the state store and
restored by `unblock_user()`.

```python
from essl_f22 import Device

with Device(
    "192.168.1.27",
    comm_key=0,
    storage_backend="sqlite",
    storage_path="access-state.db",
) as device:
    blocked = device.block_user(295)
    print(blocked.already_blocked, blocked.block_timezone_slot)
    print("blocked:", device.is_user_blocked(295))

    restored = device.unblock_user(295)
    print(restored.state_found, restored.restored)
```

Use an explicit, durable state path. If the state store is lost, the SDK cannot
restore the exact original schedule automatically. Blocking and unblocking are
unit-tested with fake transports but have not been validated against a physical
door or production access policy.

### Mirror and sync

```python
from essl_f22 import Device

with Device(
    "192.168.1.27",
    comm_key=0,
    storage_backend="sqlite",
    storage_path="mirror.db",
) as device:
    result = device.sync("full")
    mirror = device.mirror()

    print(result.mode, result.users, result.attendance)
    print(mirror.get_user(295))
    print(mirror.list_attendance(uid=295, limit=10))
```

| Mode | Behaviour |
| --- | --- |
| `full` | Replaces every mirrored collection and attendance record. |
| `incremental` | Replaces non-attendance collections, inserts new attendance keys, and replaces attendance if the device count dropped. |

The mirror is read-only. It cannot restore users, attendance, or templates to a
device. It stores full user records, including the device password field, so
protect it like a credential store. Fingerprint template bytes are not copied.

Storage is created lazily on the first blocking or mirror operation. Without an
explicit path, SQLite and JSON use platform-specific default paths available as
`default_state_path()` and `default_mirror_path()`.

## Storage backends

| Backend | Extra | Connection value |
| --- | --- | --- |
| `sqlite` | none | `storage_path` (default `state.db`) |
| `json` | none | `storage_path` (default `mirror.json`) |
| `memory` | none | none |
| `postgres` | `postgres` | `storage_options={"dsn": ...}` |
| `mysql` | `mysql` | `storage_options={"dsn": ...}` |
| `mongo` | `mongo` | `storage_options={"uri": ...}` |
| `redis` | `redis` | `storage_options={"url": ...}` |

`storage_path` can also carry the DSN, URI, or URL. `storage_options` takes
precedence when both are supplied.

```python
from essl_f22 import Device

device = Device(
    "192.168.1.27",
    comm_key=0,
    storage_backend="postgres",
    storage_options={"dsn": "postgresql://user:pass@db/app"},
)
```

An injected `storage=` object wins over backend selection. A `Device` closes
only storage it created; injected storage remains owned by the caller.

```python
from essl_f22 import MemoryStorage, Device

storage = MemoryStorage()
device = Device("192.168.1.27", comm_key=0, storage=storage)
```

`create_storage()` is available when you need a backend without a `Device`:

```python
from essl_f22 import create_storage

storage = create_storage("sqlite", path="data/essl.db")
```

Close storage you create yourself.

## Error handling

All SDK-defined exceptions inherit from `ESSL22Error`.

```python
from essl_f22 import Device, ESSL22Error, UserNotFoundError

with Device("192.168.1.27", comm_key=0) as device:
    try:
        user = device.get_user(295)
    except UserNotFoundError:
        print("no such user")
    except ESSL22Error as exc:
        print(type(exc).__name__, exc)
```

Catch specific errors when the recovery action differs. `CommandError` carries
the device status code. `DeviceTimeoutError` is ambiguous for writes: the device
may have applied the command before the response was lost, so read the current
state before retrying.

See the [error reference](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/errors.md)
for the full hierarchy.

## Safety and limits

> **Writes are real.** `set_user()`, `delete_user()`, `set_timezone()`,
> `set_group()`, `set_user_timezone()`, and `set_time()` change the live
> device. Test on a non-production device first and keep a copy of the data you
> are about to change.

> **Blocking depends on local state.** `block_user()` changes the user's access
> schedule. `unblock_user()` restores the saved schedule only while the state
> store still contains it. Back up the state store before relying on it.

> **The mirror is not a restore button.** It is a read-only copy for reporting
> and comparison. It cannot write data back to the device.

The SDK does not enroll fingerprints, match fingerprints in Python, manage
firmware or network settings, provide a GUI or CLI, or encrypt the TCP
connection. Use a trusted network or a protected tunnel.

## Compatibility

The package declares Python `>=3.12` and advertises Python 3.12, 3.13, and 3.14.
CI runs the quality gates and package build on Python 3.14.

The project has been exercised against an F22-class terminal reporting platform
`ZLM60_TFT` and firmware in the 6.60 line. Create/read/delete of a test user,
attendance reads, group and timezone reads, and mirror sync have been validated.
Updating an existing user and block/unblock against a production access policy
have not.

The hardware test is read-only and opt-in:

```bash
ESSL_F22_HOST=192.168.1.27 \
ESSL_F22_PORT=4370 \
ESSL_F22_COMM_KEY=0 \
uv run pytest -m hardware
```

It is skipped when `ESSL_F22_HOST` is unset. Read the
[compatibility guide](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/compatibility.md)
before deploying against a new firmware or OEM build.

## Documentation

The full handbook starts at
[docs/index.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/index.md).
It covers:

- installation and first connection;
- the device record model and access control;
- user management, blocking, mirroring, and storage;
- exact API, model, error, and protocol references;
- troubleshooting, compatibility, and release work.

The handbook is built with MkDocs Material:

```bash
uv sync --extra docs
uv run mkdocs serve
```

Validate it with:

```bash
uv run mkdocs build --strict
```

## Development

```bash
uv sync
```

Run the quality gates before opening a pull request:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest
uv run pre-commit run --all-files
```

Build and check the package:

```bash
uv build
uvx twine check dist/*
```

### Tests

The default suite does not require a physical device:

```bash
uv run pytest
```

External storage contract tests are opt-in:

```bash
ESSL_F22_POSTGRES_DSN=postgresql://user:pass@db/app \
ESSL_F22_MYSQL_DSN=mysql://user:pass@db/app \
ESSL_F22_MONGO_URI=mongodb://localhost/app \
ESSL_F22_REDIS_URL=redis://localhost/0 \
uv run pytest tests/test_storage_contract.py
```

Do not commit test credentials or `.env` files.

## Project layout

```text
src/essl_f22/
  access.py       # non-destructive block/unblock manager
  device.py       # high-level device read/write API
  mirror.py       # read-only offline mirror and sync
  models.py       # dataclasses for device records
  protocol.py     # command constants and binary codecs
  session.py      # request/response session
  storage/        # document storage, built-ins, and external adapters
  transport.py    # TCP socket transport
docs/             # MkDocs handbook
tests/            # unit tests and opt-in hardware/storage tests
```

## Versioning

The project is pre-1.0. Treat the public API as usable but still subject to
change. Pin the version in your lock file, read `CHANGELOG.md`, and test upgrades
on a non-production device.

## License

The Essl F22 SDK is distributed under the terms of the Apache License 2.0. See
`LICENSE` for details.
