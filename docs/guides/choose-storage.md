# Choose storage

## Why this matters

The storage backend decides how durable, shareable, and fast your mirror and
block state are. Choosing the wrong one is rarely a correctness bug at first;
it shows up later as a lost state file, a corrupted JSON snapshot, a Redis
eviction, or a database permission failure during an incident.

This guide helps you choose deliberately.

## Start with two questions

### 1. Is this for a test or for real data?

- **Test or demo:** use `memory`. It is fast, isolated, and disappears when the
  process exits. That is a feature for tests and a disaster for production.
- **Real data:** use a durable backend.

### 2. Will more than one process or host use it?

- **One process, one host:** SQLite is usually the best default.
- **Several workers or hosts:** use a shared database such as PostgreSQL,
  MySQL, or MongoDB. Redis is possible but needs a durability review.

## Decision table

| Situation | Recommended backend | Why |
| --- | --- | --- |
| Unit tests, fake device | `memory` | No files, no cleanup, no cross-test leakage. |
| One script on one machine | `sqlite` | Durable, built in, no server, good enough for most single-host jobs. |
| Small human-inspectable snapshot | `json` | Easy to open and diff; not for large or concurrent writes. |
| Shared production reporting | `postgres` | Durable, concurrent, familiar operational model. |
| Existing MySQL estate | `mysql` | Works with the existing database operations. |
| Document-oriented estate | `mongo` | Natural fit if you already run MongoDB. |
| Ephemeral shared cache | `redis` | Fast, but verify persistence and eviction before trusting it. |

## Local backends

### SQLite (`sqlite`)

```python
from essl_f22 import Device

with Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="sqlite",
    storage_path="data/essl.db",
) as device:
    device.sync("full")
```

Use it when:

- one host owns the data;
- you want a single durable file;
- you do not want to run a database server;
- your concurrency is modest.

Watch out for:

- file permissions and disk space;
- backups while writers are active;
- sharing the file over a network filesystem (avoid this unless you know the
  filesystem and SQLite locking behaviour);
- using the same file for mirror and block state when they have different
  retention needs.

SQLite is the default backend. The default file is `state.db` inside the
platform application data directory. Use an explicit path for production.

### JSON (`json`)

```python
with Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="json",
    storage_path="data/mirror.json",
) as device:
    device.sync("full")
```

Use it when:

- the snapshot is small;
- you want to inspect or diff the file by hand;
- one process writes it at a time.

Watch out for:

- the whole file is loaded into memory and rewritten on each change;
- there is no multi-writer coordination;
- large attendance logs make the file large and the rewrite expensive;
- a malformed or unsupported file raises `StateStoreError`.

JSON is a good debugging format, not a high-volume production store.

### Memory (`memory`)

```python
with Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="memory",
) as device:
    device.sync("full")
    print(device.mirror().attendance_count())
```

Use it for tests and short-lived demos. All data is lost when the process ends.
It is not shared between processes.

## External backends

All external backends require an extra and a connection value. The SDK imports
the driver lazily, so a missing driver produces `StorageConfigurationError`
with an installation hint at backend creation time, not at import time.

### PostgreSQL (`postgres` / `postgresql`)

```bash
python -m pip install "Essl_F22_SDK[postgres]"
```

```python
with Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="postgres",
    storage_options={
        "dsn": "postgresql://essl_app:secret@db.example:5432/essl_f22",
    },
) as device:
    device.sync("full")
```

Use it when you need durable shared storage and normal database operations.

### MySQL (`mysql`)

```bash
python -m pip install "Essl_F22_SDK[mysql]"
```

```python
with Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="mysql",
    storage_options={
        "dsn": "mysql://essl_app:secret@db.example:3306/essl_f22",
    },
) as device:
    device.sync("full")
```

The DSN must include a database name. The backend accepts `mysql://` and
`mysql+pymysql://` schemes.

### MongoDB (`mongo` / `mongodb`)

```bash
python -m pip install "Essl_F22_SDK[mongo]"
```

```python
with Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="mongo",
    storage_options={
        "uri": "mongodb://db.example:27017/essl_f22",
    },
) as device:
    device.sync("full")
```

The URI must include a database. The SDK uses a `documents` collection.

### Redis (`redis`)

```bash
python -m pip install "Essl_F22_SDK[redis]"
```

```python
with Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="redis",
    storage_options={
        "url": "redis://:secret@redis.example:6379/0",
    },
) as device:
    device.sync("full")
```

Use Redis only after confirming:

- persistence is enabled if the data must survive a restart;
- the eviction policy will not silently discard keys;
- the Redis instance is access-controlled and not public;
- the database index is the one you intend to use.

Redis is excellent for fast shared state. It is not automatically durable just
because it is a server.

## Connection-value rules

The constructor accepts three storage inputs:

```python
Device(
    host,
    storage=existing_storage,  # highest precedence
    storage_backend="postgres",
    storage_path="postgresql://...",  # lower precedence
    storage_options={"dsn": "..."},  # middle precedence
)
```

Precedence, highest first:

1. `storage=`
2. `storage_options`
3. `storage_path`

For external backends, `storage_options` uses:

| Backend | Key |
| --- | --- |
| PostgreSQL | `dsn` |
| MySQL | `dsn` |
| MongoDB | `uri` |
| Redis | `url` |

A path can carry the same value for convenience, but options make the intent
clearer.

## Do not share a table with another application

The external adapters use a generic `documents` table/collection. Give
`essl_f22` its own database or schema. If another application uses a
`documents` table in the same database, you can create confusing conflicts or
grant rights you did not intend.

For Redis, keys are prefixed with `essl_f22:documents:`. Confirm the target
database index and avoid sharing it with unrelated workloads if eviction is
possible.

## Security checklist

- [ ] Credentials come from a secret store or environment, not source code.
- [ ] The database user has only the permissions the SDK needs.
- [ ] TLS is enabled if the database crosses an untrusted network.
- [ ] The database is not exposed to the public internet.
- [ ] Backups are encrypted and access-controlled.
- [ ] Retention is defined for attendance and biometric-adjacent metadata.
- [ ] Connection strings are not printed in logs.
- [ ] The storage host has enough disk for the attendance log and backups.

## Capacity planning

Attendance dominates storage growth. Estimate:

```text
records per day = people × punches per person per day
annual records  = records per day × operating days
```

Add indexes, backups, and reporting copies. Fingerprint metadata is small;
template bytes are not stored by the mirror.

SQLite and JSON are single-host formats. If you need multiple readers and
writers, choose a shared database before the data grows, not after.

## Testing external backends

The repository's storage contract tests are opt-in through environment values:

```bash
ESSL_F22_POSTGRES_DSN=postgresql://user:pass@db/app \
ESSL_F22_MYSQL_DSN=mysql://user:pass@db/app \
ESSL_F22_MONGO_URI=mongodb://localhost/app \
ESSL_F22_REDIS_URL=redis://localhost/0 \
uv run pytest tests/test_storage_contract.py
```

These variables are for the test suite. The runtime SDK does not read them
automatically; pass the connection value explicitly to `Device` or
`create_storage()`.

## Migration

There is no migration command. To move a mirror:

1. sync the device into the new backend;
2. verify counts and sample records;
3. switch readers to the new backend;
4. keep the old backend read-only until the retention period ends;
5. decommission the old backend deliberately.

Do not copy the internal `documents` rows between different backend products
unless you have verified the document format and version.

## Next

- [Storage reference](../reference/storage.md)
- [Back up and sync](back-up-and-sync.md)
- [Production checklist](production-checklist.md)
