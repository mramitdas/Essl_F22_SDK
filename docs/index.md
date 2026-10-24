# Essl F22 SDK

**A synchronous Python SDK for eSSL/ZKTeco F22 attendance and access terminals.**

The Essl F22 SDK lets a Python program talk directly to a compatible device over the
local network. You can read the people, attendance, fingerprint metadata,
groups, and access schedules stored on the device. You can also create,
update, and delete users, change access schedules, and keep a read-only copy of
the device data in a local or remote database.

Install the SDK:

```bash
pip install Essl_F22_SDK
```
or
```bash
uv add Essl_F22_SDK
```

!!! note "In plain English"
    The terminal is the filing cabinet. The Essl F22 SDK is the set of labelled
    drawers, forms, and procedures your Python program uses to read and update
    that cabinet. It does **not** replace the device, and it does **not** create
    attendance by itself.

## What this handbook is for

This handbook is written for two readers at the same time:

- **Operators and administrators** who need to understand what the SDK can do
  safely before anyone runs it against a live device.
- **Python developers** who need exact method names, record fields, storage
  behaviour, and failure modes.

Every topic explains three things:

1. **Why it matters** — the real-world problem the feature solves.
2. **What it is** — the device concept and the SDK object that represents it.
3. **How to use it** — a small example, the expected result, and the traps.

## Is this the right tool?

Use the Essl F22 SDK when you need to:

- pull attendance from an F22-compatible terminal into your own system;
- manage users from Python without using the vendor's desktop software;
- keep a local or database-backed backup of device records;
- temporarily block a person's access without deleting their user record or
  fingerprint templates;
- inspect the device's groups, timezones, and access assignments.

Do **not** use it when you need to:

- enroll a fingerprint (enrollment happens at the device);
- perform fingerprint matching in Python;
- manage firmware, network settings, or the device's boot process;
- expose the device directly to the public internet;
- get a graphical interface or a command-line application. This is a library.

## Learning paths

### I need to understand the system before touching a device

1. [What this is](getting-started/what-is-this.md)
2. [How it works](concepts/how-it-works.md)
3. [First connection](getting-started/first-connection.md)
4. [Production checklist](guides/production-checklist.md)

### I need to write a program now

1. [Installation](getting-started/installation.md)
2. [Quickstart](getting-started/quickstart.md)
3. [Device API](reference/device-api.md)
4. [Handle errors](guides/handle-errors.md)

### I need to back up attendance

1. [Attendance](concepts/attendance.md)
2. [Mirror and storage](concepts/mirror-and-storage.md)
3. [Back up and sync](guides/back-up-and-sync.md)
4. [Choose storage](guides/choose-storage.md)

### I need to block someone without deleting them

1. [Access control and blocking](concepts/access-control.md)
2. [Block and unblock](guides/block-and-unblock.md)
3. [Production checklist](guides/production-checklist.md)

## A five-minute example

Install the package in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install Essl_F22_SDK
```

Then read the device identity and the first few users:

```python
from essl_f22 import Device

with Device("192.168.1.27", comm_key=0) as device:
    info = device.get_device_info()
    print(info.device_name, info.serial_number, info.firmware_version)

    for user in device.list_users()[:5]:
        print(user.uid, user.user_id, user.name)
```

`Device(...)` does not open the network connection by itself. The `with` block
calls `connect()` on entry and `close()` on exit. The default port is `4370`.
The communication key is a device setting; `0` is the default, not a guarantee.

If the connection fails, read [First connection](getting-started/first-connection.md)
and [Troubleshooting](help/troubleshooting.md) before changing device settings.

## Safety in one screen

!!! warning "Writes are real"
    `set_user()`, `delete_user()`, `set_timezone()`, `set_group()`, and
    `set_user_timezone()` change the live device. `delete_user()` is
    destructive. Test on a non-production device first, and keep a backup of
    the data you are about to change.

!!! warning "Blocking is not deleting"
    `block_user()` changes a person's access schedule. It does not remove the
    user or their fingerprint templates. `unblock_user()` restores the saved
    schedule when the SDK's state store still has it. Back up the state store
    before relying on it.

!!! warning "Biometric data is sensitive"
    `list_fingerprints()` returns raw fingerprint template bytes. Do not log
    them, commit them, or copy them into a mirror. The built-in mirror stores
    only metadata. Treat templates like passwords or identity documents.

!!! warning "The mirror is a copy, not a restore button"
    The SDK's mirror is read-only. It can help you report on and compare
    device data, but it cannot write users, attendance, or templates back to a
    device. It stores full user records, including device user password fields.
    A real backup and restore plan must be tested separately.

## Documentation map

| Section | Read it when you need to… |
| --- | --- |
| [Start here](getting-started/what-is-this.md) | Understand the product, install it, and make a first connection. |
| [Concepts](concepts/how-it-works.md) | Learn how device records, access schedules, and storage fit together. |
| [Guides](guides/manage-users.md) | Perform a specific job safely, step by step. |
| [Reference](reference/device-api.md) | Look up an exact method, field, exception, or protocol detail. |
| [Help](help/troubleshooting.md) | Diagnose a failure, check compatibility, or look up a term. |
| [Contributing](contributing/development.md) | Work on the SDK itself, run quality gates, or prepare a release. |

## Project facts

- **Distribution name:** `Essl_F22_SDK`
- **Import name:** `essl_f22`
- **Python:** 3.12 or newer
- **Transport:** TCP, default port `4370`
- **Core runtime dependencies:** none
- **Optional storage drivers:** PostgreSQL, MySQL, MongoDB, Redis
- **License:** Apache License 2.0

The distribution name is `Essl_F22_SDK` everywhere: in `pyproject.toml`, in pip and
uv commands, and in documentation. The import name is `essl_f22`. Some package
tools display the normalized spelling `essl-f22-sdk` because PEP 503 treats
hyphens, underscores, and periods as equivalent. That is a display convention,
not a different package.

## Where to go next

- New to the device? Start with [What this is](getting-started/what-is-this.md).
- Ready to connect? Go to [First connection](getting-started/first-connection.md).
- Need the exact API? Go to [Device API](reference/device-api.md).
- Something failed? Go to [Troubleshooting](help/troubleshooting.md).
