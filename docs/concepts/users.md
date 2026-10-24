# Users

## Why this matters

A user record controls who the device recognises and which access rules apply.
It is also the record most likely to be damaged by a well-meaning script,
because a write replaces the entire record rather than patching one field.

Understanding the difference between the internal UID and the visible user ID,
and knowing which fields are sent with defaults, is the difference between a
safe update and silently erasing someone's card or group assignment.

## What a user is

On the device, a user is a fixed **72-byte record**. The SDK represents it as a
mutable `User` dataclass:

```python
from essl_f22 import User

user = User(
    uid=295,
    user_id="1001",
    name="Asha Rao",
    group_id=1,
)
```

`User` is mutable, so the safe update pattern is:

```python
user = device.get_user(295)
user.name = "Asha Rao (updated)"
device.set_user(user)
```

The second example preserves every field you did not intentionally change.
Create, read, and delete have been exercised on hardware; the update path has
not yet been hardware-validated. Test it on a non-production device first.

## The fields

| Field | Type | Default | Meaning and practical notes |
| --- | --- | --- | --- |
| `uid` | `int` | required | Internal device slot. Must fit in 16 bits (`0`–`65535`). Write and delete address this value. |
| `user_id` | `str` | required | Device-visible identifier. Encoded into a 24-byte field, so at most 23 encoded bytes. |
| `name` | `str` | `""` | Display name. Encoded into a 24-byte field, so at most 23 encoded bytes. |
| `privilege` | `int` | `0` | Device privilege value. The SDK does not interpret it; preserve existing values unless you know the firmware's meaning. |
| `password` | `str` | `""` | Device password field. Encoded into an 8-byte field, so at most 7 encoded bytes. |
| `card` | `int` | `0` | Card number. Unsigned 32-bit field. |
| `group_id` | `int` | `1` | Group membership. Group definitions hold access schedules. |
| `timezone_flag` | `int` | `0` | Whether the user record carries a personal access schedule. |
| `tz1` | `int` | `0` | First personal timezone slot, when personal scheduling is active. |
| `tz2` | `int` | `0` | Second personal timezone slot. |
| `tz3` | `int` | `0` | Third personal timezone slot. |

The `timezone_flag` and `tz1`–`tz3` fields in `User` are part of the user
record. The device also exposes a separate **user timezone assignment** through
`get_user_timezone()` and `set_user_timezone()`. Blocking uses that separate
assignment. Do not assume changing `User.tz1` and changing the user-timezone
assignment are interchangeable; test the behaviour on your firmware.

## UID versus user ID

| Question | UID | User ID |
| --- | --- | --- |
| What is it? | Internal slot number | The identifier people and reports see |
| Is it stable? | Usually assigned when the record is created | Can be edited |
| How do I address it in the SDK? | `get_user(uid)`, `set_user(user)`, `delete_user(uid)` | `get_user_by_user_id(user_id)` |
| Does attendance carry it? | Yes, as `AttendanceRecord.uid` | Yes, as `AttendanceRecord.user_id` |
| Is it unique? | Should be unique per device | Intended to be unique, but the SDK does not enforce it |

`get_user_by_user_id()` is a convenience method. It calls `list_users()` and
filters in Python. It is not an indexed device lookup. If you need repeated
lookups by user ID, sync a mirror and build your own index, or cache the user
list for the duration of a short operation.

## Reading users

```python
from essl_f22 import Device, UserNotFoundError

with Device("192.168.1.50", comm_key=0) as device:
    users = device.list_users()
    print("count:", len(users))

    try:
        user = device.get_user(295)
        print(user.uid, user.user_id, user.name)
    except UserNotFoundError:
        print("no user with uid 295")

    try:
        user = device.get_user_by_user_id("1001")
        print("found by user id:", user.uid)
    except UserNotFoundError:
        print("no user with that user ID")
```

`list_users()` returns the device's user records in device order. The SDK does
not guarantee that the list is sorted. Sort explicitly if order matters.

## Creating a user

