# Back up and sync

## Why this matters

“Back up the device” can mean several different things:

- keep a read-only copy for reporting;
- preserve a snapshot before a risky change;
- recover from a hardware failure;
- meet a retention or audit requirement.

`essl_f22` supports the first two well. It supports the third only partly, and
it does not provide a device restore mechanism. Be precise about which problem
you are solving.

## What a sync gives you

A sync reads the device and writes a copy to a storage backend. The copy
contains users, groups, timezones, fingerprint metadata, attendance, device
info, and sync state.

The user records include the device `password` field. Treat the mirror as a
credential store and protect it accordingly.

It does **not** contain fingerprint template bytes or the device communication
key. It cannot write any of the copied data back to a device.

Use a sync for:

- reporting and offline search;
- comparing device state over time;
- preserving a record before a user or schedule change;
- reducing repeated full-device reads.

Do not use it as the only disaster-recovery mechanism for biometrics or access
configuration.

## Step 1: Choose a durable location

Use an explicit path so the data does not hide in a platform default directory:

```python
from essl_f22 import Device

with Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="sqlite",
    storage_path="/var/lib/essl-f22/mirror.db",
) as device:
    result = device.sync("full")
    print(result)
```

For a shared or production system, choose an external backend and a dedicated
database:

```python
with Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="postgres",
    storage_options={
        "dsn": "postgresql://essl_app:secret@db.example/essl_f22",
    },
) as device:
    result = device.sync("incremental")
```

Keep credentials out of source code. Load them from your deployment's secret
store or environment.

## Step 2: Pick a sync mode

| Mode | What it does | When to use |
| --- | --- | --- |
| `full` | Replaces every mirrored collection and attendance. | First sync, after a device reset, after a suspicious merge, or on a low-frequency schedule. |
| `incremental` | Replaces non-attendance collections; inserts new attendance keys; replaces attendance if the device count dropped. | Frequent scheduled syncs. |

Incremental still reads the entire device attendance log. The difference is in
how storage merges it.

A practical schedule:

- **Every 15–60 minutes:** incremental sync during operating hours.
- **Nightly or weekly:** full sync during a quiet window.
- **Before and after maintenance:** explicit full sync with a separate path.
- **After a device reset or log clear:** full sync, and expect
  `attendance_replaced=True` on the next incremental run.

Avoid syncing during a known peak read period if the device is slow. The read
is network- and memory-intensive.

## Step 3: Run and verify

```python
from essl_f22 import Device

with Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="sqlite",
    storage_path="mirror.db",
) as device:
    result = device.sync("full")
    mirror = device.mirror()

    print("mode:", result.mode)
    print("synced at:", result.synced_at)
    print("users:", result.users)
    print("attendance:", result.attendance)
    print("new attendance:", result.new_attendance)
    print("attendance replaced:", result.attendance_replaced)

    assert result.users == len(mirror.list_users())
    assert result.attendance == mirror.attendance_count()

    state = mirror.get_sync_state()
    print("state:", state)
```

What the assertions prove:

- the reported user count matches the stored user count;
- the reported attendance count matches the stored attendance count.

They do **not** prove that the device still has the same count. New punches can
arrive during or after the sync.

To compare with the device, read its free-size counts:

```python
with Device(
    "192.168.1.50",
    comm_key=0,
    storage_path="mirror.db",
) as device:
    result = device.sync("incremental")
    sizes = device.get_free_sizes()
    mirror = device.mirror()

    print("device says:", sizes.users, sizes.attendance)
    print("mirror says:", result.users, result.attendance)
```

If the device count is higher, new records may have arrived after the read. If
the device count is lower than the mirror count, investigate a reset or a
filtered device view before trusting the merge.

## Step 4: Watch for a count drop

Incremental sync replaces attendance when the device count is lower than the
mirror count. That protects you from keeping records the device no longer has,
but it can also discard history if the device was reset or pointed at a
different log.

Treat this as an alert-worthy event:

```python
result = device.sync("incremental")

if result.attendance_replaced:
    print("WARNING: attendance was replaced, not merged")
    print("new count:", result.attendance)
    print("new records:", result.new_attendance)
```

Before accepting a replacement:

- confirm the device was intentionally reset or cleared;
- check whether you need to archive the previous mirror;
- compare the old and new snapshots;
- record the reason.

## Step 5: Keep the previous snapshot

SQLite and JSON are single files. Before a full sync that may replace history:

```bash
cp mirror.db mirror-before-2026-10-24.db
```

Stop writers first, or use SQLite's backup mechanism, so you do not copy a
half-written file. For external databases, use the database's own snapshot
tooling.

Do not keep unlimited copies of attendance data. Define a retention period and
delete old snapshots securely.

## Step 6: Back up the state store too

The mirror and block state may share a SQLite file. If you use blocking, the
state store contains the original access assignments needed for unblocking.

If they share a file:

- back up the file before blocking changes;
- understand that deleting it also deletes the mirror;
- restore both together.

If they are separate, back up both. A mirror backup does not restore block
state, and a state backup does not restore attendance.

## Step 7: Export for reporting

The mirror supports filtered queries:

```python
from datetime import datetime

mirror = device.mirror()
records = mirror.list_attendance(
    since=datetime(2026, 10, 1),
    until=datetime(2026, 10, 31, 23, 59, 59),
    limit=5000,
)
print(len(records))
```

For a CSV export, see
[Attendance](../concepts/attendance.md#exporting-attendance). Remember that the
export is personal data and needs the same access controls as the database.

## Failure handling

| Failure | Meaning | Action |
| --- | --- | --- |
| `SyncError` with serial mismatch | The `Mirror` belongs to another device | Use the correct mirror or serial. |
| `StorageConfigurationError` | Missing driver or connection value | Install the extra and provide a DSN/URI/URL. |
| `StateStoreError` | Local file or database write failed | Check permissions, disk space, and database availability. |
| `DeviceTimeoutError` | Device read timed out | Increase timeout only after checking the network; retry off-peak. |
| Partial collection update | Sync is not atomic across collections | Re-run a full sync and verify counts before trusting reports. |
| `attendance_replaced=True` unexpectedly | Device count dropped | Archive the old mirror and investigate before accepting. |

Do not silently continue after a failed sync. A partial mirror can produce
confident but wrong reports.

## External database notes

When using PostgreSQL, MySQL, MongoDB, or Redis:

- use a dedicated database or schema for `essl_f22`;
- grant only the permissions the SDK needs;
- use TLS and strong credentials where supported;
- back up the database with its native tooling;
- monitor disk growth, especially attendance;
- confirm the database's durability and eviction settings (especially Redis);
- do not expose the database to the public internet.

The SDK creates a `documents` table/collection. Do not edit those rows by hand
unless you fully understand the document format.

## What to record for each sync

- device serial;
- start and end time;
- mode;
- operator or scheduler;
- result counts;
- whether attendance was replaced;
- any errors;
- storage location and backup path.

The `SyncState` stores some of this, but not the operator or failure reason.
Keep operational logs separately.

## Disaster recovery reality

A mirror can help you:

- rebuild reports;
- identify who was on the device;
- recreate user records manually;
- compare before and after a failure.

It cannot:

- restore fingerprint templates;
- restore device firmware or network settings;
- guarantee that a recreated user has the same biometric enrollment;
- replace a vendor-supported device backup.

If biometric disaster recovery matters, establish and test a separate process
with the device vendor or your access-control provider.

## Next

- [Choose storage](choose-storage.md)
- [Production checklist](production-checklist.md)
- [Mirror and storage](../concepts/mirror-and-storage.md)
