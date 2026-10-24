# Attendance

## Why this matters

Attendance is usually the reason the device exists. It is also the largest and
most sensitive dataset on the terminal. A careless read can exhaust memory, a
careless interpretation can put punches in the wrong order or timezone, and a
careless export can leak a workplace's entire movement history.

This page explains what an attendance record contains, how the SDK reads it,
and what it does not promise.

## What an attendance record is

Each punch becomes a fixed 40-byte record. The SDK exposes a frozen
`AttendanceRecord`:

```python
from essl_f22 import AttendanceRecord

record = AttendanceRecord(
    uid=295,
    user_id="1001",
    timestamp=...,  # a naive datetime
    status=1,
    punch=0,
)
```

| Field | Type | Meaning |
| --- | --- | --- |
| `uid` | `int` | Internal user slot at punch time. |
| `user_id` | `str` | Device-visible user ID at punch time. |
| `timestamp` | `datetime` | Device local wall-clock time, with no timezone attached. |
| `status` | `int` | Device status code. The SDK does not interpret it. |
| `punch` | `int` | Device punch/verify value. The SDK does not interpret it. |

The SDK deliberately does not map `status` and `punch` to labels such as
“check-in” or “check-out”. Those meanings are firmware- and configuration-
dependent. If you need them, document them for your device fleet and validate
against the device display or vendor software.

## Reading attendance

```python
from essl_f22 import Device

with Device("192.168.1.50", comm_key=0) as device:
    sizes = device.get_free_sizes()
    print("device says:", sizes.attendance, "records")

    records = device.list_attendance()
    print("decoded:", len(records))

    for record in records[:5]:
        print(record.timestamp, record.uid, record.user_id, record.status, record.punch)
```

How the read works:

1. The SDK asks the device for free-size information.
2. If the attendance count is zero, it returns an empty list without reading.
3. Otherwise it requests the attendance buffer and reads it in chunks.
4. It uses the device's record count to determine the record size and parse the
   records.
5. If the response does not fit the expected 40-byte record layout, it raises
   `ProtocolError`.

The entire log is read into memory. There is no pagination, cursor, or
server-side date filter in the public API.

## Why `list_attendance()` can be slow

The cost is driven by the number of records and the network:

- the device must produce the full buffer;
- the SDK reads it in chunks;
- the parser builds a Python object per record;
- the resulting list stays in memory until you release it.

A few thousand records are usually fine. Hundreds of thousands deserve a
planned ingestion job, a longer timeout, and memory monitoring. If you need
repeated filtered queries, sync a mirror once and query the mirror.

## Ordering and “latest”

Do not assume the device returns records in chronological order. The SDK does
not reorder device results before returning them. To find the latest record,
sort explicitly:

```python
records = device.list_attendance()
latest = max(records, key=lambda record: record.timestamp)
```

The mirror sorts attendance by timestamp and then by the stable record hash
when you query it. That is a mirror behavior, not a promise about the raw device
order.

## Time is naive and local

`AttendanceRecord.timestamp` is a naive `datetime`. It represents the device's
local wall-clock time. The SDK does not attach a timezone, convert to UTC, or
adjust for daylight saving.

Consequences:

- two devices in different timezones produce timestamps that look comparable
  but are not;
- changing the device clock changes future records;
- a device with a drifting clock produces drifting attendance;
- comparing with `since`/`until` uses naive datetimes in the same wall-clock
  frame.

If you need UTC in your warehouse, attach the device's timezone at ingestion
time and record the device serial. Do not guess the timezone from the host
machine.

## Filtering with the mirror

The device read has no filters. The mirror does:

```python
from datetime import datetime

with Device(
    "192.168.1.50",
    comm_key=0,
    storage_path="mirror.db",
) as device:
    device.sync("incremental")
    mirror = device.mirror()

    records = mirror.list_attendance(
        uid=295,
        since=datetime(2026, 10, 1),
        until=datetime(2026, 10, 31, 23, 59, 59),
        limit=100,
    )
    print(len(records))
```

The filters are applied by the storage layer. SQLite and JSON still load the
matching records into memory before filtering; the API shape is convenient, not
a streaming query engine.

## Duplicates and stable keys

The mirror computes a SHA-256 key from the canonical attendance document:
`uid`, `user_id`, `timestamp`, `status`, and `punch`. Two records with the same
values collapse to the same key during incremental sync.

This is useful for re-reading a device without duplicating identical punches.
It also means two genuinely distinct punches with identical values in every
field would be treated as one mirror record. In practice, the timestamp usually
distinguishes them, but do not use the mirror as a legal-grade audit log without
understanding this behavior.

## Attendance versus user records

Attendance stores the identifiers as they were at punch time:

- deleting a user does not necessarily delete that user's attendance;
- renaming a user does not rewrite old attendance names;
- changing a `user_id` does not rewrite old attendance identifiers.

Treat attendance as an event log, not as a live join to the current user table.

## Exporting attendance

A minimal CSV export:

```python
import csv

from essl_f22 import Device

with Device("192.168.1.50", comm_key=0) as device:
    records = device.list_attendance()

with open("attendance.csv", "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["timestamp", "uid", "user_id", "status", "punch"])
    for record in records:
        writer.writerow(
            [
                record.timestamp.isoformat(sep=" "),
                record.uid,
                record.user_id,
                record.status,
                record.punch,
            ]
        )
```

The CSV contains personal data. Store it with the same care as the device data:
restrict access, define a retention period, and avoid copying it into logs or
chat.

## Device clock management

```python
from datetime import datetime

from essl_f22 import Device

with Device("192.168.1.50", comm_key=0) as device:
    print("before:", device.get_time())
    # device.set_time(datetime.now())  # write: only with authorisation
    print("after: ", device.get_time())
```

`set_time()` changes the device clock. It is a write and can affect future
attendance ordering and access schedules. Use it only during a maintenance
window, with approval, and record the before/after values.

## Memory and performance planning

| Records | Practical approach |
| --- | --- |
| Up to a few thousand | `list_attendance()` or a full mirror sync is usually fine. |
| Tens of thousands | Increase timeout, run off-peak, monitor memory, prefer the mirror for queries. |
| Hundreds of thousands | Use a dedicated ingestion process, external storage, and a tested retention policy. |

There is no streaming API in the public interface. If you need one, you will
have to work with the lower-level session/buffer APIs and test carefully; see
[Protocol internals](../reference/protocol.md).

## Privacy and retention

Attendance reveals where a person was and when. Treat it as personal data:

- collect only what you need;
- restrict access to exports and mirrors;
- encrypt storage at rest where appropriate;
- define deletion and retention rules;
- avoid sending attendance to third-party services without a lawful basis;
- do not put raw attendance in application logs.

The SDK does not implement retention, consent, or access-review policy. That is
your system's responsibility.

## Next

- [Fingerprints](fingerprints.md)
- [Mirror and storage](mirror-and-storage.md)
- [Back up and sync](../guides/back-up-and-sync.md)
- [Models reference](../reference/models.md#attendancerecord)
