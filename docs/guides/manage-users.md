# Manage users

## Why this matters

User changes are real changes to who can enter a building. A script that looks
correct can still overwrite a card number, move someone to the wrong group, or
delete a record that cannot be restored. This guide uses a controlled sequence:
inspect, plan, dry-run, write, verify, and record.

## The safe sequence

```text
inspect -> back up -> plan -> dry-run -> write -> verify -> record
```

Do not skip the dry-run on a production device.

## Step 1: Inspect the current state

```python
from essl_f22 import Device

with Device("192.168.1.50", comm_key=0) as device:
    info = device.get_device_info()
    sizes = device.get_free_sizes()
    users = device.list_users()

    print(info.serial_number, info.firmware_version)
    print("users:", sizes.users, "capacity:", sizes.users_capacity)
    print("first five:")
    for user in users[:5]:
        print(user.uid, user.user_id, user.name, user.group_id)
```

Record the serial number. It identifies the device you are about to change.

## Step 2: Back up the records you will touch

A mirror is a read-only copy, not a restore mechanism, but it is still useful
for comparison and for reconstructing a record by hand if something goes wrong.

```python
with Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="sqlite",
    storage_path="backup-before-user-change.db",
) as device:
    result = device.sync("full")
    print("snapshot:", result.users, "users,", result.attendance, "attendance")
    print("synced at:", result.synced_at)
```

Also export the exact records you plan to change to a separate file, because the
mirror will be overwritten by later syncs. A simple JSON export:

```python
import json
from dataclasses import asdict

from essl_f22 import Device

UIDS = [295, 296]

with Device("192.168.1.50", comm_key=0) as device:
    records = [asdict(device.get_user(uid)) for uid in UIDS]

with open("users-before-change.json", "w", encoding="utf-8") as handle:
    json.dump(records, handle, indent=2, default=str)
```

`asdict()` recursively converts the dataclass. The `default=str` handles any
non-JSON value, but check the output before treating it as a backup.

## Step 3: Build a change plan

Write down, before coding:

- the device serial;
- the UID of every user to change;
- the exact fields to change;
- the expected old value and new value;
- who approved the change;
- how you will verify it;
- how you will reverse it.

Example plan:

| UID | Field | Old | New | Reason | Reversible? |
| --- | --- | --- | --- | --- | --- |
| 295 | `name` | `Asha R.` | `Asha Rao` | Correct spelling | Yes, old value recorded |
| 65000 | whole record | absent | test user | Integration test | Yes, delete after test |

If you cannot state the old value, you are not ready to write.

## Step 4: Dry-run

A dry-run reads and prints what would change, without writing:

```python
from essl_f22 import Device

PLANNED_NAMES = {
    295: "Asha Rao",
    296: "Ravi Kumar",
}

with Device("192.168.1.50", comm_key=0) as device:
    for uid, new_name in PLANNED_NAMES.items():
        current = device.get_user(uid)
        print(
            f"uid={uid} user_id={current.user_id!r} "
            f"name={current.name!r} -> {new_name!r}"
        )
```

Check:

- the UID maps to the person you expect;
- the user ID matches your source system;
- the old name is what you expect;
- no one has already made the change;
- the new name fits the 23-byte field.

## Step 5: Apply one change at a time

```python
from essl_f22 import Device

UID = 295
NEW_NAME = "Asha Rao"

with Device("192.168.1.50", comm_key=0) as device:
    user = device.get_user(UID)

    if user.name == NEW_NAME:
        print("already applied")
    else:
        user.name = NEW_NAME
        device.set_user(user)

        confirmed = device.get_user(UID)
        if confirmed.name != NEW_NAME:
            raise RuntimeError(
                f"verification failed: expected {NEW_NAME!r}, got {confirmed.name!r}"
            )
        print("updated:", confirmed.uid, confirmed.user_id, confirmed.name)
```

This preserves every field you did not change because `set_user()` sends the
full record read from the device.

!!! warning "Hardware validation gap"
    Create, read, and delete have been exercised on hardware. Updating an
    existing user has not yet been hardware-validated. Run the dry-run and the
    update against a dedicated test user on a non-production device first.

## Step 6: Create a new user

```python
from essl_f22 import Device, User, UserNotFoundError

NEW_UID = 65000

with Device("192.168.1.50", comm_key=0) as device:
    try:
        device.get_user(NEW_UID)
    except UserNotFoundError:
        pass
    else:
        raise RuntimeError(f"UID {NEW_UID} is already in use")

    user = User(
        uid=NEW_UID,
        user_id="sdk-65000",
        name="SDK Test User",
        group_id=1,
    )
    device.set_user(user)

    created = device.get_user(NEW_UID)
    print("created:", created.uid, created.user_id, created.name, created.group_id)
```

Decide `group_id`, privileges, card, password, and schedule from a reviewed
source, not from guesses.

## Step 7: Delete a user

!!! danger "Destructive"
    `delete_user()` cannot be undone by the SDK. Confirm the UID, back up the
    record, and understand how the firmware treats attendance and fingerprint
    templates before deleting.

```python
from essl_f22 import Device

with Device("192.168.1.50", comm_key=0) as device:
    user = device.get_user(65000)
    print("about to delete:", user.uid, user.user_id, user.name)
    device.delete_user(65000)

    try:
        device.get_user(65000)
    except Exception:
        print("confirmed: user is gone")
    else:
        raise RuntimeError("delete was acknowledged but the user is still present")
```

Catching `Exception` here is acceptable only for a confirmation check. Do not
use that pattern around the delete itself; handle the specific SDK errors.

## Step 8: Batch changes safely

There is no batch-write API. For a batch:

1. Read all target records.
2. Validate every record before writing any.
3. Write one record at a time.
4. Verify each write immediately.
5. Log UID, old value, new value, and result.
6. Stop on the first unexpected result.
7. Keep a resume file so you do not repeat completed writes.

Do not write a loop that swallows exceptions and continues. A partial batch is
harder to reason about than a stopped batch.

## Step 9: Verify beyond the API

After the change:

- read the record back with `get_user()`;
- refresh and re-read if the device UI seems stale;
- check the device display or vendor software for a sample;
- run a mirror sync and compare counts;
- test access with the person or a test user if the change affects access.

An acknowledgement is not a guarantee that the device's UI or access engine
has already applied the change in the way you expect.

## Rollback

There is no automatic rollback for user writes. To roll back:

- use the saved record and call `set_user()` with the old values;
- for a newly created user, delete it;
- for a deleted user, recreate it from the saved record, then re-enroll
  fingerprints separately if they were removed.

Because fingerprints are not in the mirror, a deleted user's biometric
enrollment may not be recoverable through the SDK. Plan for that before
deleting.

## Common mistakes

| Mistake | Consequence | Prevention |
| --- | --- | --- |
| Constructing a new `User` for an update | Omitted fields reset to defaults | Read, modify, write. |
| Using `user_id` as if it were `uid` | Wrong record or not found | Confirm both identifiers. |
| Ignoring encoded byte length | `ValueError` or failed write | Check 23/23/7-byte limits. |
| Deleting without a backup | Permanent loss | Mirror plus a record export. |
| Writing in a loop without verification | Partial, silent corruption | Verify each write. |
| Assuming delete removes attendance | Wrong retention decisions | Test firmware behaviour. |

## Next

- [Block and unblock](block-and-unblock.md)
- [Production checklist](production-checklist.md)
- [Users concept](../concepts/users.md)
