# Mirror and storage

## Why this matters

Reading a device every time you need a report is slow, fragile, and sometimes
impossible. A mirror gives you a local, queryable copy. But a copy is only
useful if you know exactly what it contains, when it was refreshed, and what it
cannot do.

The most dangerous misunderstanding is thinking the mirror is a backup/restore
system. It is not. It is a read-only offline snapshot.

## The direction of data

```text
device  --->  sync  --->  storage backend  --->  Mirror queries
```

There is no supported reverse path. The SDK cannot restore users, attendance,
schedules, or fingerprint templates from the mirror to a device.

## What the mirror stores

For each device serial, the mirror stores:

| Collection | Contents |
| --- | --- |
| Device info | Platform, device name, serial number, firmware version. |
| Users | Full `User` records, including the device user password field. |
| Groups | `GroupInfo` records. |
| Timezones | `TimeZone` records keyed by slot. |
| Fingerprints | Metadata only: `uid`, `fid`, `flag`, `size`. |
| Attendance | Full `AttendanceRecord` records. |
| Sync state | Last sync time, mode, and collection counts. |

What it does **not** store:

- fingerprint template bytes;
- the device communication key or administrator credentials;
- a copy of the device firmware;
- a restore log or write-back plan;
- proof that the device still matches the snapshot.

!!! warning "User passwords are stored"
    The mirror persists full `User` records, including the device user
    `password` field. Protect the mirror like any other credential store, and
    do not assume it is safe to share or export.

## Per-device scope

A mirror is scoped to one device serial number. `Device.mirror()` uses the
serial of the connected device. If you construct a `Mirror` yourself and then
try to sync a different device, `SyncError` is raised.

This prevents two devices with similar data from overwriting each other in the
same storage namespace.

## Sync modes

### Full sync

```python
result = device.sync("full")
```

A full sync:

- replaces device info;
- replaces users;
- replaces groups;
- replaces timezones;
- replaces fingerprint metadata;
- replaces attendance.

It is the simplest way to get a clean snapshot. It is also the most expensive,
because it reads and writes everything.

### Incremental sync

```python
result = device.sync("incremental")
```

An incremental sync:

- replaces device info, users, groups, timezones, and fingerprint metadata;
- computes a stable key for every attendance record;
- inserts attendance records whose key is not already present;
- leaves existing attendance records in place;
- if the device's attendance count is lower than the mirror count, replaces
  attendance instead.

The last rule handles a device whose log was cleared or reset. Without it, the
mirror would keep stale records forever.

Incremental sync is not a delta protocol. The SDK still reads the full
attendance log from the device. The “incremental” part is how the storage layer
merges it.

## The stable attendance key

The key is a SHA-256 hash of the canonical attendance document:

```text
uid + user_id + timestamp + status + punch
```

Two records with identical values collapse to one key. Since the key is
content-addressed, an existing key already represents the same record; the
storage layer does not need to rewrite it.

This gives you duplicate suppression across repeated reads. It also means the
mirror is not a legal-grade event log if two distinct events could be
byte-for-byte identical in all five fields. Understand that trade-off before
using it for payroll or compliance.

## What `SyncResult` tells you

```python
result = device.sync("full")

print(result.device_serial)
print(result.mode)
print(result.synced_at)  # local time when the sync finished
print(result.users)
print(result.groups)
print(result.timezones)
print(result.fingerprints)
print(result.attendance)  # count after the sync
print(result.new_attendance)  # new records in this run
print(result.attendance_replaced)
```

| Field | Meaning |
| --- | --- |
| `synced_at` | Local `datetime.now()` when the sync finished, not device time. |
| `users` | Number of users read from the device. |
| `groups` | Number of groups read. |
| `timezones` | Number of timezone slots returned. |
| `fingerprints` | Number of fingerprint metadata entries read. |
| `attendance` | Attendance count in storage after the sync. |
| `new_attendance` | New records inserted in this run, or the full count when attendance was replaced. |
| `attendance_replaced` | Whether attendance was replaced rather than merged. |

`new_attendance` is not “punches since the last sync” in a temporal sense. It
is a storage-level count of newly inserted keys. If the device has a record
whose key already exists, it is not new.

## Is sync atomic?

No, not across collections. The SDK writes device info, users, groups,
timezones, fingerprint metadata, and attendance as separate storage operations.
If the process or database fails midway, the mirror can contain a partial
update.

For most backends, each individual collection replacement is atomic, but the
whole snapshot is not. Design your reporting to tolerate a partial sync, or
sync into a fresh database and swap it at the application level.

Do not run two syncs for the same device serial concurrently against the same
storage. The writes can interleave.

## The `Mirror` object

```python
with Device(
    "192.168.1.50",
    comm_key=0,
    storage_path="mirror.db",
) as device:
    result = device.sync("incremental")
    mirror = device.mirror()

    print(mirror.device_serial)
    print(mirror.get_device_info())
    print(mirror.list_users()[:3])
    print(mirror.get_user(295))
    print(mirror.get_user_by_user_id("1001"))
    print(mirror.list_fingerprints()[:3])
    print(mirror.list_attendance(uid=295, limit=10))
    print(mirror.attendance_count())
    print(mirror.list_groups())
    print(mirror.list_timezones())
    print(mirror.get_sync_state())
```

