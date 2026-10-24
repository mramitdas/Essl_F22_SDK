# Storage

## Why this matters

Storage holds two different kinds of data:

- the **mirror**: a read-only copy of device records;
- the **block state**: the only copy of each blocked user's original access
  assignment.

Losing the mirror hurts reporting. Losing block state can prevent a correct
unblock. They may share a SQLite file, but they do not have the same recovery
requirements.

For choosing a backend, start with [Choose storage](../guides/choose-storage.md).

## `create_storage`

```python
from essl_f22 import create_storage

storage = create_storage(
    backend="sqlite",
    path="data/essl.db",
)
```

Signature:

```text
create_storage(
    backend: str = "sqlite",
    *,
    path: Path | str | None = None,
    options: Mapping[str, Any] | None = None,
) -> StorageBackend
```

| Backend name | Aliases | Required value |
| --- | --- | --- |
| `sqlite` | none | `path` optional; default `default_state_path()` |
| `json` | none | `path` optional; default `default_mirror_path()` |
| `memory` | none | none |
| `postgres` | `postgresql` | `options["dsn"]` or `path` |
| `mysql` | none | `options["dsn"]` or `path` |
| `mongo` | `mongodb` | `options["uri"]` or `path` |
| `redis` | none | `options["url"]` or `path` |

Names are case-insensitive. An unknown name raises
`StorageConfigurationError`.

For external backends, `options` takes precedence over `path`:

```python
storage = create_storage(
    "postgres",
    path="postgresql://ignored",
    options={"dsn": "postgresql://used@db/app"},
)
```

## Backend classes

All of these are exported from `essl_f22`:

| Class | Constructor |
| --- | --- |
| `SqliteStorage` | `SqliteStorage(path)` |
| `JsonFileStorage` | `JsonFileStorage(path)` |
| `MemoryStorage` | `MemoryStorage()` |
| `PostgresStorage` | `PostgresStorage(dsn)` |
| `MysqlStorage` | `MysqlStorage(dsn)` |
| `MongoStorage` | `MongoStorage(uri)` |
| `RedisStorage` | `RedisStorage(url)` |

`SqliteStorage(":memory:")` is supported and creates a process-local SQLite
database.

## `StorageBackend` protocol

`StorageBackend` combines the block-state and mirror protocols and adds
`close()`.

```python
class StorageBackend(BlockStateStore, MirrorStore, Protocol):
    def close(self) -> None: ...
```

A custom object can be passed as `Device(..., storage=...)` if it implements the
methods the device actually calls. For blocking and mirroring, that means the
full protocol below.

### Block-state methods

| Method | Purpose |
| --- | --- |
| `get_original_user_timezone(serial, uid)` | Read the saved original assignment. |
| `save_original_user_timezone(serial, uid, timezone)` | Save it before blocking. |
| `delete_original_user_timezone(serial, uid)` | Remove it after unblocking. |
| `list_blocked_uids(serial)` | List UIDs with saved state. |
| `get_block_timezone(serial)` | Read the saved deny-all slot. |
| `save_block_timezone(serial, slot)` | Save the deny-all slot. |

### Mirror methods

| Method | Purpose |
| --- | --- |
| `save_device_info(serial, info)` | Store device info. |
| `get_device_info(serial)` | Read device info. |
| `replace_users(serial, users)` | Replace all users. |
| `list_users(serial)` | List users. |
| `get_user(serial, uid)` | Read one user or `None`. |
| `replace_groups(serial, groups)` | Replace all groups. |
| `list_groups(serial)` | List groups. |
| `get_group(serial, group_id)` | Read one group or `None`. |
| `replace_timezones(serial, timezones)` | Replace all timezone slots. |
| `list_timezones(serial)` | Return slots as a dict. |
| `get_timezone(serial, slot)` | Read one slot or `None`. |
| `replace_fingerprints(serial, fingerprints)` | Replace metadata only. |
| `list_fingerprints(serial)` | List metadata. |
| `upsert_attendance(serial, entries)` | Insert new attendance keys; return new count. |
| `replace_attendance(serial, entries)` | Replace all attendance. |
| `list_attendance(serial, *, uid, since, until, limit)` | Query attendance. |
| `attendance_count(serial)` | Count stored attendance. |
| `save_sync_state(serial, state)` | Store sync metadata. |
| `get_sync_state(serial)` | Read sync metadata. |
| `clear_device(serial)` | Remove a device's stored data. |

`clear_device()` removes a device's mirror data and is part of the
`MirrorStore` protocol. Treat it as a destructive maintenance operation and
test it before use.

## Backend details