```python
from essl_f22 import Device, User

with Device("192.168.1.50", comm_key=0) as device:
    new_user = User(
        uid=65000,
        user_id="sdk-65000",
        name="SDK Test User",
        group_id=1,
    )
    device.set_user(new_user)

    confirmed = device.get_user(65000)
    print(confirmed.user_id, confirmed.name)
```

Before creating:

1. Confirm the UID is free. `set_user()` overwrites an existing user with the
   same UID.
2. Confirm the user ID does not collide with an existing person.
3. Decide the group and access schedule deliberately.
4. Use a test device for the first write.

## Updating a user

```python
from essl_f22 import Device

with Device("192.168.1.50", comm_key=0) as device:
    user = device.get_user(65000)
    user.name = "SDK Test User (updated)"
    device.set_user(user)

    print(device.get_user(65000).name)
```

This works because `set_user()` sends the full record, including the fields you
did not change.

Do **not** do this unless you mean it:

```python
# Dangerous: every omitted field is sent with its dataclass default.
device.set_user(User(uid=65000, user_id="sdk-65000"))
```

That can reset the name, card, password, group, and timezone fields. Even when
the defaults happen to be acceptable, they are not a substitute for reading the
current record.

## Field length limits

The device fields are fixed-width byte arrays. The SDK encodes strings using
the device's `encoding` (UTF-8 by default) and rejects values that do not fit.

| Field | Storage | Maximum encoded length |
| --- | --- | --- |
| `user_id` | 24 bytes | 23 bytes |
| `name` | 24 bytes | 23 bytes |
| `password` | 8 bytes | 7 bytes |

One non-ASCII character can use more than one byte. For example, a name with
many accented or CJK characters can exceed 23 bytes even if it has fewer than
23 characters. The SDK raises `ValueError` rather than silently truncating.

Test with representative names:

```python
from essl_f22 import User

user = User(uid=65001, user_id=" José ", name="José Álvarez")
try:
    record = user.to_record()
except ValueError as exc:
    print("record does not fit:", exc)
else:
    print("record bytes:", len(record))
```

`to_record()` returns exactly 72 bytes when successful.

## Deleting a user

```python
from essl_f22 import Device

with Device("192.168.1.50", comm_key=0) as device:
    device.delete_user(65000)
```

`delete_user(uid)` is destructive. The SDK sends the delete command and
refreshes device data. It cannot undo the delete.

Before deleting:

- export or mirror the user record;
- confirm whether the firmware also removes that user's fingerprint templates;
- confirm whether attendance history remains;
- check whether the person is referenced by another system;
- test on a non-production device.

Do not assume that deleting a user deletes all related data, or that it does
not. Behaviour can vary by firmware.

## Batch operations

There is no public batch-write API. Each `set_user()` and `delete_user()` is a
separate device write followed by a refresh. A loop over hundreds of users will
be slow and will produce many round trips.

If you need bulk changes:

1. Read the current records.
2. Build a changeset and review it.
3. Write in small batches with logging and a way to resume.
4. Verify counts and sample records after each batch.
5. Keep a record of what changed.

## How users relate to attendance

Attendance records contain both `uid` and `user_id` as they were at punch time.
If you change a user's `user_id`, old attendance rows keep the old identifier.
If you delete a user, old attendance rows may remain, depending on the device.
Never join attendance to users by name.

## How users relate to access control

A user's access can come from:

- their group's timezone assignments;
- a personal timezone assignment (`timezone_flag` plus `tz1`–`tz3`);
- a separate user-timezone assignment managed through the user-timezone
  commands.

The exact precedence is firmware behaviour. The SDK exposes the fields but does
not implement the device's policy engine. Validate actual access at the door
with a test user before relying on a schedule change.

## Safe checklist

- [ ] I read the existing user before updating.
- [ ] I am changing only fields I intend to change.
- [ ] I verified the UID is the one I think it is.
- [ ] I checked encoded name and ID lengths.
- [ ] I have a backup or mirror of the record.
- [ ] I tested on a non-production device.
- [ ] I verified the result with `get_user()`.
- [ ] I understand that delete is destructive.

## Next

- [Attendance](attendance.md)
- [Access control and blocking](access-control.md)
- [Manage users](../guides/manage-users.md)
- [Models reference](../reference/models.md#user)
