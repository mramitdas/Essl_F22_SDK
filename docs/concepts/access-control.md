# Access control and blocking

## Why this matters

Access control decides who can open a door and when. The SDK can read and write
the device's schedules, and it offers a non-destructive way to block a person
temporarily. That is useful, but it is also the area where a wrong assumption
can lock out a whole group or silently remove a legitimate schedule.

This page explains the device model, then the exact blocking algorithm. Read it
before using `block_user()` on a real person.

!!! warning "Not hardware-validated"
    The blocking algorithm is tested with fake transports, but it has not been
    validated against a physical door or production access policy. Verify the
    full block, door, unblock, and door sequence on a non-production device.

## The device model

### Timezone slots

A device has a fixed number of **timezone slots**. The default scan limit in the
SDK is `50`, controlled by `max_timezone_slots`. Each slot contains seven day
intervals, one per weekday.

```python
from essl_f22 import DayInterval, TimeZone

slot = TimeZone(
    slot=10,
    days=(
        DayInterval(9, 0, 17, 0),
        DayInterval(9, 0, 17, 0),
        DayInterval(9, 0, 17, 0),
        DayInterval(9, 0, 17, 0),
        DayInterval(9, 0, 17, 0),
        DayInterval(0, 0, 0, 0),
        DayInterval(0, 0, 0, 0),
    ),
)
```

`DayInterval` has inclusive start and end minutes:

```python
DayInterval(9, 0, 17, 0).allows(datetime(2026, 10, 24, 9, 0))  # True
DayInterval(9, 0, 17, 0).allows(datetime(2026, 10, 24, 17, 0))  # True
DayInterval(9, 0, 17, 0).allows(datetime(2026, 10, 24, 17, 1))  # False
```

An interval where the start is greater than or equal to the end never allows
access. This is how a deny-all day is represented.

The SDK provides two helpers:

- `TimeZone.is_default_allow_all()` is true when every day is exactly
  `00:00–23:59`.
- `TimeZone.is_deny_all()` is true when every day has start greater than or
  equal to end.

### Groups

A group has three timezone slots and a few device-specific flags:

```python
from essl_f22 import GroupInfo

group = GroupInfo(
    group_id=1,
    tz1=1,
    tz2=0,
    tz3=0,
    verify_style=0,
    holiday_enabled=False,
)
```

| Field | Meaning |
| --- | --- |
| `group_id` | Group identifier, scanned from `1` to `max_groups` (default `100`). |
| `tz1`–`tz3` | Timezone slots used by the group. |
| `verify_style` | Device verification style. The SDK preserves it but does not interpret it. |
| `holiday_enabled` | Whether holiday behaviour is enabled. |

`list_groups()` asks the device for each ID in range and skips the device's
“not found” response (`0x1381`). It is a scan, not a single bulk read. If your
device has groups above `max_groups`, they will not appear unless you raise the
limit.

### User-timezone assignment

Separate from the `User` record's `tz1`–`tz3` fields, the device exposes a
per-user assignment:

```python
from essl_f22 import UserTimeZone

assignment = UserTimeZone(
    uid=295,
    use_personal=True,
    tz1=10,
    tz2=0,
    tz3=0,
)
```

```python
device.set_user_timezone(295, assignment)
current = device.get_user_timezone(295)
```

`UserTimeZone.canonical()` returns the assignment unchanged when
`use_personal=True`. When `use_personal=False`, it clears the timezone slots so
the group schedule applies.

## What blocking is

`block_user(uid)` does **not** delete the user. It:

1. assigns the user a personal access schedule pointing at a deny-all timezone;
2. saves the user's original assignment in the SDK state store;
3. verifies the new assignment by reading it back;
4. restores the original if verification fails.

The user record and fingerprint templates are untouched. The person still
exists on the device; they simply have a schedule that does not allow access.

## The exact blocking algorithm

For a user who is not already blocked:

```text
read device serial
read user (must exist)
read current user-timezone assignment  -> original
ensure a block slot:
    if state has a slot and device still has a deny-all slot there:
        reuse it
    else:
        scan users, groups, and timezones
        find slots not referenced by any group or personal schedule
        keep only default-allow-all slots
        choose the highest remaining slot
        write a deny-all timezone into that slot
        save the slot in state
save original in state
set user assignment: use_personal=True, tz1=block_slot, tz2=0, tz3=0
read the assignment back
if it does not match:
    restore original
    delete saved state for this user
    raise DeviceVerificationError
return BlockResult(...)
```

