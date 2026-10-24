# What this is

## Why this matters

Before you install a library that can change who is allowed into a building,
you should know exactly what it does, what it does not do, and where the real
data lives. That knowledge is what separates a safe integration from an
accidental lockout.

## The short answer

The Essl F22 SDK is a **Python library** that talks to an **eSSL/ZKTeco
F22-compatible attendance and access terminal** over a TCP network connection.
It reads and writes the records that already exist on the device.

It is not a cloud service. It is not a replacement for the terminal. It is not
an attendance policy engine. It is a translator between Python method calls and
the device's binary protocol.

```text
Your Python program
        |
        |  method calls (Python)
        v
   Essl F22 SDK
        |
        |  ZKTeco-style TCP frames
        v
F22-compatible terminal  --->  people, fingerprints, attendance, schedules
```

!!! note "In plain English"
    Think of the terminal as a locked filing cabinet in the building. The SDK
    is a set of authorised hands and labelled forms. It can open the right
    drawer, read a card, and file a new one. It cannot invent a person, turn a
    fingerprint into an identity, or recover a card that was destroyed.

## The three pieces

### 1. The device

The terminal stores the operational data:

- user records, including a numeric internal ID, a user ID, a name, a card
  number, a group, and access-schedule fields;
- fingerprint templates and the metadata that says which template belongs to
  which user and finger;
- attendance punch records with a user identifier, a timestamp, a status, and
  a punch value;
- group definitions;
- timezone slots that describe when access is allowed;
- per-user timezone assignments that can override group schedules.

The device is the source of truth for access decisions. It performs fingerprint
matching locally. The SDK does not sit in the access-control path.

### 2. The SDK

The SDK provides:

- a `Device` object for connecting and sending commands;
- typed models such as `User`, `AttendanceRecord`, `TimeZone`, and `GroupInfo`;
- a read-only offline mirror for reporting and comparison;
- a non-destructive blocking manager;
- storage adapters for local files, memory, and external databases;
- an exception hierarchy so failures can be handled deliberately.

### 3. Your storage

If you use the mirror, your program stores a copy of device data in a backend:

- SQLite (the default), JSON, or memory for local use;
- PostgreSQL, MySQL, MongoDB, or Redis for shared or remote use.

The mirror is separate from the device. It is **read-only** from the SDK's point
of view: you can query it, but the SDK does not write it back to the terminal.

## What you can do

| Job | SDK support | Notes |
| --- | --- | --- |
| Read device name, platform, serial, firmware | Yes | `get_device_info()` |
| Read users | Yes | `list_users()`, `get_user()`, `get_user_by_user_id()` |
| Create or update a user | Yes | `set_user()`; create/read/delete are hardware-validated, update is not yet |
| Delete a user | Yes | `delete_user()`; destructive |
| Read attendance | Yes | `list_attendance()`; reads the full log |
| Read fingerprint templates | Yes | `list_fingerprints()`; sensitive bytes |
| Read fingerprint metadata | Yes | Through the mirror, or derive from templates |
| Read groups and timezones | Yes | `list_groups()`, `list_timezones()` |
| Change groups, timezones, user schedules | Yes | Write methods exist |
| Block or unblock a user non-destructively | Yes | Uses an access timezone, not deletion |
| Enroll a fingerprint | No | Enrollment is a device workflow |
| Match fingerprints in Python | No | The device performs matching |
| Change device network or firmware settings | No | Use the device menu or vendor tools |
| Provide a GUI or CLI | No | This is an importable library |
| Restore the mirror back to a device | No | The mirror is read-only |
| Guarantee access-control correctness | No | You must validate schedules and policy |

## What it cannot do

These limits are deliberate and important:

- **It cannot create attendance.** Attendance exists because a person punched
  the device. The SDK only reads records.
- **It cannot recover deleted data.** If a user or attendance record is removed
  and you have no backup, the SDK cannot reconstruct it.
- **It cannot bypass the communication key.** You need the device's key or a
  network path that the device accepts.
- **It cannot make an unsupported device speak the protocol.** Compatibility is
  limited to devices that implement the commands and record formats used here.
- **It cannot protect you from a bad write.** `set_user()` sends a full record.
  If you construct a `User` from scratch and omit fields, those fields are sent
  with their defaults.
- **It cannot provide legal or privacy compliance.** You must decide what
  biometric and attendance data you are allowed to collect, store, and retain.

## Who this is for

- **Python developers** integrating attendance into an HR, payroll, or site
  management system.
- **System administrators** who need a scripted read-only audit or a controlled
  user-management job.
- **Support engineers** who need to inspect device state without the vendor's
  desktop application.
- **Researchers and integrators** who need to understand the F22 record model.

You should be comfortable with Python, a terminal, IP addresses, and the idea of
testing against a non-production device.

## What “F22-compatible” means

The SDK targets the command set and record layouts used by eSSL/ZKTeco F22
terminals. The project has been exercised against an F22-class device reporting
the `ZLM60_TFT` platform and firmware in the 6.60 line. That does not prove that
every device sold under an F22 label, every firmware revision, or every OEM
variant behaves identically.

Before relying on a new model or firmware:

1. Connect read-only.
2. Read device info, users, attendance, fingerprints, groups, and timezones.
3. Compare counts and a sample of records with the device display or vendor
   software.
4. Test writes with a dedicated test user.
5. Only then use it on production data.

See [Compatibility](../help/compatibility.md) for the exact validation stance.

## The safety model

The SDK separates operations into three risk levels:

| Risk | Examples | Default advice |
| --- | --- | --- |
| Read-only | `get_device_info()`, `list_users()`, `list_attendance()`, mirror sync | Safe to start here, but treat the data as sensitive. |
| Reversible write | `block_user()`, `unblock_user()` | Back up state and verify the user's original schedule. |
| Destructive or broad write | `delete_user()`, `set_user()`, `set_timezone()`, `set_group()` | Test on a non-production device and keep a backup. |

The blocking feature is reversible only while its state store is intact. It
changes an access schedule; it does not delete a person. Read
[Access control and blocking](../concepts/access-control.md) before using it.

## Next steps

- Learn the record model: [How it works](../concepts/how-it-works.md).
- Install the package: [Installation](installation.md).
- Connect safely: [First connection](first-connection.md).
