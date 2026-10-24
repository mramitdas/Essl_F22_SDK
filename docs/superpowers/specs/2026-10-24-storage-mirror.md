# Pluggable Storage and Offline Mirror

**Date:** 2026-10-24

**Status:** Approved for implementation.

## Goal

Add a pluggable local storage layer that persists non-destructive block state
and a full read-only offline mirror of an eSSL/ZKTeco F22 terminal.

The mirror lets applications read device data without a live connection. It
does not write to the device.

## Requirements

- Mirror device info, users, groups, timezones, attendance, and fingerprint
  metadata.
- Never store fingerprint template blobs.
- Store user password/PIN fields as read from the device.
- Keep the offline API read-only; writes require a connected `Device`.
- Support full and incremental synchronization.
- Built-in backends: in-memory, JSON file, SQLite (default).
- External backends: PostgreSQL, MySQL, MongoDB, Redis.
- Use direct database drivers; no ORM or SQLAlchemy.
- External drivers are optional extras; the core remains stdlib-only.
- Support both injected storage objects and convenience backend selection.
- Keep the existing block/unblock state contract.
- One device may be mirrored in a shared storage backend alongside others;
  records are keyed by device serial.

## Architecture

New modules:

```text
src/essl_f22/storage/
  __init__.py      # public exports
  base.py          # BlockStateStore, MirrorStore, StorageBackend protocols
  codec.py         # model <-> JSON document codecs, attendance record hash
  document.py      # typed storage methods over namespace/key documents
  factory.py       # create_storage()
  jsonfile.py      # atomic JSON file backend
  memory.py        # process-local backend
  models.py        # storage-only dataclasses
  paths.py         # platform default paths
  sqlite.py        # default SQLite backend
src/essl_f22/state.py  # compatibility shim for block-state imports
```

External adapters add `postgres.py`, `mysql.py`, `mongo.py`, and `redis.py`
under `storage/`.

### Protocols

`BlockStateStore` persists each user's original timezone and the reserved
deny-all timezone slot.

`MirrorStore` stores device snapshots and incremental attendance updates.

`StorageBackend` composes both and adds `close()`.

### Document storage

All built-ins share a namespace/key JSON document primitive. This keeps
semantics identical across backends and makes future adapters small.

Namespaces are scoped by device serial where appropriate:

```text
device_info:<serial>
users:<serial>
groups:<serial>
timezones:<serial>
fingerprints:<serial>
attendance:<serial>
sync_state:<serial>
block_original_user_timezone:<serial>
block_timezone
```

Block timezone uses the device serial as the key in the shared namespace.

### Records

- Users are keyed by `uid`.
- Groups are keyed by `group_id`.
- Timezones are keyed by `slot`.
- Fingerprints are keyed by `uid:fid`.
- Attendance is keyed by a SHA-256 hash of its canonical fields.
- Sync state is keyed by device serial.

Attendance record hashing deliberately treats identical punches as the same
record. Incremental synchronization is therefore idempotent.

### Built-in backends

- `MemoryStorage`: deep-copied process-local documents.
- `JsonFileStorage`: one versioned JSON file, written with a temporary file
  and `os.replace` for atomic replacement.
- `SqliteStorage`: a `documents(namespace, key, payload)` table with
  transactional batch replace and upsert operations.

`create_storage(backend, path=None, options=None)` accepts `sqlite`, `json`,
and `memory`; SQLite is the default. Unknown backends raise
`StorageConfigurationError`.

Default paths use the platform application-data directory:

- macOS: `~/Library/Application Support/essl_f22`
- Windows: `%LOCALAPPDATA%\essl_f22`
- Linux/other: `$XDG_DATA_HOME/essl_f22` or `~/.local/share/essl_f22`

The default SQLite file is `state.db`; the default JSON file is
`mirror.json`.

### Synchronization

`Mirror.sync(device, mode="incremental")`:

1. Read device info, users, groups, timezones, fingerprints, and attendance.
2. Replace users, groups, timezones, fingerprint metadata, and device info.
3. For `full`, replace attendance.
4. For `incremental`:
   - If the device record count is lower than the stored count, replace
     attendance (handles deletions).
   - Otherwise, upsert attendance by record hash.
5. Save and return sync state/results.

The protocol has no validated attendance cursor, so incremental sync still
reads the full attendance buffer.

### Offline API

`Mirror` exposes read-only methods for device info, users, groups, timezones,
fingerprints, attendance filters, and sync state. Missing single records raise
typed storage errors; list methods return empty collections.

### Security

The mirror stores password/PIN fields by explicit product requirement. It
must not store fingerprint template blobs. Storage files and database
credentials are the caller's responsibility to protect.

## Out of scope

- Fingerprint template restoration or enrollment.
- Offline writes to the device.
- Cross-device synchronization.
- Query-specific schemas for analytics.
- Automatic background synchronization.
