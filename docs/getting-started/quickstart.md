# Quickstart

## Why this matters

This page takes you from “the package is installed” to a working read-only
script, an offline mirror, and an optional write test. It is deliberately
ordered from safest to riskiest so you can stop at any point without changing
the device.

## Before you begin

- Complete [Installation](installation.md).
- Know the device IP, port, and communication key.
- Confirm the TCP port is reachable with the steps in
  [First connection](first-connection.md).
- Use a non-production device for the write section, or get explicit approval.
- Keep the device's existing user data backed up.

## Step 1: Read the device

Create `quickstart.py`:

```python
from essl_f22 import Device

HOST = "192.168.1.50"
PORT = 4370
COMM_KEY = 0

with Device(HOST, PORT, comm_key=COMM_KEY, timeout=10.0) as device:
    info = device.get_device_info()
    sizes = device.get_free_sizes()

    print(f"{info.device_name} ({info.platform})")
    print(f"serial={info.serial_number} firmware={info.firmware_version}")
    print(f"users={sizes.users}/{sizes.users_capacity}")
    print(f"fingerprints={sizes.fingerprints}/{sizes.fingerprints_capacity}")
    print(f"attendance={sizes.attendance}/{sizes.attendance_capacity}")
```

Run it:

```bash
python quickstart.py
```

If this works, the network, key, and basic protocol are sound.

## Step 2: Read users and attendance

```python
from essl_f22 import Device

with Device("192.168.1.50", comm_key=0) as device:
    for user in device.list_users()[:5]:
        print(
            "uid=",
            user.uid,
            "user_id=",
            user.user_id,
            "name=",
            user.name,
            "group=",
            user.group_id,
        )

    records = device.list_attendance()
    print("attendance records:", len(records))
    for record in records[:5]:
        print(record.timestamp, record.uid, record.user_id)
```

!!! warning "Attendance can be large"
    `list_attendance()` reads the entire device log into memory. A device with
    tens of thousands of records can produce a large list and a slow read.
    Start with a small test device or use the mirror after the first successful
    sync.

The SDK does not promise chronological order from the device. Do not treat
`records[0]` as the newest record. Sort by `timestamp` when order matters.

## Step 3: Create a read-only mirror

The mirror stores a copy of device data in SQLite, including full user records
and their device password fields. Use an explicit path for a demo so you can
find and delete it later:

```python
from essl_f22 import Device

with Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="sqlite",
    storage_path="demo-mirror.db",
) as device:
    result = device.sync("full")
    mirror = device.mirror()

    print("synced at:", result.synced_at)
    print("users:", result.users)
    print("groups:", result.groups)
    print("timezones:", result.timezones)
    print("fingerprint metadata:", result.fingerprints)
    print("attendance:", result.attendance)

    print("first user:", mirror.list_users()[:1])
    print("recent sample:", mirror.list_attendance(limit=5))
```

What happened:

1. `sync("full")` read device info, users, groups, timezones, fingerprint
   metadata, and attendance.
2. It replaced the mirrored collections and attendance in `demo-mirror.db`.
3. `mirror()` opened a read-only view of that snapshot.
4. Fingerprint **templates** were read from the device to produce metadata, but
   only `uid`, `fid`, `flag`, and `size` were stored.

The mirror is read-only. It is not a restore mechanism. See
[Mirror and storage](../concepts/mirror-and-storage.md).

## Step 4: Optional write test

!!! danger "Read this before running"
    This creates and deletes a real user on a real device. Run it only on a
    non-production device with a UID you know is free. `delete_user()` is
    destructive. The example checks that the UID is free first, but you must
    still verify the device and the UID yourself.

```python
from essl_f22 import Device, User, UserNotFoundError

TEST_UID = 65000

with Device("192.168.1.50", comm_key=0) as device:
    try:
        existing = device.get_user(TEST_UID)
    except UserNotFoundError:
        existing = None

    if existing is not None:
        raise RuntimeError(f"UID {TEST_UID} is already in use; choose another")

    test_user = User(
        uid=TEST_UID,
        user_id="sdk-demo-65000",
        name="SDK Demo User",
        group_id=1,
    )

    try:
        device.set_user(test_user)
        written = device.get_user(TEST_UID)
        print("created:", written.uid, written.user_id, written.name)
    finally:
        device.delete_user(TEST_UID)
        print("deleted test user", TEST_UID)
```

What to check:

- `set_user()` sends the full 72-byte record. The fields you did not set were
  sent with their dataclass defaults.
- `set_user()` does not read the record back to compare every field. It requires
  an acknowledgement and refreshes device data. If you need proof, call
  `get_user()` afterward.
- `delete_user()` removes the user. Associated attendance history may remain,
  depending on firmware behaviour. Test that separately before relying on it.
- If the `finally` block cannot delete the test user, the user remains on the
  device. Investigate before running the script again.

## Step 5: Update a user without erasing fields

Do not construct a replacement `User` from memory. Read the existing record,
change only the field you intend to change, and write the whole record back:

```python
from essl_f22 import Device

with Device("192.168.1.50", comm_key=0) as device:
    user = device.get_user(65000)
    user.name = "SDK Demo User (updated)"
    device.set_user(user)

    confirmed = device.get_user(65000)
    print(confirmed.name)
```

This pattern preserves `card`, `password`, `privilege`, group, and timezone
fields that you did not touch.

## Step 6: Optional block test

Blocking is non-destructive, but it changes access immediately:

```python
from essl_f22 import Device

with Device(
    "192.168.1.50",
    comm_key=0,
    storage_path="demo-state.db",
) as device:
    result = device.block_user(65000)
    print("blocked:", result.uid, "slot:", result.block_timezone_slot)

    restored = device.unblock_user(65000)
    print("restored:", restored.restored, "state found:", restored.state_found)
```

Before using this on a real person:

- read [Access control and blocking](../concepts/access-control.md);
- back up the state database;
- verify that the device's timezone scheme matches your assumptions;
- test with a dedicated test user.

## Step 7: Handle expected failures

```python
from essl_f22 import (
    Device,
    DeviceAuthenticationError,
    DeviceConnectionError,
    DeviceTimeoutError,
    ESSL22Error,
)

try:
    with Device("192.168.1.50", comm_key=0, timeout=5.0) as device:
        print(device.get_device_info())
except DeviceAuthenticationError:
    print("The communication key was rejected. Ask the administrator.")
except DeviceTimeoutError:
    print("The device did not answer in time. Check network and address.")
except DeviceConnectionError as exc:
    print("Could not connect:", exc)
except ESSL22Error as exc:
    print("SDK error:", type(exc).__name__, exc)
```

Catch specific errors first. A broad `except Exception` hides programming
mistakes and makes device problems harder to diagnose.

## Clean up the demo

The demo created two files:

- `demo-mirror.db` — the SQLite mirror;
- `demo-state.db` — block state, only if you ran the block example.

Remove them only after you no longer need the data. They may contain names and
attendance records, so treat them as sensitive.

## What you have proved

- The SDK can connect to the device.
- The communication key is accepted.
- Reads decode into typed Python objects.
- The mirror can persist a snapshot.
- If you ran the write example, a user can be created, read back, and deleted.

## Next steps

- Understand the records: [Users](../concepts/users.md) and
  [Attendance](../concepts/attendance.md).
- Build a real backup: [Back up and sync](../guides/back-up-and-sync.md).
- Prepare for production: [Production checklist](../guides/production-checklist.md).
