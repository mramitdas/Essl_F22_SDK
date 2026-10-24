# essl_f22

**Synchronous Python SDK for eSSL/ZKTeco F22 terminals.**

[![CI](https://github.com/mramitdas/essl-f22-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/mramitdas/essl-f22-sdk/actions/workflows/ci.yml)

Read users, fingerprint templates, attendance, groups, and timezones over TCP;
block and unblock users without deleting them; and keep a read-only offline
mirror in SQLite, JSON, memory, PostgreSQL, MySQL, MongoDB, or Redis.

## Install

```bash
uv sync
```

Optional storage drivers and documentation tooling are extras:

```bash
uv sync --extra postgres
uv sync --extra mysql
uv sync --extra mongo
uv sync --extra redis
uv sync --extra docs
```

Optional drivers are imported lazily. The core package imports and the default
test suite work without installing any of them.

## Quickstart

```python
from essl_f22 import Device

with Device("192.168.1.27", comm_key=0) as device:
    info = device.get_device_info()
    print(info.serial_number, info.firmware_version)

    for user in device.list_users()[:5]:
        print(user.uid, user.user_id)
```

The device port defaults to `4370` and the communication key defaults to `0`.
Pass `port=`, `comm_key=`, `timeout=`, or `encoding=` when needed.

## Offline mirror

The mirror is read-only and stored separately from the device. Fingerprint
template bytes are never copied; only fingerprint metadata is stored.

```python
from essl_f22 import Device

with Device(
    "192.168.1.27",
    comm_key=0,
    storage_backend="sqlite",
) as device:
    result = device.sync("full")
    mirror = device.mirror()

    print(result.users, result.attendance)
    print(mirror.get_user(295))
    print(mirror.list_attendance(uid=295, limit=10))
```

`sync("full")` replaces every mirrored collection and attendance record.
`sync("incremental")` upserts attendance by a stable record hash and falls back
to a full attendance replacement when the device count drops. Users, groups,
timezones, device info, and fingerprint metadata are replaced on every sync.

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

## Blocking

Blocking reassigns the user to a deny-all access timezone. It does not delete
the user or any fingerprint template. The original timezone assignment is saved
and restored by `unblock_user()`.

```python
blocked = device.block_user(13)
print(blocked.block_timezone_slot)

restored = device.unblock_user(13)
print(restored.restored)
```

Blocking is idempotent. The manager reuses an existing deny-all slot when one
is available, otherwise uses the highest free default-allow-all slot. If no
slot is free, `NoFreeTimeZoneSlotError` is raised.

## Tests

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src/ tests/
uv run pre-commit run --all-files
```

External storage integration tests are skipped unless their connection values
are set:

```bash
ESSL_F22_POSTGRES_DSN=postgresql://user:pass@db/app \
ESSL_F22_MYSQL_DSN=mysql://user:pass@db/app \
ESSL_F22_MONGO_URI=mongodb://localhost/app \
ESSL_F22_REDIS_URL=redis://localhost/0 \
uv run pytest tests/test_storage_contract.py
```

The hardware test is opt-in and read-only: it syncs a device into memory and
checks counts, a user, and fingerprint metadata. It never calls block/unblock
or writes to the device.

```bash
ESSL_F22_HOST=192.168.1.27 \
ESSL_F22_PORT=4370 \
ESSL_F22_COMM_KEY=0 \
uv run pytest -m hardware
```

Without `ESSL_F22_HOST`, the hardware test is skipped.

## Project layout

```
src/essl_f22/
  access.py       # non-destructive block/unblock manager
  device.py       # high-level device API
  mirror.py       # read-only offline mirror and sync
  models.py       # dataclasses for device records
  protocol.py     # command constants and binary codecs
  session.py      # request/response session
  storage/        # document storage, built-ins, and external adapters
  transport.py    # TCP socket transport
tests/
  test_hardware.py  # opt-in read-only device validation
```

## License

essl_f22 is distributed under the terms of the Apache License 2.0. See
`LICENSE` for details.