### SQLite

- Durable local file; the default backend.
- Each operation opens a SQLite connection.
- Creates a `documents` table with `(namespace, key)` as the primary key.
- `:memory:` is process-local and disappears when the connection closes.
- Subject to normal SQLite locking and filesystem behaviour.

### JSON

- Loads the entire file at construction and rewrites it on each change.
- Stores a top-level object with `version` and `namespaces`.
- Unsupported format versions, invalid JSON, or invalid records raise
  `StateStoreError`.
- Not designed for multiple concurrent writers.
- Loads the whole snapshot into memory.

### Memory

- Process-local dictionaries.
- Lost on exit.
- `close()` does nothing.
- Use for tests and short-lived demos.

### PostgreSQL

- Requires `psycopg` from the `postgres` extra.
- Creates a `documents` table with `(namespace, key_name)` as the primary key.
- Accepts a psycopg-compatible DSN.
- Opens a new connection per operation.
- Missing driver or connection value raises `StorageConfigurationError`.

### MySQL

- Requires `pymysql` from the `mysql` extra.
- DSN must include a database name.
- Accepts `mysql://` and `mysql+pymysql://` schemes.
- Creates a `documents` table with `(namespace, key_name)` as the primary key.
- Uses `utf8mb4`.
- Opens a new connection per operation.

### MongoDB

- Requires `pymongo` from the `mongo` extra.
- URI must include a database.
- Uses a `documents` collection with a unique `(namespace, key_name)` index.
- Sets a 5-second server-selection timeout.
- Missing driver or invalid URI raises `StorageConfigurationError`.

### Redis

- Requires `redis` from the `redis` extra.
- Uses hashes named `essl_f22:documents:<namespace>`.
- Pings the server at construction.
- `close()` closes the client.
- Durability depends on the Redis configuration; verify persistence and
  eviction before using it for data you cannot lose.

## Default paths

```python
from essl_f22 import default_data_dir, default_mirror_path, default_state_path

print(default_data_dir())
print(default_state_path())
print(default_mirror_path())
```

| Function | Result |
| --- | --- |
| `default_data_dir()` | Platform application-data directory for `essl_f22`. |
| `default_state_path()` | `state.db` inside that directory. |
| `default_mirror_path()` | `mirror.json` inside that directory. |

Platform bases:

- Windows: `%LOCALAPPDATA%\essl_f22` (or `~/AppData/Local/essl_f22`);
- macOS: `~/Library/Application Support/essl_f22`;
- Linux: `$XDG_DATA_HOME/essl_f22` or `~/.local/share/essl_f22`.

## Storage ownership

- `Device` creates storage lazily if you do not inject it.
- `Device.close()` closes owned storage.
- Injected storage is not closed by `Device`.
- `create_storage()` returns an object you own; close it yourself.

```python
from essl_f22 import SqliteStorage

storage = SqliteStorage("shared.db")
try:
    ...
finally:
    storage.close()
```

## Document format

The built-in backends store JSON documents in namespaces keyed by device serial
and record identity. The JSON file also has a format version.

This is an implementation detail, not a stable public API. Do not write or
migrate `documents` rows by hand unless you have read the code and tested the
change. Use `Device.sync()` to populate a new backend instead of copying rows
between database products.

## What storage does not do

- It does not write data back to a device.
- It does not store fingerprint template bytes.
- It stores full user records, including device user password fields. Protect
  it as a credential store.
- It does not encrypt data for you. Use filesystem/database encryption and
  access controls.
- It does not provide retention or deletion policy.
- It does not make a sync atomic across collections.
- It does not add cross-process locking beyond the underlying backend.

## Environment variables

The SDK runtime does not read storage connection values from environment
variables automatically. Pass them explicitly.

The test suite reads:

```text
ESSL_F22_POSTGRES_DSN
ESSL_F22_MYSQL_DSN
ESSL_F22_MONGO_URI
ESSL_F22_REDIS_URL
```

for the opt-in storage contract tests.

## Errors

| Error | When |
| --- | --- |
| `StorageConfigurationError` | Unknown backend, missing driver, missing/invalid connection value. |
| `StateStoreError` | Local file, SQLite, JSON, or state operation failed. |
| `StorageError` | Base class for storage failures. |
| `MirrorRecordNotFoundError` | A mirror timezone/group record is absent. |
| `SyncError` | Unsupported mode or serial mismatch. |

See [Errors](errors.md).

## Next

- [Choose storage](../guides/choose-storage.md)
- [Mirror and storage](../concepts/mirror-and-storage.md)
- [Models](models.md#storage-models)