The slot scan is conservative: a slot referenced by any group's `tz1`–`tz3` or
by a user with `timezone_flag` set is not considered free. Only default
allow-all slots are eligible. The highest eligible slot is chosen.

If no eligible slot exists, `NoFreeTimeZoneSlotError` is raised before the user
is changed.

## The exact unblocking algorithm

```text
read device serial
read user (must exist)
read saved original assignment from state
target = original.canonical() if saved else UserTimeZone(uid, use_personal=False)
set user assignment to target
read it back
if it does not match:
    raise DeviceVerificationError
if saved state existed:
    delete saved state
return UnblockResult(..., state_found=...)
```

If `state_found` is `False`, the SDK did not have the original assignment. It
falls back to disabling personal scheduling (`use_personal=False`). That may
not match the person's original schedule, especially if they had a legitimate
personal schedule before anyone used this SDK.

## Example

```python
from essl_f22 import Device

with Device(
    "192.168.1.50",
    comm_key=0,
    storage_path="state.db",
) as device:
    blocked = device.block_user(295)
    print("blocked:", blocked.uid, "slot:", blocked.block_timezone_slot)
    print("was already blocked:", blocked.already_blocked)

    print("currently blocked:", device.is_user_blocked(295))
    print("blocked users in state:", device.get_blocked_users())

    restored = device.unblock_user(295)
    print("restored:", restored.restored)
    print("state was found:", restored.state_found)
```

## Idempotence

`block_user()` is idempotent for the same block slot. If the current assignment
already points at the saved block slot (with `tz2` and `tz3` zero), it returns:

```text
already_blocked=True
```

and does not rewrite the user. It still ensures the block slot exists.

`unblock_user()` is not symmetrical in the same way: it always writes a target
assignment. Calling it on a user who was never blocked by this SDK will disable
personal scheduling, with `state_found=False`.

## What `get_blocked_users()` really means

`get_blocked_users()` reads the SDK's **state store**, not the device. It lists
UIDs for which the state store has a saved original assignment for that device
serial.

It is not a device-wide scan. It can be incomplete or stale if:

- blocking was performed by another machine or another state store;
- the state database was deleted or restored from an old backup;
- someone changed the user's schedule directly on the device;
- the device was replaced and the serial changed.

`is_user_blocked(uid)` is more precise: it reads the current device assignment
and compares it with the saved block slot. It returns `False` if no block slot
is recorded in state.

## Limits and risks

### Slot availability

Blocking needs a free default-allow-all timezone slot. A device with a custom
schedule scheme, or one where every slot is referenced, may have none. The SDK
does not invent slots or overwrite referenced ones.

### Custom timezone semantics

The SDK assumes a deny-all slot is represented by intervals where start is
greater than or equal to end. It also assumes `00:00–23:59` is a default
allow-all slot. Validate both assumptions on your firmware before using
blocking in production.

### State-store loss

The state store is the only place the original assignment is saved. If it is
lost:

- `unblock_user()` cannot restore the exact original schedule;
- `get_blocked_users()` may return an empty list even though users are blocked;
- `is_user_blocked()` may return `False` even though the device still denies
  access.

Back up the state store. Treat it as part of your access-control configuration.

### Device replacement

State is scoped by device serial. A replacement device has a different serial,
so old state does not apply. Reconcile blocks intentionally after a hardware
swap. Do not assume the new device inherited the old schedules.

### Not a security boundary

Blocking is an access-schedule change, not a cryptographic lock. Someone with
device administrator access can change it. It does not delete the user, does
not delete templates, and may not prevent the device from recording events. It
is not a substitute for a formal access-review or incident-response process.

### Multi-device environments

Use one state store and one serial per physical device. If you share a database
between devices, the serial namespacing keeps records separate, but your
operational process must still track which block belongs to which device.

## Before blocking a real person

- [ ] I have written approval for the access change.
- [ ] I know the person's UID and have confirmed their identity.
- [ ] I backed up the state store.
- [ ] I know the device's timezone-slot scheme.
- [ ] I confirmed a free default-allow-all slot exists.
- [ ] I tested block and unblock on a non-production user.
- [ ] I know how to restore the person's original schedule if state is lost.
- [ ] I have a plan to verify the person's actual access at the door.

## Next

- [Block and unblock](../guides/block-and-unblock.md)
- [Mirror and storage](mirror-and-storage.md)
- [Models reference](../reference/models.md#timezone)
