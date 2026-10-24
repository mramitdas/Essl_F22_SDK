# Block and unblock

## Why this matters

Blocking is the SDK's least destructive way to stop access: the user and their
fingerprints stay in place, but their schedule becomes deny-all. That is safer
than deleting a person, but it still changes access immediately and depends on a
local state store to restore the original schedule later.

This guide is a controlled procedure. Do not skip the preflight or the state
backup.

!!! warning "Not hardware-validated"
    Blocking and unblocking are covered by unit tests with fake transports, but
    they have not been validated against a physical access policy. Test the
    full block, door, unblock, and door sequence on a non-production device.

## What you need

- A device you can reach and a communication key.
- The user's UID, confirmed against the device.
- A dedicated state store path.
- Permission for the access change.
- A backup of the state store.
- A test user and a way to verify actual access.

## How blocking works, in one paragraph

The SDK writes a deny-all timezone into a free slot, saves the user's current
timezone assignment in its state store, and points the user at that deny-all
slot. On unblock, it writes the saved assignment back. If the state store is
lost, the exact original schedule cannot be restored automatically.

Full details: [Access control and blocking](../concepts/access-control.md).

## Step 1: Back up the state store

Use an explicit state path so you know exactly what to back up:

```python
from essl_f22 import Device

with Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="sqlite",
    storage_path="access-state.db",
) as device:
    print(device.get_serial_number())
```

Before any block:

- stop other processes that write the same state store;
- use your normal SQLite/database backup process;
- record the backup time and device serial;
- test that the backup can be opened.

The state store contains the only record of each user's original assignment.
Treat it as configuration, not a cache.

## Step 2: Confirm the user and current schedule

```python
from essl_f22 import Device

UID = 295

with Device(
    "192.168.1.50",
    comm_key=0,
    storage_path="access-state.db",
) as device:
    user = device.get_user(UID)
    current = device.get_user_timezone(UID)

    print("user:", user.uid, user.user_id, user.name)
    print("personal:", current.use_personal)
    print("tz1/tz2/tz3:", current.tz1, current.tz2, current.tz3)
```

Confirm the identity and record the current assignment somewhere outside this
database. If `use_personal` is already true, the person may have a legitimate
personal schedule. Do not overwrite it casually.

## Step 3: Preflight the timezone slots

The SDK needs a free default-allow-all slot. This read-only check mirrors the
manager's eligibility rules:

```python
from essl_f22 import Device

with Device(
    "192.168.1.50",
    comm_key=0,
    storage_path="access-state.db",
) as device:
    users = device.list_users()
    groups = device.list_groups()
    timezones = device.list_timezones()

    referenced = set()

    for group in groups:
        referenced.update(slot for slot in (group.tz1, group.tz2, group.tz3) if slot)

    for user in users:
        if user.timezone_flag:
            referenced.update(slot for slot in (user.tz1, user.tz2, user.tz3) if slot)

    eligible = sorted(
        timezone.slot
        for timezone in timezones.values()
        if timezone.slot not in referenced and timezone.is_default_allow_all()
    )

    print("referenced slots:", sorted(referenced))
    print("eligible slots:", eligible)
    print("next block slot would be:", max(eligible) if eligible else None)
```

If the eligible list is empty, stop. `block_user()` will raise
`NoFreeTimeZoneSlotError` before changing the user, but there is no point
starting the process.

This preflight is a snapshot. Another process could change slots between the
check and the write. Do not run concurrent schedule changes.

## Step 4: Block the user

```python
from essl_f22 import Device

UID = 295

with Device(
    "192.168.1.50",
    comm_key=0,
    storage_path="access-state.db",
) as device:
    before = device.get_user_timezone(UID)
    result = device.block_user(UID)

    print("uid:", result.uid)
    print("user_id:", result.user_id)
    print("already blocked:", result.already_blocked)
    print("block slot:", result.block_timezone_slot)
    print("original:", result.original)

    after = device.get_user_timezone(UID)
    print("after:", after)

    if not device.is_user_blocked(UID):
        raise RuntimeError("block did not verify as active")
```

What to check:

- `result.uid` is the person you intended;
- `result.user_id` matches;
- `result.block_timezone_slot` is a deny-all slot;
- `after.use_personal` is true and `after.tz1` is the block slot;
- `after.tz2` and `after.tz3` are `0`;
- `is_user_blocked(UID)` is true.

