# essl_f22

Synchronous Python SDK for eSSL/ZKTeco F22 terminals. The SDK reads and writes
device records over TCP, provides non-destructive user blocking, and maintains
a read-only offline mirror in a pluggable storage backend.

## Install

```bash
pip install essl_f22
```

Or with uv:

```bash
uv add essl_f22
```

Optional features:

```bash
pip install "essl_f22[postgres]"
pip install "essl_f22[mysql]"
pip install "essl_f22[mongo]"
pip install "essl_f22[redis]"
pip install "essl_f22[docs]"
```

This is a library, not a CLI. `pipx` and `uvx` are application runners; use
`pip` or `uv` to add `essl_f22` to a project. For a one-off `uvx` run:

```bash
uvx --from essl_f22 python -c "from essl_f22 import Device; print(Device)"
```

Optional storage drivers are imported only when their backend is selected.

## Device usage

```python
from essl_f22 import Device

with Device("192.168.1.27", comm_key=0) as device:
    info = device.get_device_info()
    print(info.serial_number, info.firmware_version)

    users = device.list_users()
    fingerprints = device.list_fingerprints()
    attendance = device.list_attendance()
    groups = device.list_groups()
    timezones = device.list_timezones()
```

The default port is `4370`; the default communication key is `0`. The
constructor also accepts `timeout`, `encoding`, transport/session overrides,
storage settings, and timezone/group scan limits.

## User management

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

`set_user()` creates or updates by `uid` and sends the full 72-byte user record.
Read the user first and preserve fields you do not intend to change.
`delete_user()` removes the user and is destructive. Both calls refresh the
device after a successful acknowledgement.

## Offline mirror

```python
from essl_f22 import Device

with Device(
    "192.168.1.27",
    comm_key=0,
    storage_backend="sqlite",
) as device:
    result = device.sync("full")
    mirror = device.mirror()

    print(result.users, result.groups, result.attendance)
    print(mirror.get_user(295))
    print(mirror.list_attendance(uid=295, limit=10))
    print(mirror.get_sync_state())
```

Sync modes:

- `full` replaces all mirrored collections and attendance.
- `incremental` upserts attendance by a stable record hash. If the device
  attendance count drops below the mirror count, attendance is replaced
  instead. Other collections are replaced on every sync.

The mirror never stores fingerprint template bytes, only metadata (`uid`,
`fid`, `flag`, `size`). It is read-only; writes require a connected `Device`.

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

```python
from essl_f22 import Device

device = Device(
    "192.168.1.27",
    comm_key=0,
    storage_backend="postgres",
    storage_options={"dsn": "postgresql://user:pass@db/app"},
)
```

`storage_options` takes precedence over `storage_path`. An injected `storage=`
object takes precedence over both. A `Device` closes only storage it created.

Default paths are available as `default_state_path()`, `default_mirror_path()`,
and `default_data_dir()`.

## Blocking

```python
blocked = device.block_user(13)
print(blocked.block_timezone_slot)

restored = device.unblock_user(13)
print(restored.restored)
```

Blocking assigns a deny-all access timezone and saves the original assignment.
It never deletes users or fingerprint templates. The manager reuses an existing
deny-all slot or allocates the highest free default-allow-all slot. If no slot
is free, `NoFreeTimeZoneSlotError` is raised. Blocking is idempotent.

## Development

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src/ tests/
uv run pre-commit run --all-files
```

Storage integration tests are skipped unless their environment values are set:

```bash
ESSL_F22_POSTGRES_DSN=postgresql://user:pass@db/app \
ESSL_F22_MYSQL_DSN=mysql://user:pass@db/app \
ESSL_F22_MONGO_URI=mongodb://localhost/app \
ESSL_F22_REDIS_URL=redis://localhost/0 \
uv run pytest tests/test_storage_contract.py
```

The hardware test is opt-in and read-only. It syncs into memory and validates
counts, a user, and fingerprint metadata without calling block/unblock or
writing to the device.

```bash
ESSL_F22_HOST=192.168.1.27 \
ESSL_F22_PORT=4370 \
ESSL_F22_COMM_KEY=0 \
uv run pytest -m hardware
```

The test is skipped when `ESSL_F22_HOST` is unset.

## License

Apache License 2.0. See `LICENSE`.