`Mirror` is read-only. Its methods query storage; they do not contact the
device.

Important error behaviour:

- `Mirror.get_user()` raises `UserNotFoundError` if the user is absent.
- `Mirror.get_timezone()` and `Mirror.get_group()` raise
  `MirrorRecordNotFoundError` if the record is absent.
- `Mirror.sync()` raises `SyncError` for an unsupported mode or a serial
  mismatch.

`Mirror.snapshot()` loads every collection, including all attendance, into a
single `MirrorSnapshot`. It is convenient for small datasets and dangerous for
large ones.

## Storage backends

| Backend | Name(s) | Extra | Connection value | Best for |
| --- | --- | --- | --- | --- |
| SQLite | `sqlite` | none | `storage_path` | Single-host mirror and block state. |
| JSON | `json` | none | `storage_path` | Small, inspectable snapshots. |
| Memory | `memory` | none | none | Tests and short-lived demos. |
| PostgreSQL | `postgres`, `postgresql` | `postgres` | `storage_options={"dsn": ...}` or path | Shared, durable storage. |
| MySQL | `mysql` | `mysql` | `storage_options={"dsn": ...}` or path | Shared, durable storage. |
| MongoDB | `mongo`, `mongodb` | `mongo` | `storage_options={"uri": ...}` or path | Document-oriented shared storage. |
| Redis | `redis` | `redis` | `storage_options={"url": ...}` or path | Fast, ephemeral/shared state. |

Backend names are case-insensitive.

## Choosing a path or connection value

```python
from essl_f22 import Device

device = Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="sqlite",
    storage_path="data/mirror.db",
)
```

For external backends:

```python
device = Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="postgres",
    storage_options={"dsn": "postgresql://user:pass@db/app"},
)
```

Rules:

1. `storage_options` takes precedence over `storage_path`.
2. `storage_path` can carry a DSN, URI, or URL for an external backend.
3. An injected `storage=` object takes precedence over both.
4. A `Device` closes only storage it created. Injected storage remains yours.

The connection value must be non-empty. A missing DSN/URI/URL raises
`StorageConfigurationError` when the backend is created.

## Default paths

The SQLite and JSON backends use platform-specific application data paths when
you do not provide one:

| Helper | Default |
| --- | --- |
| `default_data_dir()` | Platform application data directory for `essl_f22`. |
| `default_state_path()` | `state.db` inside that directory. |
| `default_mirror_path()` | `mirror.json` inside that directory. |

```python
from essl_f22 import default_data_dir, default_mirror_path, default_state_path

print(default_data_dir())
print(default_state_path())
print(default_mirror_path())
```

On macOS the base is under `~/Library/Application Support/essl_f22`; on Windows
it uses `LOCALAPPDATA`; on Linux it follows `XDG_DATA_HOME` or
`~/.local/share`.

The default SQLite backend is used for both block state and the mirror. That is
convenient, but it means deleting the state database also deletes the local
mirror. Use an explicit path when the two have different retention needs.

## Storage lifecycle

Storage is created lazily:

- `Device(...)` does not touch storage.
- The first `block_user()`, `unblock_user()`, `is_user_blocked()`,
  `get_blocked_users()`, `mirror()`, or `sync()` creates it.
- `Device.close()` closes it only if the device created it.

If you create a `StorageBackend` yourself:

```python
from essl_f22 import Device, SqliteStorage

storage = SqliteStorage("shared.db")
try:
    with Device("192.168.1.50", comm_key=0, storage=storage) as device:
        device.sync("full")
        print(device.mirror().attendance_count())
finally:
    storage.close()
```

Do not close injected storage while another device or reporting job is still
using it.

## Concurrency and durability

| Backend | Notes |
| --- | --- |
| Memory | Process-local; lost on exit; not shared between processes. |
| JSON | Loads the whole file at construction and rewrites it on each change. One writer per file is the safe assumption. |
| SQLite | Durable local file; each operation opens a connection. Suitable for one host, with normal SQLite concurrency limits. |
| PostgreSQL / MySQL | Shared database; the SDK creates a `documents` table; use normal database access controls and backups. |
| MongoDB | Shared database; the SDK uses a `documents` collection and a unique namespace/key index. |
| Redis | Shared service; data lives in hashes named `essl_f22:documents:<namespace>`. Confirm persistence and eviction policy before treating it as durable. |

For all backends, the mirror is a copy. Your database backup policy, access
control, encryption, and retention rules still apply.

## What the mirror is good for

- fast read-only reports;
- comparing two snapshots;
- searching attendance without repeatedly reading the device;
- keeping a local copy when the device is offline;
- metadata audits without holding template bytes.

## What the mirror is not good for

- restoring a device;
- biometric disaster recovery;
- proving that the device still matches the copy;
- legal-grade audit without additional controls;
- real-time access decisions;
- replacing a device-vendor backup process.

## Next

- [Choose storage](../guides/choose-storage.md)
- [Back up and sync](../guides/back-up-and-sync.md)
- [Storage reference](../reference/storage.md)