Then test actual access at the door. The API verifies the assignment, not the
physical access engine.

## Step 5: Confirm the state record

```python
with Device(
    "192.168.1.50",
    comm_key=0,
    storage_path="access-state.db",
) as device:
    blocked = device.get_blocked_users()
    print("blocked UIDs in state:", blocked)
    print("this user:", device.is_user_blocked(295))
```

`get_blocked_users()` reads the state store, not the device. It is useful for
your own reconciliation, not as proof that the device has no other blocked
users.

## Step 6: Unblock

```python
from essl_f22 import Device

with Device(
    "192.168.1.50",
    comm_key=0,
    storage_path="access-state.db",
) as device:
    result = device.unblock_user(295)

    print("restored:", result.restored)
    print("state was found:", result.state_found)

    current = device.get_user_timezone(295)
    print("current:", current)
```

Check:

- `result.state_found` is `True` when the original assignment was available;
- `result.restored` matches the saved assignment;
- the read-back assignment matches;
- `is_user_blocked(295)` is false;
- actual access works again.

If `state_found` is `False`, the SDK did not have the original. It disabled
personal scheduling instead. That may not be the person's real original
schedule. Investigate before declaring success.

## Idempotence

Calling `block_user()` twice is safe for the same slot:

```python
first = device.block_user(295)
second = device.block_user(295)
print(first.already_blocked)  # False
print(second.already_blocked)  # True
```

Calling `unblock_user()` on a user who was never blocked is **not** a no-op. It
writes a non-personal assignment and reports `state_found=False`. Do not use it
as a harmless reset.

## Failure recovery

| Failure | What it means | Action |
| --- | --- | --- |
| `NoFreeTimeZoneSlotError` | No eligible default-allow-all slot | Free a slot or choose a different access-control method. |
| `DeviceVerificationError` after block | Read-back did not match; SDK attempted to restore the original | Check the user's current assignment; do not assume block is active. |
| `DeviceVerificationError` after unblock | Read-back did not match | Re-read the assignment; retry only after understanding the state. |
| `DeviceTimeoutError` during block | Outcome is ambiguous | Reconnect and read the user's assignment before retrying. |
| State store lost | Original assignment unavailable | Restore from backup or reconstruct from records; do not blind-unblock. |
| Device replaced | Serial changed; old state does not apply | Reconcile schedules on the new device intentionally. |
| Someone changed the schedule on the device | State and device disagree | Treat the device as authoritative; update state deliberately. |

### Ambiguous writes

A timeout can happen after the device received the command but before the SDK
read the acknowledgement. Do not immediately resend a write. Reconnect, read the
current assignment, and decide based on what the device actually shows.

### State loss

If the state store is lost:

1. Do not run `unblock_user()` blindly.
2. Read each user's current assignment.
3. Determine whether they are blocked.
4. Restore the intended schedule from your records or backup.
5. Rebuild a new state record only through the supported block/unblock flow.

The SDK cannot reconstruct the original from the device after the state is
gone.

## Multi-user procedures

Blocking several people:

```python
UIDS = [295, 296, 297]

with Device("192.168.1.50", comm_key=0, storage_path="access-state.db") as device:
    for uid in UIDS:
        result = device.block_user(uid)
        print(uid, result.already_blocked, result.block_timezone_slot)
```

The first block allocates a slot; later blocks reuse the same saved deny-all
slot when possible. Verify each result. Stop on the first unexpected error.

## Audit record

For each change, record:

- timestamp;
- operator;
- device serial;
- UID and user ID;
- action (block/unblock);
- block slot;
- original assignment;
- result and verification;
- approval reference.

The SDK does not write an audit log for you.

## Emergency access restoration

If someone must regain access immediately and the state is intact:

```python
device.unblock_user(uid)
```

If the state is not intact, do not guess. Read the current assignment, then set
the correct schedule with `set_user_timezone()` and verify. If you do not know
the correct schedule, involve the access-control owner. Restoring access
incorrectly can be worse than a short delay.

## Next

- [Production checklist](production-checklist.md)
- [Access control concept](../concepts/access-control.md)
- [Handle errors](handle-errors.md)
