# Essl F22 SDK

**A synchronous Python SDK for eSSL/ZKTeco F22 attendance and access terminals.**

[![CI](https://github.com/mramitdas/Essl_F22_SDK/actions/workflows/ci.yml/badge.svg)](https://github.com/mramitdas/Essl_F22_SDK/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://github.com/mramitdas/Essl_F22_SDK)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

Essl_F22_SDK 0.1.0 is published on PyPI.

This README is generated from `docs/`; the full handbook lives in the repository.

## Install

```bash
pip install Essl_F22_SDK
```

```bash
uv add Essl_F22_SDK
```

Optional extras:

```bash
pip install "Essl_F22_SDK[postgres]"
pip install "Essl_F22_SDK[mysql]"
pip install "Essl_F22_SDK[mongo]"
pip install "Essl_F22_SDK[redis]"
pip install "Essl_F22_SDK[docs]"
```

The distribution name is `Essl_F22_SDK`. Some package tools display the
normalized spelling `essl-f22-sdk`; that is the same package. The import name is
`essl_f22`.

---


---

### From [docs/index.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/index.md)

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

> **In plain English:**
> The terminal is the filing cabinet. The Essl F22 SDK is the set of labelled
> drawers, forms, and procedures your Python program uses to read and update
> that cabinet. It does **not** replace the device, and it does **not** create
> attendance by itself.
>
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

1. [What this is](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/what-is-this.md)
2. [How it works](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/how-it-works.md)
3. [First connection](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/first-connection.md)
4. [Production checklist](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/production-checklist.md)

### I need to write a program now

1. [Installation](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/installation.md)
2. [Quickstart](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/quickstart.md)
3. [Device API](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/device-api.md)
4. [Handle errors](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/handle-errors.md)

### I need to back up attendance

1. [Attendance](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/attendance.md)
2. [Mirror and storage](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/mirror-and-storage.md)
3. [Back up and sync](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/back-up-and-sync.md)
4. [Choose storage](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/choose-storage.md)

### I need to block someone without deleting them

1. [Access control and blocking](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/access-control.md)
2. [Block and unblock](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/block-and-unblock.md)
3. [Production checklist](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/production-checklist.md)

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

If the connection fails, read [First connection](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/first-connection.md)
and [Troubleshooting](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/troubleshooting.md) before changing device settings.

## Safety in one screen

> **Writes are real:**
> `set_user()`, `delete_user()`, `set_timezone()`, `set_group()`, and
> `set_user_timezone()` change the live device. `delete_user()` is
> destructive. Test on a non-production device first, and keep a backup of
> the data you are about to change.
>
> **Blocking is not deleting:**
> `block_user()` changes a person's access schedule. It does not remove the
> user or their fingerprint templates. `unblock_user()` restores the saved
> schedule when the SDK's state store still has it. Back up the state store
> before relying on it.
>
> **Biometric data is sensitive:**
> `list_fingerprints()` returns raw fingerprint template bytes. Do not log
> them, commit them, or copy them into a mirror. The built-in mirror stores
> only metadata. Treat templates like passwords or identity documents.
>
> **The mirror is a copy, not a restore button:**
> The SDK's mirror is read-only. It can help you report on and compare
> device data, but it cannot write users, attendance, or templates back to a
> device. It stores full user records, including device user password fields.
> A real backup and restore plan must be tested separately.
>
## Documentation map

| Section | Read it when you need to… |
| --- | --- |
| [Start here](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/what-is-this.md) | Understand the product, install it, and make a first connection. |
| [Concepts](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/how-it-works.md) | Learn how device records, access schedules, and storage fit together. |
| [Guides](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/manage-users.md) | Perform a specific job safely, step by step. |
| [Reference](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/device-api.md) | Look up an exact method, field, exception, or protocol detail. |
| [Help](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/troubleshooting.md) | Diagnose a failure, check compatibility, or look up a term. |
| [Contributing](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/contributing/development.md) | Work on the SDK itself, run quality gates, or prepare a release. |

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

- New to the device? Start with [What this is](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/what-is-this.md).
- Ready to connect? Go to [First connection](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/first-connection.md).
- Need the exact API? Go to [Device API](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/device-api.md).
- Something failed? Go to [Troubleshooting](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/troubleshooting.md).

---

### From [docs/getting-started/what-is-this.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/what-is-this.md)

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

> **In plain English:**
> Think of the terminal as a locked filing cabinet in the building. The SDK
> is a set of authorised hands and labelled forms. It can open the right
> drawer, read a card, and file a new one. It cannot invent a person, turn a
> fingerprint into an identity, or recover a card that was destroyed.
>
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

See [Compatibility](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/compatibility.md) for the exact validation stance.

## The safety model

The SDK separates operations into three risk levels:

| Risk | Examples | Default advice |
| --- | --- | --- |
| Read-only | `get_device_info()`, `list_users()`, `list_attendance()`, mirror sync | Safe to start here, but treat the data as sensitive. |
| Reversible write | `block_user()`, `unblock_user()` | Back up state and verify the user's original schedule. |
| Destructive or broad write | `delete_user()`, `set_user()`, `set_timezone()`, `set_group()` | Test on a non-production device and keep a backup. |

The blocking feature is reversible only while its state store is intact. It
changes an access schedule; it does not delete a person. Read
[Access control and blocking](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/access-control.md) before using it.

## Next steps

- Learn the record model: [How it works](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/how-it-works.md).
- Install the package: [Installation](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/installation.md).
- Connect safely: [First connection](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/first-connection.md).

---

### From [docs/getting-started/installation.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/installation.md)

# Installation

## Why this matters

The SDK is a library, not an application. Installing it correctly means your
project's Python interpreter can import `essl_f22`, and that optional database
drivers are present only when you actually use those databases. Installing it
incorrectly usually shows up later as `ModuleNotFoundError` or as a package that
works in one terminal window but not in your program.

## Requirements

- **Python 3.12 or newer.** The package declares `requires-python = ">=3.12"`.
- **Network access to the device** on TCP port `4370` (or the port you configured).
- A virtual environment for your project. Do not install project dependencies
  into the system Python.
- No database driver is required for the default SQLite, JSON, or memory
  backends.

Check your interpreter:

```bash
python --version
```

If that prints 3.11 or older, install a newer Python before continuing.

## Create a virtual environment

=== "macOS / Linux"

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    ```

=== "Windows PowerShell"

    ```powershell
    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    ```

Your prompt should show the environment name, for example `(.venv)`. Every
command below assumes the environment is active.

## Install the library

=== "pip"

    ```bash
    python -m pip install Essl_F22_SDK
    ```

=== "uv"

    ```bash
    uv add Essl_F22_SDK
    ```

Inside an existing uv project, `uv add` records the dependency in
`pyproject.toml` and updates the lock file. `uv sync` installs the environment
from the lock file.

> **Release availability:**
> This handbook assumes `Essl_F22_SDK` is available from your configured package
> index. If you are working before the first public release, install a wheel
> built from the repository:
>
> ```bash
> python -m pip install /path/to/essl_f22_sdk-0.1.0-py3-none-any.whl
> ```
>
> Do not install from an untrusted index or an unofficial package with a
> similar name.
>
## Verify the import

```bash
python -c "from essl_f22 import Device, __version__; print(__version__); print(Device)"
```

Expected shape:

```text
0.1.0
<class 'essl_f22.device.Device'>
```

The exact version may be newer. If the import fails, see
[Troubleshooting](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/troubleshooting.md#the-import-fails).

## Optional database drivers

The core package has no runtime dependencies. External storage drivers are
optional extras so that a program using SQLite does not need a PostgreSQL or
MongoDB driver.

| Backend | Extra | Driver installed |
| --- | --- | --- |
| PostgreSQL | `postgres` | `psycopg[binary]` |
| MySQL | `mysql` | `pymysql` |
| MongoDB | `mongo` | `pymongo` |
| Redis | `redis` | `redis` |
| Documentation build | `docs` | `mkdocs-material` |

Install only what you need:

```bash
python -m pip install "Essl_F22_SDK[postgres]"
python -m pip install "Essl_F22_SDK[mysql]"
python -m pip install "Essl_F22_SDK[mongo]"
python -m pip install "Essl_F22_SDK[redis]"
```

With uv:

```bash
uv add "Essl_F22_SDK[postgres]"
```

If you select a backend without its extra, the SDK raises
`StorageConfigurationError` with an installation hint when it tries to create
the backend. The core import still works because drivers are loaded lazily.

## This is a library, not a CLI

There is no console entry point. After installation you write Python code that
imports the package.

`pipx` and `uvx` are application runners. They can run a Python command in an
isolated environment, but they do not add the library to your project's
interpreter. Use `pip` or `uv add` for normal project use.

For a one-off import check with uv:

```bash
uvx --from Essl_F22_SDK python -c "from essl_f22 import Device; print(Device)"
```

That command runs `python` inside a temporary environment. It does not make
`essl_f22` importable from your own script afterward.

## Upgrading

=== "pip"

    ```bash
    python -m pip install --upgrade Essl_F22_SDK
    ```

=== "uv"

    ```bash
    uv sync --upgrade-package Essl_F22_SDK
    ```

Read the project changelog before upgrading across minor versions. Record,
storage, and error behaviour can change even when the core API stays familiar.

## Uninstalling

```bash
python -m pip uninstall Essl_F22_SDK
```

Uninstalling the package does not delete your mirror, SQLite state database, or
JSON files. Those are your data. Remove them deliberately, after taking a
backup, if you no longer need them.

## Package-name spelling

The distribution name is `Essl_F22_SDK`; the import name is `essl_f22`. Some
tools display the normalized spelling `essl-f22-sdk` because Python package
normalization (PEP 503) treats hyphens, underscores, and periods as equivalent.
Use the distribution name in `pyproject.toml`, install commands, and
documentation; use the import name in Python code.

If `pip show Essl_F22_SDK` reports the package but `pip show essl-f22-sdk` does
not (or the reverse), that is normal spelling normalization, not a second
package.

## Next step

You have the library installed. Now make a safe, read-only connection:
[First connection](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/first-connection.md).

---

### From [docs/getting-started/first-connection.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/first-connection.md)

# First connection

## Why this matters

Most failed SDK sessions are not SDK bugs. They are network, port, or
communication-key problems. A careful first connection proves four things
before you run any write:

1. the computer can reach the device's IP address;
2. TCP port `4370` (or your configured port) is open;
3. the communication key is accepted;
4. the device returns records the SDK can decode.

Do this on a non-production device, or at least during a quiet period with a
known backup.

## Before you start

Collect these facts:

| Fact | Where to find it | Example |
| --- | --- | --- |
| Device IP address | Router DHCP table, device network menu, or vendor tool | `192.168.1.50` |
| TCP port | Device network settings; default is `4370` | `4370` |
| Communication key | Device security/communication settings; ask the administrator | `0` |
| Network path | Same LAN, VLAN, VPN, or routed network | Same subnet |
| Device model/firmware | Device information screen | F22-class, `ZLM60_TFT` |
| Permission to read | Owner/administrator approval | Written approval |

Do not guess the communication key and do not repeatedly try random values. A
wrong key can trigger lockouts or alerts, and some organisations treat repeated
authentication failures as a security incident.

## Step 1: Confirm the address

From the computer that will run the SDK:

=== "macOS / Linux"

    ```bash
    ping -c 3 192.168.1.50
    ```

=== "Windows PowerShell"

    ```powershell
    ping -n 3 192.168.1.50
    ```

If ping fails, the computer may be on a different network, the device may block
ICMP, or the address may be wrong. Ping failure alone does not prove the TCP
port is closed, and ping success does not prove the SDK will connect.

## Step 2: Confirm TCP port 4370

=== "macOS / Linux"

    ```bash
    nc -vz 192.168.1.50 4370
    ```

A successful connection prints something like `succeeded`. A refusal or timeout
means the port is not reachable.

=== "Windows PowerShell"

    ```powershell
    Test-NetConnection -ComputerName 192.168.1.50 -Port 4370
    ```

Look for `TcpTestSucceeded : True`.

If the port is closed:

- confirm the device's TCP port in its network settings;
- confirm the device and computer are on networks that can route to each other;
- check host firewalls, VLAN access rules, and VPN split tunnelling;
- ask the network administrator before changing device settings.

## Step 3: Make a read-only connection

Create a file named `check_device.py`:

```python
from essl_f22 import Device

HOST = "192.168.1.50"
PORT = 4370
COMM_KEY = 0

with Device(HOST, PORT, comm_key=COMM_KEY, timeout=10.0) as device:
    info = device.get_device_info()
    sizes = device.get_free_sizes()

    print("Device name:  ", info.device_name)
    print("Platform:     ", info.platform)
    print("Serial:       ", info.serial_number)
    print("Firmware:     ", info.firmware_version)
    print("Users:        ", sizes.users, "of", sizes.users_capacity)
    print("Fingerprints: ", sizes.fingerprints, "of", sizes.fingerprints_capacity)
    print("Attendance:   ", sizes.attendance, "of", sizes.attendance_capacity)
```

Run it:

```bash
python check_device.py
```

Expected shape:

```text
Device name:   F22
Platform:      ZLM60_TFT
Serial:        ABC1234567890
Firmware:      6.60.0
Users:         42 of 3000
Fingerprints:  80 of 5000
Attendance:    1200 of 100000
```

The numbers are examples. Your device may show different capacities.

> **What the context manager does:**
> `Device(...)` constructs the client but does not open the socket. Entering
> the `with` block calls `connect()`. Leaving the block calls `close()` even
> if an exception occurred. Use the context manager unless you have a good
> reason to manage the lifecycle manually.
>
## Step 4: Read a small, safe sample

Once the identity and counts look correct, read a few users:

```python
from essl_f22 import Device

with Device("192.168.1.50", comm_key=0) as device:
    users = device.list_users()
    for user in users[:5]:
        print(user.uid, user.user_id, repr(user.name))
```

`list_users()` reads the full user buffer, even if you only print five records.
That is how the device protocol works. It is still a read-only operation.

To check attendance without printing the whole log:

```python
with Device("192.168.1.50", comm_key=0) as device:
    records = device.list_attendance()
    print("records:", len(records))
    if records:
        print("newest-ish sample:", records[0])
```

The SDK does not promise that the device returns attendance in chronological
order. Sort or filter explicitly before making claims about the latest punch.

## Step 5: Prove that writes are not happening

The examples above use only read methods. Before moving on, you can wrap the
session in a small guard that makes the intent obvious:

```python
from essl_f22 import Device

with Device("192.168.1.50", comm_key=0) as device:
    before = device.get_free_sizes()
    users = device.list_users()
    fingerprints = device.list_fingerprints()
    after = device.get_free_sizes()

    print("users read:       ", len(users))
    print("templates read:   ", len(fingerprints))
    print("user count before:", before.users)
    print("user count after: ", after.users)
```

The counts should be unchanged. `list_fingerprints()` returns template bytes;
do not print or store them casually.

## Connection options explained

| Argument | Default | What it means |
| --- | --- | --- |
| `host` | required | IPv4 address or hostname of the device. |
| `port` | `4370` | TCP port used by the device protocol. |
| `timeout` | `10.0` | Socket timeout in seconds for connect and operations. |
| `comm_key` | `0` | Device communication key. Confirm it; do not guess. |
| `encoding` | `"utf-8"` | Text encoding for names and identifiers. |
| `max_timezone_slots` | `50` | How many timezone slots `list_timezones()` scans. |
| `max_groups` | `100` | How many group IDs `list_groups()` scans. |
| `storage_backend` | `"sqlite"` | Backend used lazily by blocking and mirror operations. |
| `storage_path` | platform default | File path for SQLite/JSON, or a connection string for external backends. |
| `storage_options` | `None` | Backend options such as `{"dsn": ...}`. |
| `storage` | `None` | An already-constructed storage object you own. |
| `transport` | `None` | Low-level transport override, mainly for tests. |
| `session` | `None` | Low-level session override, mainly for tests. |

The timeout applies to the socket. A very large attendance read can still take
longer than ten seconds even if every individual network operation is healthy.
Increase the timeout for slow links, not as a substitute for fixing a network
problem.

## Lifecycle and concurrency

- One `Device` owns one session.
- Do not share one `Device` across threads without your own locking. The
  session keeps a receive buffer and request sequence state.
- If a connection breaks, close the device and construct a new one. Do not try
  to reuse a half-closed socket.
- `Device.close()` closes storage only if the device created it. If you injected
  `storage=`, you own its lifecycle.
- `get_serial_number()` caches the serial after the first read. A reconnect
  should use a new `Device` if the hardware may have changed.

## Common first-connection failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `DeviceTimeoutError` during connect | Wrong IP, wrong network, firewall, device offline | Recheck address and port; test with `nc` or `Test-NetConnection`. |
| `DeviceConnectionError` with “Connection refused” | Nothing listening on that port | Confirm the device's TCP port. |
| `DeviceAuthenticationError` | Wrong communication key or auth rejected | Ask the administrator for the correct key. Do not brute force. |
| Connect succeeds but reads fail | Firmware/protocol mismatch, session dropped, or timeout | Retry once; then check firmware compatibility. |
| Names look garbled | Encoding mismatch | Confirm the device's text encoding; try a documented alternative only with test data. |
| `ProtocolError` | Malformed or unsupported response | Capture the model/firmware and report it; do not ignore the error. |

See [Troubleshooting](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/troubleshooting.md) for deeper diagnosis.

## Next step

Now that you can connect read-only, run the guided end-to-end example:
[Quickstart](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/quickstart.md).

---

### From [docs/getting-started/quickstart.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/quickstart.md)

# Quickstart

## Why this matters

This page takes you from “the package is installed” to a working read-only
script, an offline mirror, and an optional write test. It is deliberately
ordered from safest to riskiest so you can stop at any point without changing
the device.

## Before you begin

- Complete [Installation](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/installation.md).
- Know the device IP, port, and communication key.
- Confirm the TCP port is reachable with the steps in
  [First connection](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/first-connection.md).
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

> **Attendance can be large:**
> `list_attendance()` reads the entire device log into memory. A device with
> tens of thousands of records can produce a large list and a slow read.
> Start with a small test device or use the mirror after the first successful
> sync.
>
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
[Mirror and storage](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/mirror-and-storage.md).

## Step 4: Optional write test

> **Read this before running:**
> This creates and deletes a real user on a real device. Run it only on a
> non-production device with a UID you know is free. `delete_user()` is
> destructive. The example checks that the UID is free first, but you must
> still verify the device and the UID yourself.
>
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

- read [Access control and blocking](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/access-control.md);
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

- Understand the records: [Users](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/users.md) and
  [Attendance](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/attendance.md).
- Build a real backup: [Back up and sync](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/back-up-and-sync.md).
- Prepare for production: [Production checklist](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/production-checklist.md).

---

### From [docs/concepts/how-it-works.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/how-it-works.md)

# How it works

## Why this matters

The SDK is small, but it sits between three different worlds: Python objects,
a binary device protocol, and persistent storage. Knowing which layer owns
which fact prevents a class of dangerous mistakes, such as assuming a mirror
write changes the device, or assuming a successful method call means the device
has already applied and verified the change.

## The layers

```text
+-----------------------------+
| Your application            |  business rules, scheduling, reports
+-----------------------------+
| essl_f22 public API         |  Device, Mirror, BlockManager, models
+-----------------------------+
| Session and protocol        |  commands, frames, checksums, buffering
+-----------------------------+
| TCP transport               |  socket to host:port
+-----------------------------+
| F22-compatible terminal     |  users, templates, attendance, schedules
+-----------------------------+
| Storage backend             |  SQLite, JSON, memory, PostgreSQL, ...
+-----------------------------+
```

The device is always the authority for access decisions. The SDK never performs
fingerprint matching and never sits in the door-opening path. If your program
crashes, the device continues to enforce its local schedules.

## A read, step by step

When you call `device.list_users()`:

1. The `Device` asks its session to send the user-read command.
2. The session builds a binary frame with a command number, session ID, reply
   ID, and checksum.
3. The transport writes the frame to the TCP socket.
4. The device answers with a frame containing a status and a data buffer.
5. The session reads the buffer in chunks when necessary.
6. The record parser turns 72-byte user records into `User` objects.
7. Your code receives a Python list.

No database is involved unless you explicitly use storage. No local cache is
consulted for device reads.

## A write, step by step

When you call `device.set_user(user)`:

1. The SDK validates the UID range (`0` to `65535`).
2. The `User` is encoded into the device's **full 72-byte record**.
3. The session sends the write command and waits for an acknowledgement.
4. If the device rejects the command, `CommandError` is raised.
5. On success, the SDK asks the device to refresh its in-memory data.
6. The method returns `None`.

`set_user()` does **not** read the record back and compare every field. It
trusts the acknowledgement plus the refresh request. If you need proof of the
final state, call `get_user()` yourself.

`delete_user()` follows a similar path but sends only the UID. It is
destructive and cannot be undone by the SDK.

## The session

A `Session` owns:

- the TCP connection;
- the communication-key exchange;
- the session ID assigned by the device;
- the reply-ID sequence;
- a receive buffer for partial frames;
- command send/receive and buffered-read operations.

`Device(...)` creates the session but does not connect. The context manager
does:

```python
host = "192.168.1.50"

with Device(host, comm_key=0) as device:
    device.get_device_info()
```

is equivalent to:

```python
host = "192.168.1.50"

device = Device(host, comm_key=0)
device.connect()
try:
    device.get_device_info()
finally:
    device.close()
```

One `Device` should be used by one thread at a time. The session has mutable
request and buffer state; concurrent calls on the same instance can interleave
frames. Use one device per worker, or protect the device with a lock.

## The protocol in one paragraph

The SDK speaks a legacy ZKTeco-style binary protocol over TCP. Frames carry a
magic header, a payload length, a command, a checksum, a session ID, and a reply
ID. Some commands return data directly; larger buffers are read in chunks. The
communication key is scrambled with the session ID before authentication. The
protocol is not TLS and the SDK does not add encryption. Run it only on a
trusted, segmented network. See [Protocol internals](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/protocol.md) if
you need the wire details.

## Identity: serial number, UID, and user ID

These three identifiers are easy to confuse:

| Identifier | Scope | Why it matters |
| --- | --- | --- |
| Device serial number | One physical device | The mirror and block state are scoped by serial. |
| UID | Internal device slot, 16-bit | Write and delete operations address users by UID. |
| User ID | Device-visible identifier, up to 23 bytes | Attendance records carry the user ID at punch time. |

Changing a user's `user_id` does not rewrite old attendance records. The old
records still contain the identifier that was used when the punch happened.

The serial number is read from the device and cached by the `Device` instance.
A mirror created for one serial refuses to sync a different serial.

## Time

Device timestamps are decoded into **naive** `datetime` objects. They represent
the device's local wall-clock time. The SDK does not attach a timezone or
convert to UTC.

This means:

- two devices in different timezones produce comparable-looking timestamps
  that are not directly comparable;
- daylight-saving changes are whatever the device did;
- a device with a wrong clock produces wrong attendance timestamps;
- filtering `since`/`until` compares naive datetimes, so use values in the same
  wall-clock frame.

Check and set device time deliberately:

```python
from datetime import datetime

with Device("192.168.1.50", comm_key=0) as device:
    print("device time:", device.get_time())
    # device.set_time(datetime.now())  # write: only when authorised
```

See [Attendance](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/attendance.md) for the operational consequences.

## What is cached

The SDK caches only a few things:

- the device serial number, after the first read;
- the storage backend object, after the first blocking or mirror operation;
- nothing about users, attendance, groups, or timezones.

Every `list_users()`, `list_attendance()`, `list_groups()`, and
`list_timezones()` reads from the device. That is good for freshness and bad
for speed. If you need repeated queries, sync a mirror and query the mirror
instead.

## What the mirror owns

The mirror owns a **copy** of device data in a storage backend. It does not own
the device. The direction is always:

```text
device  --->  mirror
```

There is no supported `mirror  --->  device` path. The mirror cannot restore
users, attendance, schedules, or templates. It is for reporting, comparison,
and offline access.

## Storage ownership

`Device` creates a storage backend lazily on the first operation that needs one.
If you pass `storage=...`, the device uses your object and does not close it.
If the device created the backend, `Device.close()` closes it.

This matters when you share a storage object between multiple devices or
between a device and your own reporting code. Decide who owns the lifecycle and
close it once.

## Security boundary

The SDK does not provide:

- transport encryption;
- user authentication beyond the device communication key;
- audit logging;
- role-based access control;
- biometric template protection beyond “do not store it in the mirror”;
- protection against a malicious device on the network.

The communication key is a shared secret, not a strong identity system. Treat
the device network as sensitive infrastructure. Use a dedicated VLAN or VPN,
restrict which hosts can reach port `4370`, and never expose the device
directly to the internet.

## Failure model

The SDK fails loudly:

- `DeviceConnectionError` for socket and connection failures;
- `DeviceTimeoutError` when an operation exceeds the socket timeout;
- `DeviceAuthenticationError` when the communication key is rejected;
- `CommandError` when the device returns a non-success command status;
- `ProtocolError` when a response is malformed or unsupported;
- `UserNotFoundError` when a requested user does not exist;
- `StorageError` and its subclasses for local or remote storage failures.

Do not catch `Exception` and continue as if a write succeeded. A failed write
may have partially changed device state, especially if the connection dropped
after the device received the command. Verify state after an ambiguous failure.

## Next topics

- [Users](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/users.md)
- [Attendance](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/attendance.md)
- [Fingerprints](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/fingerprints.md)
- [Access control and blocking](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/access-control.md)
- [Mirror and storage](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/mirror-and-storage.md)

---

### From [docs/concepts/users.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/users.md)

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

- [Attendance](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/attendance.md)
- [Access control and blocking](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/access-control.md)
- [Manage users](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/manage-users.md)
- [Models reference](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/models.md#user)

---

### From [docs/concepts/attendance.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/attendance.md)

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
[Protocol internals](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/protocol.md).

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

- [Fingerprints](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/fingerprints.md)
- [Mirror and storage](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/mirror-and-storage.md)
- [Back up and sync](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/back-up-and-sync.md)
- [Models reference](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/models.md#attendancerecord)

---

### From [docs/concepts/fingerprints.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/fingerprints.md)

# Fingerprints

## Why this matters

Fingerprint templates are the most sensitive data the device holds. They are
biometric identifiers, not ordinary rows. The SDK can read them, but it cannot
enroll them, match them, or write them back. It also deliberately keeps them out
of the offline mirror.

Knowing the boundary prevents two common mistakes: treating the mirror as a
biometric backup, and logging template bytes while debugging.

## What the device stores

For each enrolled fingerprint, the device stores a template plus a small header:

| Field | Meaning |
| --- | --- |
| `uid` | Internal user slot that owns the template. |
| `fid` | Finger identifier on the device. The SDK does not map it to a finger name. |
| `flag` | Device-specific template flag. The SDK does not interpret it. |
| `template` | Raw template bytes in the device's proprietary format. |
| `size` | `len(template) + 6`, because the device entry includes a 6-byte header. |

The SDK exposes a frozen `FingerprintTemplate`:

```python
from essl_f22 import FingerprintTemplate

template = FingerprintTemplate(
    uid=295,
    fid=1,
    flag=0,
    template=b"...",  # raw device bytes
)
print(template.size)
```

The raw bytes are not a standard image and are not useful without the device or
vendor tooling. Do not try to parse them as a fingerprint image.

## Reading fingerprints

```python
from essl_f22 import Device

with Device("192.168.1.50", comm_key=0) as device:
    templates = device.list_fingerprints()
    print("templates:", len(templates))

    for template in templates[:3]:
        print(
            "uid=",
            template.uid,
            "fid=",
            template.fid,
            "flag=",
            template.flag,
            "size=",
            template.size,
        )
```

`list_fingerprints()` reads the full template buffer. It is a read-only
operation, but it transfers sensitive bytes over the network and creates Python
`bytes` objects in memory.

To find one user's templates:

```python
templates = device.get_user_fingerprints(295)
print([(item.fid, item.flag, item.size) for item in templates])
```

`get_user_fingerprints()` calls `list_fingerprints()` and filters in Python. It
is not a device-side lookup.

## What the mirror stores

The mirror stores only `FingerprintMetadata`:

```python
from essl_f22 import FingerprintMetadata

metadata = FingerprintMetadata(uid=295, fid=1, flag=0, size=512)
```

It does **not** store the `template` bytes. This is intentional:

- biometric templates are highly sensitive;
- the mirror is for reporting and comparison, not biometric restore;
- a stolen mirror should not become a stolen biometric database.

You can still inspect metadata:

```python
with Device(
    "192.168.1.50",
    comm_key=0,
    storage_path="mirror.db",
) as device:
    device.sync("full")
    mirror = device.mirror()

    for item in mirror.list_fingerprints()[:5]:
        print(item.uid, item.fid, item.flag, item.size)
```

## What the SDK cannot do

The public API does not provide:

- fingerprint enrollment;
- fingerprint template writes;
- fingerprint deletion as a separate operation;
- fingerprint matching or identification;
- conversion to an image;
- template format decoding;
- a supported way to restore templates from the mirror.

Enrollment and matching are device workflows. The SDK reads the results.

Deleting a user may or may not delete that user's templates, depending on the
firmware. Test the behaviour on a non-production device before assuming either
way.

## Handling templates safely

If you must read templates, treat the bytes as secrets:

- do not print them;
- do not put them in logs, exception messages, or analytics;
- do not commit them to source control;
- do not copy them to a mirror or shared bucket;
- restrict access to the process and host that read them;
- delete them from memory as soon as the task is done where practical;
- document why you need them and who approved the access.

Python cannot guarantee secure memory erasure. Avoiding collection is stronger
than trying to wipe a `bytes` object after the fact.

## A metadata-only audit

If you only need to verify enrollment counts, avoid holding templates longer
than necessary:

```python
from collections import Counter

from essl_f22 import Device

with Device("192.168.1.50", comm_key=0) as device:
    templates = device.list_fingerprints()
    per_user = Counter(item.uid for item in templates)

    print("total templates:", len(templates))
    print("users with templates:", len(per_user))
    print("uid 295:", per_user.get(295, 0))
```

This still reads the raw bytes. The audit reports only metadata and never
prints the template contents.

## Compliance questions to answer

Before reading biometric data, answer these with your organisation:

- Is enrollment consented and documented?
- Is the template considered personal or sensitive personal data?
- How long may it be retained?
- Who may access it?
- Is it transferred or stored outside the device?
- What happens when a person leaves or withdraws consent?
- Does local law require deletion of templates on request?

The SDK does not answer these questions. It gives you a low-level read. Use it
only within a policy you can defend.

## Recovery reality

Because the mirror does not store template bytes and the SDK has no template
write API, the mirror is not a biometric disaster-recovery plan. A real recovery
plan needs a supported vendor backup/restore process, tested separately.

## Next

- [Access control and blocking](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/access-control.md)
- [Mirror and storage](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/mirror-and-storage.md)
- [Models reference](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/models.md#fingerprinttemplate)

---

### From [docs/concepts/access-control.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/access-control.md)

# Access control and blocking

## Why this matters

Access control decides who can open a door and when. The SDK can read and write
the device's schedules, and it offers a non-destructive way to block a person
temporarily. That is useful, but it is also the area where a wrong assumption
can lock out a whole group or silently remove a legitimate schedule.

This page explains the device model, then the exact blocking algorithm. Read it
before using `block_user()` on a real person.

> **Not hardware-validated:**
> The blocking algorithm is tested with fake transports, but it has not been
> validated against a physical door or production access policy. Verify the
> full block, door, unblock, and door sequence on a non-production device.
>
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

- [Block and unblock](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/block-and-unblock.md)
- [Mirror and storage](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/mirror-and-storage.md)
- [Models reference](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/models.md#timezone)

---

### From [docs/concepts/mirror-and-storage.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/mirror-and-storage.md)

# Mirror and storage

## Why this matters

Reading a device every time you need a report is slow, fragile, and sometimes
impossible. A mirror gives you a local, queryable copy. But a copy is only
useful if you know exactly what it contains, when it was refreshed, and what it
cannot do.

The most dangerous misunderstanding is thinking the mirror is a backup/restore
system. It is not. It is a read-only offline snapshot.

## The direction of data

```text
device  --->  sync  --->  storage backend  --->  Mirror queries
```

There is no supported reverse path. The SDK cannot restore users, attendance,
schedules, or fingerprint templates from the mirror to a device.

## What the mirror stores

For each device serial, the mirror stores:

| Collection | Contents |
| --- | --- |
| Device info | Platform, device name, serial number, firmware version. |
| Users | Full `User` records, including the device user password field. |
| Groups | `GroupInfo` records. |
| Timezones | `TimeZone` records keyed by slot. |
| Fingerprints | Metadata only: `uid`, `fid`, `flag`, `size`. |
| Attendance | Full `AttendanceRecord` records. |
| Sync state | Last sync time, mode, and collection counts. |

What it does **not** store:

- fingerprint template bytes;
- the device communication key or administrator credentials;
- a copy of the device firmware;
- a restore log or write-back plan;
- proof that the device still matches the snapshot.

> **User passwords are stored:**
> The mirror persists full `User` records, including the device user
> `password` field. Protect the mirror like any other credential store, and
> do not assume it is safe to share or export.
>
## Per-device scope

A mirror is scoped to one device serial number. `Device.mirror()` uses the
serial of the connected device. If you construct a `Mirror` yourself and then
try to sync a different device, `SyncError` is raised.

This prevents two devices with similar data from overwriting each other in the
same storage namespace.

## Sync modes

### Full sync

```python
result = device.sync("full")
```

A full sync:

- replaces device info;
- replaces users;
- replaces groups;
- replaces timezones;
- replaces fingerprint metadata;
- replaces attendance.

It is the simplest way to get a clean snapshot. It is also the most expensive,
because it reads and writes everything.

### Incremental sync

```python
result = device.sync("incremental")
```

An incremental sync:

- replaces device info, users, groups, timezones, and fingerprint metadata;
- computes a stable key for every attendance record;
- inserts attendance records whose key is not already present;
- leaves existing attendance records in place;
- if the device's attendance count is lower than the mirror count, replaces
  attendance instead.

The last rule handles a device whose log was cleared or reset. Without it, the
mirror would keep stale records forever.

Incremental sync is not a delta protocol. The SDK still reads the full
attendance log from the device. The “incremental” part is how the storage layer
merges it.

## The stable attendance key

The key is a SHA-256 hash of the canonical attendance document:

```text
uid + user_id + timestamp + status + punch
```

Two records with identical values collapse to one key. Since the key is
content-addressed, an existing key already represents the same record; the
storage layer does not need to rewrite it.

This gives you duplicate suppression across repeated reads. It also means the
mirror is not a legal-grade event log if two distinct events could be
byte-for-byte identical in all five fields. Understand that trade-off before
using it for payroll or compliance.

## What `SyncResult` tells you

```python
result = device.sync("full")

print(result.device_serial)
print(result.mode)
print(result.synced_at)  # local time when the sync finished
print(result.users)
print(result.groups)
print(result.timezones)
print(result.fingerprints)
print(result.attendance)  # count after the sync
print(result.new_attendance)  # new records in this run
print(result.attendance_replaced)
```

| Field | Meaning |
| --- | --- |
| `synced_at` | Local `datetime.now()` when the sync finished, not device time. |
| `users` | Number of users read from the device. |
| `groups` | Number of groups read. |
| `timezones` | Number of timezone slots returned. |
| `fingerprints` | Number of fingerprint metadata entries read. |
| `attendance` | Attendance count in storage after the sync. |
| `new_attendance` | New records inserted in this run, or the full count when attendance was replaced. |
| `attendance_replaced` | Whether attendance was replaced rather than merged. |

`new_attendance` is not “punches since the last sync” in a temporal sense. It
is a storage-level count of newly inserted keys. If the device has a record
whose key already exists, it is not new.

## Is sync atomic?

No, not across collections. The SDK writes device info, users, groups,
timezones, fingerprint metadata, and attendance as separate storage operations.
If the process or database fails midway, the mirror can contain a partial
update.

For most backends, each individual collection replacement is atomic, but the
whole snapshot is not. Design your reporting to tolerate a partial sync, or
sync into a fresh database and swap it at the application level.

Do not run two syncs for the same device serial concurrently against the same
storage. The writes can interleave.

## The `Mirror` object

```python
with Device(
    "192.168.1.50",
    comm_key=0,
    storage_path="mirror.db",
) as device:
    result = device.sync("incremental")
    mirror = device.mirror()

    print(mirror.device_serial)
    print(mirror.get_device_info())
    print(mirror.list_users()[:3])
    print(mirror.get_user(295))
    print(mirror.get_user_by_user_id("1001"))
    print(mirror.list_fingerprints()[:3])
    print(mirror.list_attendance(uid=295, limit=10))
    print(mirror.attendance_count())
    print(mirror.list_groups())
    print(mirror.list_timezones())
    print(mirror.get_sync_state())
```

`Mirror` is read-only. Its methods query storage; they do not contact the
device.

Important error behaviour:

- `Mirror.get_user()` raises `UserNotFoundError` if the user is absent.
- `Mirror.get_timezone()` and `Mirror.get_group()` raise
  `MirrorRecordNotFoundError` if the record is absent.
- `Mirror.sync()` raises `SyncError` for an unsupported mode or a serial
  mismatch.

`Mirror.snapshot()` loads every collection, including all attendance, into a
single `MirrorSnapshot`. It is convenient for small datasets and dangerous for
large ones.

## Storage backends

| Backend | Name(s) | Extra | Connection value | Best for |
| --- | --- | --- | --- | --- |
| SQLite | `sqlite` | none | `storage_path` | Single-host mirror and block state. |
| JSON | `json` | none | `storage_path` | Small, inspectable snapshots. |
| Memory | `memory` | none | none | Tests and short-lived demos. |
| PostgreSQL | `postgres`, `postgresql` | `postgres` | `storage_options={"dsn": ...}` or path | Shared, durable storage. |
| MySQL | `mysql` | `mysql` | `storage_options={"dsn": ...}` or path | Shared, durable storage. |
| MongoDB | `mongo`, `mongodb` | `mongo` | `storage_options={"uri": ...}` or path | Document-oriented shared storage. |
| Redis | `redis` | `redis` | `storage_options={"url": ...}` or path | Fast, ephemeral/shared state. |

Backend names are case-insensitive.

## Choosing a path or connection value

```python
from essl_f22 import Device

device = Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="sqlite",
    storage_path="data/mirror.db",
)
```

For external backends:

```python
device = Device(
    "192.168.1.50",
    comm_key=0,
    storage_backend="postgres",
    storage_options={"dsn": "postgresql://user:pass@db/app"},
)
```

Rules:

1. `storage_options` takes precedence over `storage_path`.
2. `storage_path` can carry a DSN, URI, or URL for an external backend.
3. An injected `storage=` object takes precedence over both.
4. A `Device` closes only storage it created. Injected storage remains yours.

The connection value must be non-empty. A missing DSN/URI/URL raises
`StorageConfigurationError` when the backend is created.

## Default paths

The SQLite and JSON backends use platform-specific application data paths when
you do not provide one:

| Helper | Default |
| --- | --- |
| `default_data_dir()` | Platform application data directory for `essl_f22`. |
| `default_state_path()` | `state.db` inside that directory. |
| `default_mirror_path()` | `mirror.json` inside that directory. |

```python
from essl_f22 import default_data_dir, default_mirror_path, default_state_path

print(default_data_dir())
print(default_state_path())
print(default_mirror_path())
```

On macOS the base is under `~/Library/Application Support/essl_f22`; on Windows
it uses `LOCALAPPDATA`; on Linux it follows `XDG_DATA_HOME` or
`~/.local/share`.

The default SQLite backend is used for both block state and the mirror. That is
convenient, but it means deleting the state database also deletes the local
mirror. Use an explicit path when the two have different retention needs.

## Storage lifecycle

Storage is created lazily:

- `Device(...)` does not touch storage.
- The first `block_user()`, `unblock_user()`, `is_user_blocked()`,
  `get_blocked_users()`, `mirror()`, or `sync()` creates it.
- `Device.close()` closes it only if the device created it.

If you create a `StorageBackend` yourself:

```python
from essl_f22 import Device, SqliteStorage

storage = SqliteStorage("shared.db")
try:
    with Device("192.168.1.50", comm_key=0, storage=storage) as device:
        device.sync("full")
        print(device.mirror().attendance_count())
finally:
    storage.close()
```

Do not close injected storage while another device or reporting job is still
using it.

## Concurrency and durability

| Backend | Notes |
| --- | --- |
| Memory | Process-local; lost on exit; not shared between processes. |
| JSON | Loads the whole file at construction and rewrites it on each change. One writer per file is the safe assumption. |
| SQLite | Durable local file; each operation opens a connection. Suitable for one host, with normal SQLite concurrency limits. |
| PostgreSQL / MySQL | Shared database; the SDK creates a `documents` table; use normal database access controls and backups. |
| MongoDB | Shared database; the SDK uses a `documents` collection and a unique namespace/key index. |
| Redis | Shared service; data lives in hashes named `essl_f22:documents:<namespace>`. Confirm persistence and eviction policy before treating it as durable. |

For all backends, the mirror is a copy. Your database backup policy, access
control, encryption, and retention rules still apply.

## What the mirror is good for

- fast read-only reports;
- comparing two snapshots;
- searching attendance without repeatedly reading the device;
- keeping a local copy when the device is offline;
- metadata audits without holding template bytes.

## What the mirror is not good for

- restoring a device;
- biometric disaster recovery;
- proving that the device still matches the copy;
- legal-grade audit without additional controls;
- real-time access decisions;
- replacing a device-vendor backup process.

## Next

- [Choose storage](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/choose-storage.md)
- [Back up and sync](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/back-up-and-sync.md)
- [Storage reference](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/storage.md)

---

### From [docs/guides/manage-users.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/manage-users.md)

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

> **Hardware validation gap:**
> Create, read, and delete have been exercised on hardware. Updating an
> existing user has not yet been hardware-validated. Run the dry-run and the
> update against a dedicated test user on a non-production device first.
>
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

> **Destructive:**
> `delete_user()` cannot be undone by the SDK. Confirm the UID, back up the
> record, and understand how the firmware treats attendance and fingerprint
> templates before deleting.
>
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

- [Block and unblock](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/block-and-unblock.md)
- [Production checklist](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/production-checklist.md)
- [Users concept](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/users.md)

---

### From [docs/guides/block-and-unblock.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/block-and-unblock.md)

# Block and unblock

## Why this matters

Blocking is the SDK's least destructive way to stop access: the user and their
fingerprints stay in place, but their schedule becomes deny-all. That is safer
than deleting a person, but it still changes access immediately and depends on a
local state store to restore the original schedule later.

This guide is a controlled procedure. Do not skip the preflight or the state
backup.

> **Not hardware-validated:**
> Blocking and unblocking are covered by unit tests with fake transports, but
> they have not been validated against a physical access policy. Test the
> full block, door, unblock, and door sequence on a non-production device.
>
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

Full details: [Access control and blocking](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/access-control.md).

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

- [Production checklist](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/production-checklist.md)
- [Access control concept](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/access-control.md)
- [Handle errors](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/handle-errors.md)

---

### From [docs/guides/back-up-and-sync.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/back-up-and-sync.md)

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
[Attendance](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/attendance.md#exporting-attendance). Remember that the
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

- [Choose storage](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/choose-storage.md)
- [Production checklist](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/production-checklist.md)
- [Mirror and storage](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/mirror-and-storage.md)

---

### From [docs/guides/choose-storage.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/choose-storage.md)

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

- [Storage reference](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/storage.md)
- [Back up and sync](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/back-up-and-sync.md)
- [Production checklist](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/production-checklist.md)

---

### From [docs/guides/handle-errors.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/handle-errors.md)

# Handle errors

## Why this matters

A device integration fails in more ways than a normal function call: the network
drops, the key is wrong, the device rejects a command, a response is malformed,
a database is unavailable, or a write succeeds on the device but the
acknowledgement never arrives. Treating all of these as “something went wrong”
makes recovery dangerous.

This guide shows which errors to catch, which to retry, and which to stop on.

## The error tree

```text
ESSL22Error
├── DeviceConnectionError
├── DeviceAuthenticationError
├── DeviceTimeoutError
├── ProtocolError
├── CommandError
├── DeviceVerificationError
├── UserNotFoundError
├── NoFreeTimeZoneSlotError
└── StorageError
    ├── StorageConfigurationError
    ├── MirrorRecordNotFoundError
    ├── SyncError
    └── StateStoreError
```

All SDK errors inherit from `ESSL22Error`. That gives you a clean outer catch
without catching programming mistakes such as `TypeError` or `AttributeError`.

## What each error means

| Error | Meaning | Typical action |
| --- | --- | --- |
| `DeviceConnectionError` | The socket could not open, closed, or is not usable. | Check network and device power; retry a read with backoff. |
| `DeviceTimeoutError` | A connect or command exceeded the timeout. | Check network; retry reads cautiously. For writes, verify state first. |
| `DeviceAuthenticationError` | The communication key was rejected or the connect response was unexpected. | Ask for the correct key; do not brute force. |
| `ProtocolError` | The response was malformed, truncated, or unsupported. | Capture model/firmware; do not loop retries. |
| `CommandError` | The device returned a non-success command code. | Inspect `exc.code`; fix the request or device state. |
| `DeviceVerificationError` | A block/unblock read-back did not match. | Re-read the user's assignment; do not assume success. |
| `UserNotFoundError` | The requested UID or user ID does not exist. | Confirm the identifier; create the user if intended. |
| `NoFreeTimeZoneSlotError` | No eligible timezone slot is available for blocking. | Free a slot or use another access-control method. |
| `StorageError` | Base for storage failures. | Handle the specific subclass where possible. |
| `StorageConfigurationError` | Unknown backend, missing driver, or missing connection value. | Install the extra or fix the DSN/URI/URL. |
| `MirrorRecordNotFoundError` | A mirror timezone or group record is absent. | Re-sync or check the slot/group ID. |
| `SyncError` | Unsupported sync mode or serial mismatch. | Fix the mode or use the correct mirror. |
| `StateStoreError` | Block state could not be read or written. | Check permissions, disk, and database availability. |

`CommandError` exposes the device code:

```python
from essl_f22 import CommandError

try:
    ...
except CommandError as exc:
    print(f"device rejected command with 0x{exc.code:04X}")
```

## A basic read pattern

```python
from essl_f22 import (
    Device,
    DeviceAuthenticationError,
    DeviceConnectionError,
    DeviceTimeoutError,
    ESSL22Error,
)

try:
    with Device("192.168.1.50", comm_key=0, timeout=10.0) as device:
        users = device.list_users()
        print("users:", len(users))
except DeviceAuthenticationError:
    print("The communication key was rejected. Ask the administrator.")
except DeviceTimeoutError:
    print("The device did not answer in time. Check the network and address.")
except DeviceConnectionError as exc:
    print("Connection failed:", exc)
except ESSL22Error as exc:
    print("SDK error:", type(exc).__name__, exc)
```

Why this order:

- authentication is a configuration/security problem, not a transient network
  problem;
- timeout and connection failures are infrastructure problems;
- the outer `ESSL22Error` catches anything else from the SDK;
- programming errors are not swallowed.

## Retrying reads

Reads are usually safe to retry because they do not change the device. Use a
small, bounded retry with a delay:

```python
import time

from essl_f22 import Device, DeviceConnectionError, DeviceTimeoutError


def read_users(host: str, comm_key: int, attempts: int = 3) -> list:
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            with Device(host, comm_key=comm_key, timeout=10.0) as device:
                return device.list_users()
        except (DeviceConnectionError, DeviceTimeoutError) as exc:
            last_error = exc
            print(f"read attempt {attempt} failed: {exc}")
            if attempt < attempts:
                time.sleep(2**attempt)

    raise RuntimeError("device read failed after retries") from last_error
```

Do not retry:

- `DeviceAuthenticationError`;
- `ProtocolError`;
- `StorageConfigurationError`;
- `UserNotFoundError` when the absence is expected and meaningful;
- `CommandError` without changing the request or device state.

For large attendance reads, a timeout may simply mean “increase the timeout or
run off-peak”, not “retry immediately”.

## Writes and ambiguous outcomes

A write is different. A timeout can occur after the device received the command
but before the SDK read the acknowledgement. The write may have succeeded.

```python
from essl_f22 import Device, DeviceTimeoutError

try:
    with Device("192.168.1.50", comm_key=0) as device:
        device.set_user(user)
except DeviceTimeoutError:
    print("Outcome unknown. Reconnect and read the record before retrying.")
    # Do not blindly call set_user() again.
```

Recovery pattern:

1. Reconnect with a new `Device`.
2. Read the target record.
3. Compare it with the intended state.
4. If it matches, treat the write as successful.
5. If it does not match, decide whether to retry.
6. Record what you observed.

Never retry a delete or a timezone write just because the first call timed out.

## CommandError

`CommandError` means the device responded, but rejected the operation. Retrying
the same bytes usually produces the same rejection.

Common causes:

- the UID does not exist;
- a timezone slot is absent;
- the device is in a mode that rejects writes;
- the record is invalid for that firmware;
- a prerequisite command was not performed.

Inspect the code and the operation. For `list_timezones()` and `list_groups()`,
the SDK internally skips the device's “not found” code `0x1381`; other command
errors propagate.

## Verification errors

`DeviceVerificationError` is specific to blocking/unblocking. When a block
read-back does not match, the manager attempts to restore the original schedule
before raising. When an unblock read-back does not match, it raises without a
second automatic change.

After catching it:

1. reconnect;
2. read `get_user_timezone(uid)`;
3. compare with the intended state;
4. restore deliberately if needed;
5. do not report success to the operator until the device matches.

## Storage errors

### Missing driver or connection value

```python
from essl_f22 import StorageConfigurationError

try:
    device = Device(
        "192.168.1.50",
        storage_backend="postgres",
        storage_options={},
    )
    device.sync("full")
except StorageConfigurationError as exc:
    print("Fix storage configuration:", exc)
```

The backend is created lazily, so the error appears at the first storage
operation, not at `Device(...)` construction.

### State store failure during blocking

A `StateStoreError` during `block_user()` is serious: the SDK may have changed
the device but failed to save the original assignment. Stop, inspect the user's
current schedule, and restore from backup or a recorded value.

### Partial sync

A storage error during `sync()` can leave some collections updated and others
not. The sync is not atomic across collections. Re-run a full sync after fixing
the storage problem, and verify counts before trusting reports.

## Logging safely

Log:

- operation name;
- device serial or a non-secret device label;
- UID/user ID only if your privacy policy allows it;
- exception type and message;
- command code for `CommandError`;
- timestamps and retry counts.

Do not log:

- communication keys;
- database passwords or full DSNs;
- fingerprint template bytes;
- full attendance exports;
- names and other personal data unless necessary and approved.

A useful log line:

```text
sync failed serial=ABC123 mode=incremental error=StateStoreError retry=2
```

## Cleanup

Use the context manager so the socket and owned storage are closed even on
failure:

```python
with Device("192.168.1.50", comm_key=0) as device:
    device.list_users()
```

If you manage the lifecycle manually, use `try/finally`:

```python
device = Device("192.168.1.50", comm_key=0)
try:
    device.connect()
    device.list_users()
finally:
    device.close()
```

If you injected `storage=`, close it yourself after all users of that object are
done.

## When to stop and escalate

Stop and involve the device/access-control owner when:

- authentication fails repeatedly;
- a write's outcome is unknown and cannot be verified;
- blocking state is missing or inconsistent;
- a timezone or group change could affect a group of people;
- the device reports a protocol response the SDK does not understand;
- the device clock or access behaviour differs from the expected model.

Guessing is more dangerous than pausing.

## Next

- [Troubleshooting](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/troubleshooting.md)
- [Production checklist](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/production-checklist.md)
- [Errors reference](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/errors.md)

---

### From [docs/guides/production-checklist.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/production-checklist.md)

# Production checklist

## Why this matters

A successful test on a lab device proves that the protocol works. It does not
prove that the integration is safe for real people, real attendance, and real
access decisions. This checklist closes the operational gaps: ownership,
network exposure, backups, verification, monitoring, privacy, and recovery.

Use it before the first production run and again after any material change.

## 1. Ownership and approval

- [ ] A named owner is responsible for the device and the integration.
- [ ] A named owner is responsible for access-control policy.
- [ ] The change has written approval.
- [ ] The maintenance window and rollback window are agreed.
- [ ] Someone can physically access the device if the network fails.
- [ ] The incident contact list is current.

## 2. Network and exposure

- [ ] The device is on a dedicated VLAN or trusted network segment.
- [ ] Only approved hosts can reach TCP port `4370`.
- [ ] Port `4370` is **not** exposed to the public internet.
- [ ] Firewall rules are documented and reviewed.
- [ ] VPN or jump-host access is required for remote administration.
- [ ] The device IP is static or reserved by DHCP.
- [ ] The host running the SDK has a stable address or documented NAT path.
- [ ] Network latency and packet loss have been measured during peak hours.
- [ ] The device's TCP port and communication key are recorded in the
  configuration inventory.

## 3. Credentials and secrets

- [ ] The communication key is stored in a secret store, not source code.
- [ ] Database passwords and DSNs are stored in a secret store.
- [ ] Secrets are not printed in logs, exception messages, or tickets.
- [ ] Credentials are rotated on a defined schedule.
- [ ] The database user has least privilege.
- [ ] TLS is enabled for database connections that cross untrusted networks.
- [ ] The communication key is not treated as strong authentication for the
  device network.

## 4. Device baseline

- [ ] Model, platform, firmware, and serial are recorded.
- [ ] User, fingerprint, attendance, group, and timezone counts are recorded.
- [ ] A sample user is compared with the device display or vendor software.
- [ ] A sample attendance record is compared with the device display.
- [ ] Timezone slots and group assignments are understood.
- [ ] The device clock is correct for its timezone.
- [ ] Daylight-saving behaviour is understood.
- [ ] The device's capacity limits are known.
- [ ] A read-only sync has completed and its counts match expectations.

```bash
# Reachability check examples
nc -vz DEVICE_IP 4370
# or on Windows PowerShell
Test-NetConnection -ComputerName DEVICE_IP -Port 4370
```

## 5. Read-only proof

- [ ] The first production run uses only read methods.
- [ ] No `set_*`, `delete_*`, `block_*`, or `unblock_*` call is reachable in the
  read-only path.
- [ ] The read path has a timeout and a bounded retry policy.
- [ ] The mirror path is tested.
- [ ] The read path does not print fingerprint templates.
- [ ] The read path does not log full personal records unnecessarily.

## 6. Backup and state

- [ ] The mirror path is explicit and on durable storage.
- [ ] The block-state path is explicit and backed up separately if needed.
- [ ] A restore of the storage backup has been tested.
- [ ] The backup is encrypted and access-controlled; it contains user password
  fields and personal data.
- [ ] The backup contains no communication key or database credentials.
- [ ] The retention period is defined.
- [ ] Old snapshots are deleted securely.
- [ ] The team knows that the mirror cannot restore fingerprint templates.
- [ ] A vendor-supported device backup/restore process exists if biometric
  recovery is required.

## 7. Access changes

- [ ] Blocking and unblocking have been tested on a non-production user.
- [ ] The state store is backed up before a block.
- [ ] A free default-allow-all timezone slot was confirmed.
- [ ] The user's original assignment was recorded outside the state store.
- [ ] Access was tested at the door, not only through the API.
- [ ] The team knows that `unblock_user()` with no saved state disables personal
  scheduling.
- [ ] The team knows that deleting a user and blocking a user are different.
- [ ] A lost-state recovery procedure is documented.

## 8. Write safety

- [ ] Every update reads the existing record first.
- [ ] Every write preserves fields that are not intentionally changed.
- [ ] UID ranges and encoded field lengths are validated before writing.
- [ ] Deletes have a backup and a second-person review.
- [ ] Batch jobs stop on the first unexpected result.
- [ ] Batch jobs have a resume plan.
- [ ] Writes are verified with a read-back.
- [ ] Ambiguous timeouts are investigated before retrying.
- [ ] Writes are logged with operator, target, and result.

## 9. Scheduling and performance

- [ ] Sync frequency is defined.
- [ ] Full and incremental sync schedules are documented.
- [ ] Sync runs off-peak where possible.
- [ ] Only one sync per device serial runs at a time.
- [ ] Timeout values are appropriate for the attendance volume.
- [ ] Memory use for large attendance reads is measured.
- [ ] Storage growth is monitored.
- [ ] Database connection limits are respected.
- [ ] JSON is not used for high-volume concurrent writes.
- [ ] Redis durability and eviction policy are confirmed, if used.

## 10. Monitoring and alerting

- [ ] Connection failures are alerted.
- [ ] Authentication failures are alerted.
- [ ] Sync failures are alerted.
- [ ] An unexpected `attendance_replaced=True` is alerted.
- [ ] A large drop in device or mirror counts is alerted.
- [ ] Disk and database capacity are monitored.
- [ ] The device's own event log or tamper alerts are monitored separately.
- [ ] Logs exclude secrets and biometric templates.
- [ ] A runbook links to [Troubleshooting](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/troubleshooting.md).

## 11. Privacy and retention

- [ ] The lawful basis for processing attendance and biometric data is
  documented.
- [ ] Enrollment consent is handled by the device process.
- [ ] Access to attendance exports and mirrors is restricted.
- [ ] Attendance retention is defined.
- [ ] Deletion requests have a tested procedure.
- [ ] Backups follow the same retention and access rules as live data.
- [ ] Third-party processors are approved and contractually covered.
- [ ] Raw templates are not copied into the mirror or logs.

## 12. Version and change management

- [ ] The `Essl_F22_SDK` version is pinned in the lock file or requirements.
- [ ] The device model and firmware are recorded against that version.
- [ ] Upgrades are tested on a non-production device.
- [ ] The changelog is reviewed before upgrading.
- [ ] The database schema impact is understood.
- [ ] A rollback artifact (wheel or lock file) is retained.
- [ ] The branch/PR/release process in the repository is followed.
- [ ] Documentation is updated with the change.

## 13. Incident response

- [ ] The team can stop scheduled jobs quickly.
- [ ] The team can revoke database credentials.
- [ ] The team can block a user without deleting them.
- [ ] The team can restore access from recorded state.
- [ ] The team can replace the device and reconcile serial-scoped state.
- [ ] The team knows how to preserve logs for an investigation.
- [ ] The team knows not to retry destructive writes blindly.
- [ ] A post-incident review is required for access-control mistakes.

## 14. Final go/no-go

Before the first production write:

- [ ] Read-only production run succeeded.
- [ ] Mirror counts and samples match the device.
- [ ] Backup was taken and restore-tested.
- [ ] A test user was created, read, updated, and deleted successfully.
- [ ] Block and unblock were tested end-to-end on a non-production user.
- [ ] The operator has the runbook open.
- [ ] The rollback owner is available.
- [ ] The approval reference is recorded.

If any item is unchecked, do not proceed with a broad write. Resolve it or
narrow the change to a reversible test.

## Next

- [Handle errors](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/handle-errors.md)
- [Troubleshooting](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/troubleshooting.md)
- [Compatibility](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/compatibility.md)

---

### From [docs/reference/device-api.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/device-api.md)

# Device API

## Why this matters

This is the exact surface most programs use. The signatures, return types, and
write behaviour matter because a small misunderstanding can turn a read-only
script into a device change.

All examples assume:

```python
from essl_f22 import Device
```

## Constructor

```text
Device(
    host: str,
    port: int = 4370,
    *,
    timeout: float = 10.0,
    comm_key: int = 0,
    encoding: str = "utf-8",
    transport: Transport | None = None,
    session: SessionLike | None = None,
    storage: StorageBackend | None = None,
    storage_backend: str = "sqlite",
    storage_path: Path | str | None = None,
    storage_options: Mapping[str, Any] | None = None,
    max_timezone_slots: int = 50,
    max_groups: int = 100,
)
```

| Argument | Meaning |
| --- | --- |
| `host` | Device IP or hostname. |
| `port` | TCP port, default `4370`. |
| `timeout` | Socket timeout in seconds. |
| `comm_key` | Device communication key. |
| `encoding` | Text encoding for names and IDs. |
| `transport` | Low-level transport override, mainly for tests. |
| `session` | Low-level session override, mainly for tests. |
| `storage` | Injected storage object; caller owns it. |
| `storage_backend` | Backend name used when storage is created lazily. |
| `storage_path` | File path or connection value for the backend. |
| `storage_options` | Backend options, such as `{"dsn": ...}`. |
| `max_timezone_slots` | Upper bound for `list_timezones()` scanning. |
| `max_groups` | Upper bound for `list_groups()` scanning. |

The constructor does **not** connect. It creates a `Session` unless you inject
one. `host`, `port`, `timeout`, and `comm_key` are used to construct that
session.

## Lifecycle

| Method | Returns | Notes |
| --- | --- | --- |
| `connect()` | `self` | Opens the socket and authenticates if required. Idempotent while connected. |
| `close()` | `None` | Closes the session and owned storage. Safe to call more than once. |
| `__enter__()` | `Device` | Calls `connect()`. |
| `__exit__()` | `None` | Calls `close()` even on error. |

```python
with Device("192.168.1.50", comm_key=0) as device:
    print(device.get_serial_number())
```

Manual lifecycle:

```python
device = Device("192.168.1.50", comm_key=0)
try:
    device.connect()
    print(device.get_device_info())
finally:
    device.close()
```

Do not share one `Device` across threads without external locking. The session
has mutable request and receive-buffer state.

## Device information

### `get_option(name: str) -> str`

Reads a device option. The SDK sends the option name followed by a NUL byte and
expects a `name=value` response. It returns the value after the first `=`.

```python
print(device.get_option("~Platform"))
print(device.get_option("~DeviceName"))
```

Option names are device-specific. The SDK uses `~Platform`, `~DeviceName`, and
`~SerialNumber` internally.

Raises `CommandError` if the device rejects the option, or `ProtocolError` if the
response has no value.

### `get_device_info() -> DeviceInfo`

Reads platform, device name, serial number, and firmware version. It performs
several commands: platform option, device name option, serial option, and
version.

```python
info = device.get_device_info()
print(info.platform, info.device_name, info.serial_number, info.firmware_version)
```

### `get_serial_number() -> str`

Reads the device serial through the `~SerialNumber` option and caches it on the
`Device` instance. Later calls return the cached value.

```python
serial = device.get_serial_number()
```

The serial scopes the mirror and block state. If the hardware changes, create a
new `Device` or clear the cached value by reconnecting a new instance.

## Users

### `list_users() -> list[User]`

Reads the full user buffer and parses 72-byte records. Returns an empty list if
the device returns no data. Device order is not guaranteed.

```python
users = device.list_users()
```

### `get_user(uid: int) -> User`

Reads all users and returns the one whose `uid` matches. Raises
`UserNotFoundError` if absent.

```python
user = device.get_user(295)
```

### `get_user_by_user_id(user_id: str) -> User`

Reads all users and returns the first whose `user_id` matches. Linear scan; not
an indexed lookup. Raises `UserNotFoundError` if absent.

```python
user = device.get_user_by_user_id("1001")
```

### `set_user(user: User) -> None`

Creates or replaces the user with `user.uid`. Sends the full 72-byte record.

- Raises `ValueError` if `uid` is outside `0`–`65535`.
- Create/read/delete have been exercised on hardware. Updating an existing
  user has not yet been hardware-validated; test it on a non-production device
  first.
- Raises `ValueError` if a string does not fit its fixed field.
- Raises `CommandError` if the device rejects the write.
- Calls `refresh_data()` after a successful acknowledgement.
- Does not read the record back to compare fields.

```python
user = device.get_user(295)
user.name = "Asha Rao"
device.set_user(user)
```

### `delete_user(uid: int) -> None`

Deletes the user with that UID.

- Raises `ValueError` if `uid` is outside `0`–`65535`.
- Raises `CommandError` if the device rejects the delete.
- Calls `refresh_data()` after success.
- Destructive; the SDK cannot undo it.

```python
device.delete_user(295)
```

## Fingerprints

### `list_fingerprints() -> list[FingerprintTemplate]`

Reads all fingerprint templates. Each item includes raw template bytes. This is
sensitive data.

```python
templates = device.list_fingerprints()
for item in templates:
    print(item.uid, item.fid, item.flag, item.size)
```

### `get_user_fingerprints(uid: int) -> list[FingerprintTemplate]`

Calls `list_fingerprints()` and filters by `uid` in Python.

```python
items = device.get_user_fingerprints(295)
```

There is no public enrollment or template-write API.

## Attendance

### `list_attendance() -> list[AttendanceRecord]`

Reads the device attendance count, then reads and parses the full attendance
buffer. Returns `[]` when the count is zero. Raises `ProtocolError` if the
record layout is not the expected 40-byte format.

```python
records = device.list_attendance()
```

There is no device-side date filter or pagination. The returned list is in
device order, not guaranteed chronological.

## Timezones

### `get_timezone(slot: int) -> TimeZone`

Reads one timezone slot. Raises `CommandError` if the device rejects the request;
the “not found” code is `0x1381`.

```python
timezone = device.get_timezone(1)
```

### `list_timezones() -> dict[int, TimeZone]`

Scans slots from `1` through `max_timezone_slots` (default `50`), skipping
`CommandError` with code `0x1381`. Other command errors propagate.

```python
timezones = device.list_timezones()
print(sorted(timezones))
```

### `set_timezone(timezone: TimeZone) -> None`

Writes a timezone slot, requires acknowledgement, and refreshes device data.

```python
from essl_f22 import DayInterval, TimeZone

timezone = TimeZone(
    slot=10,
    days=(DayInterval(9, 0, 17, 0),) * 7,
)
device.set_timezone(timezone)
```

## Groups

### `get_group(group_id: int) -> GroupInfo`

Reads one group. Raises `CommandError` if the device rejects the request.

```python
group = device.get_group(1)
```

### `list_groups() -> list[GroupInfo]`

Scans group IDs from `1` through `max_groups` (default `100`), skipping the
device's not-found code `0x1381`. Other command errors propagate.

```python
groups = device.list_groups()
```

### `set_group(group: GroupInfo) -> None`

Writes a group, requires acknowledgement, and refreshes device data.

```python
from essl_f22 import GroupInfo

device.set_group(
    GroupInfo(
        group_id=1,
        tz1=1,
        tz2=0,
        tz3=0,
        verify_style=0,
        holiday_enabled=False,
    )
)
```

## User timezone assignment

### `get_user_timezone(uid: int) -> UserTimeZone`

Reads the device's per-user assignment.

```python
assignment = device.get_user_timezone(295)
print(assignment.use_personal, assignment.tz1, assignment.tz2, assignment.tz3)
```

### `set_user_timezone(uid: int, timezone: UserTimeZone) -> None`

Writes the per-user assignment, requires acknowledgement, and refreshes data.
The SDK canonicalizes the assignment first: when `use_personal` is false, the
timezone fields are cleared. It does not read the record back for comparison;
call `get_user_timezone()` if you need verification.

```python
from essl_f22 import UserTimeZone

device.set_user_timezone(
    295,
    UserTimeZone(uid=295, use_personal=True, tz1=10),
)
```

## Capacity and time

### `get_free_sizes() -> FreeSizes`

Reads device counts and capacities.

```python
sizes = device.get_free_sizes()
print(sizes.users, sizes.users_capacity)
print(sizes.fingerprints, sizes.fingerprints_capacity)
print(sizes.attendance, sizes.attendance_capacity)
```

The device response is parsed with a 20-integer layout; a response shorter than
80 bytes raises `ProtocolError`.

### `get_time() -> datetime`

Returns the device's local time as a naive `datetime`.

```python
print(device.get_time())
```

### `set_time(value: datetime) -> None`

Writes the device time. This is a write and can affect attendance and schedules.

```python
from datetime import datetime

device.set_time(datetime(2026, 10, 24, 9, 30, 0))
```

### `refresh_data() -> None`

Asks the device to refresh its internal data. Called automatically after
successful writes.

```python
device.refresh_data()
```

## Blocking

### `block_user(uid: int) -> BlockResult`

Blocks a user by assigning a deny-all timezone. Non-destructive: the user and
templates remain. Unit-tested with fake transports; not yet validated against a
physical door or production access policy.

```python
result = device.block_user(295)
print(result.already_blocked, result.block_timezone_slot, result.original)
```

Raises:

- `UserNotFoundError` if the user is absent;
- `NoFreeTimeZoneSlotError` if no eligible slot exists;
- `DeviceVerificationError` if the read-back fails;
- `CommandError` or storage errors from underlying operations.

See [Access control and blocking](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/access-control.md).

### `unblock_user(uid: int) -> UnblockResult`

Restores the saved assignment, or disables personal scheduling if no state is
saved.

```python
result = device.unblock_user(295)
print(result.restored, result.state_found)
```

### `is_user_blocked(uid: int) -> bool`

Reads the current user assignment and compares it with the saved block slot.
Returns `False` if no block slot is recorded for the device.

```python
print(device.is_user_blocked(295))
```

### `get_blocked_users() -> list[int]`

Lists UIDs from the **state store**, not a device scan.

```python
print(device.get_blocked_users())
```

## Mirror and sync

### `mirror() -> Mirror`

Returns a read-only mirror for the current device serial. Creates storage lazily.

```python
mirror = device.mirror()
```

### `sync(mode: SyncMode = "incremental") -> SyncResult`

Syncs the device into the mirror. `mode` is `"full"` or `"incremental"`.

```python
result = device.sync("full")
print(result.attendance, result.new_attendance, result.attendance_replaced)
```

`"full"` replaces all collections and attendance. `"incremental"` replaces
non-attendance collections, inserts new attendance keys, and replaces attendance
if the device count dropped.

Raises `SyncError` for an unsupported mode or a serial mismatch.

## Method summary

| Method | Kind | Returns |
| --- | --- | --- |
| `connect` | lifecycle | `Device` |
| `close` | lifecycle | `None` |
| `get_option` | read | `str` |
| `get_device_info` | read | `DeviceInfo` |
| `get_serial_number` | read/cached | `str` |
| `list_users` | read | `list[User]` |
| `get_user` | read | `User` |
| `get_user_by_user_id` | read | `User` |
| `set_user` | write | `None` |
| `delete_user` | destructive write | `None` |
| `list_fingerprints` | read | `list[FingerprintTemplate]` |
| `get_user_fingerprints` | read | `list[FingerprintTemplate]` |
| `list_attendance` | read | `list[AttendanceRecord]` |
| `get_timezone` | read | `TimeZone` |
| `list_timezones` | read scan | `dict[int, TimeZone]` |
| `set_timezone` | write | `None` |
| `get_group` | read | `GroupInfo` |
| `list_groups` | read scan | `list[GroupInfo]` |
| `set_group` | write | `None` |
| `get_user_timezone` | read | `UserTimeZone` |
| `set_user_timezone` | write | `None` |
| `get_free_sizes` | read | `FreeSizes` |
| `get_time` | read | `datetime` |
| `set_time` | write | `None` |
| `refresh_data` | device command | `None` |
| `block_user` | reversible write | `BlockResult` |
| `unblock_user` | reversible write | `UnblockResult` |
| `is_user_blocked` | read | `bool` |
| `get_blocked_users` | state read | `list[int]` |
| `mirror` | local read | `Mirror` |
| `sync` | read + storage write | `SyncResult` |

## Next

- [Models](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/models.md)
- [Errors](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/errors.md)
- [Storage](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/storage.md)

---

### From [docs/reference/models.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/models.md)

# Models

## Why this matters

The models are the typed boundary between binary device records and your
application. If you know which fields exist, which are mutable, and which are
validated only at write time, you can avoid both silent field loss and invalid
device records.

Most models are frozen value objects. `User` is the important exception: it is
mutable so you can read, modify, and write it back.

## `User`

```python
@dataclass(slots=True)
class User:
    uid: int
    user_id: str
    name: str = ""
    privilege: int = 0
    password: str = ""
    card: int = 0
    group_id: int = 1
    timezone_flag: int = 0
    tz1: int = 0
    tz2: int = 0
    tz3: int = 0
```

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `uid` | `int` | required | Internal slot; `0`–`65535` enforced by `set_user()` and `delete_user()`. |
| `user_id` | `str` | required | Up to 23 encoded bytes. |
| `name` | `str` | `""` | Up to 23 encoded bytes. |
| `privilege` | `int` | `0` | Device-specific. |
| `password` | `str` | `""` | Up to 7 encoded bytes. |
| `card` | `int` | `0` | Unsigned 32-bit field. |
| `group_id` | `int` | `1` | Group membership. |
| `timezone_flag` | `int` | `0` | Personal schedule flag in the user record. |
| `tz1`–`tz3` | `int` | `0` | Personal timezone slots in the user record. |

`User` is **mutable**. It is not frozen.

### `User.from_record(data: bytes, encoding: str = "utf-8") -> User`

Decodes exactly 72 bytes. Raises `ProtocolError` if the length is not 72.

### `User.to_record(encoding: str = "utf-8") -> bytes`

Encodes exactly 72 bytes. Raises `ValueError` if an encoded string does not fit
its fixed field.

The wire layout is `<HB8s24sIBHHHH24s`:

```text
uid, privilege, password, name, card, group_id,
timezone_flag, tz1, tz2, tz3, user_id
```

The total is 72 bytes.

### Validation timing

`User(uid=70000, ...)` can be constructed. The UID range is checked when you call
`set_user()` or `delete_user()`. String length is checked when `to_record()` is
called, which `set_user()` does.

Do not confuse “the object was constructed” with “the record is valid for the
device”.

## `AttendanceRecord`

```python
@dataclass(frozen=True, slots=True)
class AttendanceRecord:
    uid: int
    user_id: str
    timestamp: datetime
    status: int
    punch: int
```

Frozen. The device record is 40 bytes.

| Field | Meaning |
| --- | --- |
| `uid` | Internal user slot at punch time. |
| `user_id` | User identifier at punch time. |
| `timestamp` | Naive device-local time. |
| `status` | Device status code; not interpreted by the SDK. |
| `punch` | Device punch/verify value; not interpreted by the SDK. |

There is no timezone attached to `timestamp`.

## `FingerprintTemplate`

```python
@dataclass(frozen=True, slots=True)
class FingerprintTemplate:
    uid: int
    fid: int
    flag: int
    template: bytes

    @property
    def size(self) -> int:
        return len(self.template) + 6
```

Frozen. `size` includes the 6-byte device entry header. The `template` bytes are
sensitive and proprietary; the SDK does not decode them.

## `DayInterval`

```python
@dataclass(frozen=True, slots=True)
class DayInterval:
    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int
```

`allows(value: datetime) -> bool`:

- returns `False` if `(start_hour, start_minute) >= (end_hour, end_minute)`;
- otherwise compares the value's hour/minute, with **inclusive** start and end.

Examples:

```python
DayInterval(9, 0, 17, 0).allows(datetime(2026, 10, 24, 9, 0))  # True
DayInterval(9, 0, 17, 0).allows(datetime(2026, 10, 24, 17, 0))  # True
DayInterval(9, 0, 17, 0).allows(datetime(2026, 10, 24, 17, 1))  # False
DayInterval(0, 0, 0, 0).allows(datetime(2026, 10, 24, 12, 0))  # False
```

The model does not support an interval that crosses midnight. A start at or
after the end is treated as deny-all for that day.

## `TimeZone`

```python
@dataclass(frozen=True, slots=True)
class TimeZone:
    slot: int
    days: tuple[DayInterval, ...]
```

Frozen. `days` holds seven intervals, one per weekday.

### `TimeZone.from_response(data: bytes) -> TimeZone`

Decodes exactly 32 bytes: a 2-byte slot plus seven 4-byte day intervals. Raises
`ProtocolError` if the length is not 32.

### `TimeZone.to_request() -> bytes`

Encodes the slot and seven intervals into 32 bytes.

### `is_default_allow_all() -> bool`

True when every day is exactly `00:00–23:59`.

### `is_deny_all() -> bool`

True when every day has start greater than or equal to end.

The blocking manager uses these helpers to choose and validate slots.

## `GroupInfo`

```python
@dataclass(frozen=True, slots=True)
class GroupInfo:
    group_id: int
    tz1: int
    tz2: int
    tz3: int
    verify_style: int
    holiday_enabled: bool
```

Frozen. Encodes to 8 bytes.

- `verify_style` is `flags & 0x7F` on decode.
- `holiday_enabled` is bit `0x80` of the same flags byte.
- `tz1`–`tz3` are timezone slot references.

## `UserTimeZone`

```python
@dataclass(frozen=True, slots=True)
class UserTimeZone:
    uid: int
    use_personal: bool
    tz1: int = 0
    tz2: int = 0
    tz3: int = 0
```

Frozen. Represents the device's per-user timezone assignment, separate from the
`User` record fields.

### `canonical() -> UserTimeZone`

- if `use_personal` is true, returns `self`;
- if false, returns a copy with `use_personal=False` and all timezone fields
  cleared.

`unblock_user()` uses this to avoid restoring meaningless timezone values when
personal scheduling is disabled.

## `DeviceInfo`

```python
@dataclass(frozen=True, slots=True)
class DeviceInfo:
    platform: str
    device_name: str
    serial_number: str
    firmware_version: str
```

Frozen. Values come from device options and the version command.

## `FreeSizes`

```python
@dataclass(frozen=True, slots=True)
class FreeSizes:
    users: int
    fingerprints: int
    attendance: int
    users_capacity: int
    fingerprints_capacity: int
    attendance_capacity: int
```

Frozen. `users`, `fingerprints`, and `attendance` are current counts; the
`*_capacity` fields are device limits.

## Blocking result models

### `BlockResult`

```python
@dataclass(frozen=True, slots=True)
class BlockResult:
    uid: int
    user_id: str
    already_blocked: bool
    block_timezone_slot: int
    original: UserTimeZone
```

`original` is the assignment the SDK intended to save. On an idempotent block,
it is the saved original when available.

### `UnblockResult`

```python
@dataclass(frozen=True, slots=True)
class UnblockResult:
    uid: int
    user_id: str
    restored: UserTimeZone
    state_found: bool
```

`state_found=False` means the SDK had no saved original and used the fallback
non-personal assignment.

## Storage models

### `FingerprintMetadata`

```python
@dataclass(frozen=True, slots=True)
class FingerprintMetadata:
    uid: int
    fid: int
    flag: int
    size: int
```

The mirror stores this instead of template bytes.

### `BlockTimeZoneState`

```python
@dataclass(frozen=True, slots=True)
class BlockTimeZoneState:
    slot: int
```

The saved deny-all slot for a device serial.

### `AttendanceEntry`

```python
@dataclass(frozen=True, slots=True)
class AttendanceEntry:
    record_key: str
    record: AttendanceRecord
```

Used when writing attendance to storage. `record_key` is normally the stable
SHA-256 hash.

### `SyncMode`

```python
SyncMode = Literal["full", "incremental"]
```

### `SyncState`

```python
@dataclass(frozen=True, slots=True)
class SyncState:
    device_serial: str
    synced_at: datetime
    mode: SyncMode
    users: int
    groups: int
    timezones: int
    fingerprints: int
    attendance: int
```

Stored after a sync. `synced_at` is local time, not device time.

### `SyncResult`

```python
@dataclass(frozen=True, slots=True)
class SyncResult:
    device_serial: str
    mode: SyncMode
    synced_at: datetime
    users: int
    groups: int
    timezones: int
    fingerprints: int
    attendance: int
    new_attendance: int
    attendance_replaced: bool
```

Returned by `Device.sync()` and `Mirror.sync()`.

### `MirrorSnapshot`

```python
@dataclass(frozen=True, slots=True)
class MirrorSnapshot:
    device_info: DeviceInfo | None
    users: tuple[User, ...]
    groups: tuple[GroupInfo, ...]
    timezones: dict[int, TimeZone]
    fingerprints: tuple[FingerprintMetadata, ...]
    attendance: tuple[AttendanceRecord, ...]
    sync_state: SyncState | None
```

Loaded by `Mirror.snapshot()`. This can be large because it includes all
attendance.

## Next

- [Device API](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/device-api.md)
- [Errors](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/errors.md)
- [Storage](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/storage.md)

---

### From [docs/reference/errors.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/errors.md)

# Errors

## Why this matters

The exception type tells you whether to retry, ask for credentials, fix a
configuration, or stop before making the situation worse. Catching the base
class is useful at the outermost boundary; catching only the base class inside
recovery code hides the information you need.

## Hierarchy

```text
ESSL22Error
├── DeviceConnectionError
├── DeviceAuthenticationError
├── DeviceTimeoutError
├── ProtocolError
├── CommandError
├── DeviceVerificationError
├── UserNotFoundError
├── NoFreeTimeZoneSlotError
└── StorageError
    ├── StorageConfigurationError
    ├── MirrorRecordNotFoundError
    ├── SyncError
    └── StateStoreError
```

## `ESSL22Error`

Base class for every SDK-defined error.

```python
from essl_f22 import ESSL22Error

try:
    ...
except ESSL22Error as exc:
    log.error("SDK failure: %s: %s", type(exc).__name__, exc)
```

Use this at a process or request boundary. Do not use it as a substitute for
handling known failures where the correct action differs.

## Device errors

### `DeviceConnectionError`

The socket could not be opened, the connection was lost, or the transport is not
usable.

Typical causes:

- wrong host or port;
- device powered off;
- firewall or VLAN block;
- connection closed by the device;
- using a closed transport.

Retryable for reads, with a bounded policy. Investigate before retrying writes.

### `DeviceTimeoutError`

A connect or command exceeded the socket timeout.

A timeout is ambiguous for writes: the device may have received and applied the
command before the response was lost. Read the current state before retrying.

### `DeviceAuthenticationError`

The device rejected the communication key or returned an unexpected connect
response.

Do not brute force the key. Ask the device administrator. Repeated failures can
be a security event.

### `ProtocolError`

A response was malformed, truncated, had invalid framing, or did not match the
expected record layout.

Common causes:

- unsupported firmware;
- a non-F22 device speaking a different dialect;
- a dropped or interleaved connection;
- an unexpected buffer size.

Capture the device model and firmware. Do not loop retries; a deterministic
protocol mismatch will not heal.

### `CommandError`

The device returned a non-success command status.

```python
from essl_f22 import CommandError

try:
    device.delete_user(295)
except CommandError as exc:
    print(f"device code: 0x{exc.code:04X}")
    print("message:", exc)
```

Attributes:

| Attribute | Meaning |
| --- | --- |
| `code` | Integer command/status code returned by the device. |
| `args[0]` | Human-readable message, if supplied. |

The not-found code `0x1381` is handled internally by `list_timezones()` and
`list_groups()`, which skip it. A direct `get_timezone()` or `get_group()` call
can still raise `CommandError` with that code.

### `DeviceVerificationError`

A block or unblock read-back did not match the intended assignment.

For a block, the manager attempts to restore the original assignment before
raising. If that restore also fails, the error message says so. For an unblock,
the manager raises without a second automatic change.

Always re-read the user's assignment after catching this error.

### `UserNotFoundError`

The requested UID or user ID does not exist.

```python
from essl_f22 import UserNotFoundError

try:
    user = device.get_user(295)
except UserNotFoundError:
    print("no such user")
```

`Mirror.get_user()` also raises `UserNotFoundError` when the mirror has no such
user.

### `NoFreeTimeZoneSlotError`

The blocking manager could not find a free default-allow-all timezone slot that
is unreferenced by groups and personal schedules.

This is a capacity/configuration problem, not a transient network problem.
Free a slot or choose another access-control method.

## Storage errors

### `StorageError`

Base class for storage failures. Catch a subclass when the response differs.

### `StorageConfigurationError`

The backend name is unknown, a required driver is missing, or a connection
value is missing/invalid.

Examples:

- `storage_backend="postgres"` without the `postgres` extra;
- an external backend without a DSN/URI/URL;
- a MySQL DSN without a database;
- a MongoDB URI without a database;
- an invalid Redis URL.

This is a configuration error. Fix it; do not retry the same call unchanged.

### `StateStoreError`

Block state could not be read or written, or a local SQLite/JSON store could not
be initialized.

Typical causes:

- permissions;
- disk full;
- corrupt JSON;
- unsupported JSON format version;
- SQLite open failure;
- closed external storage.

A `StateStoreError` during blocking is serious: the device may have changed even
though the state was not saved. Stop and inspect.

### `MirrorRecordNotFoundError`

A mirror timezone or group record is absent.

```python
from essl_f22 import MirrorRecordNotFoundError

try:
    timezone = mirror.get_timezone(99)
except MirrorRecordNotFoundError:
    print("slot 99 is not in the mirror")
```

`Mirror.get_user()` uses `UserNotFoundError` instead.

### `SyncError`

A sync could not be performed:

- unsupported mode (anything other than `"full"` or `"incremental"`);
- the device serial does not match the mirror serial.

This is usually a programming or targeting error. Fix the mode or use the
correct mirror.

## Non-SDK exceptions

The SDK can also raise standard Python exceptions:

| Exception | Cause |
| --- | --- |
| `ValueError` | UID outside `0`–`65535`, or an encoded user field does not fit. |
| `TypeError` | Wrong argument type or unsupported value. |
| `OSError` | Underlying socket/file problem not wrapped by the SDK. |

Do not catch `ValueError` as if it were a device failure. It usually means the
input is invalid.

## Retry matrix

| Error | Retry reads? | Retry writes? |
| --- | --- | --- |
| `DeviceConnectionError` | Yes, bounded backoff | Verify first; then decide |
| `DeviceTimeoutError` | Yes, bounded backoff | Verify first; then decide |
| `DeviceAuthenticationError` | No | No |
| `ProtocolError` | No | No |
| `CommandError` | No, unless the request/state changed | No, unless the request/state changed |
| `DeviceVerificationError` | Re-read state | Only after re-reading state |
| `UserNotFoundError` | No | No |
| `NoFreeTimeZoneSlotError` | No | Free a slot first |
| `StorageConfigurationError` | No | No |
| `StateStoreError` | Fix storage first | Fix storage first |
| `MirrorRecordNotFoundError` | Re-sync or use another slot | Not a write path |
| `SyncError` | Fix mode/serial | Not a write path |

## Logging exceptions

Log the type, message, and operation. For `CommandError`, log the code. Do not
log:

- the communication key;
- database passwords or full DSNs;
- fingerprint template bytes;
- full user or attendance records unless approved.

```python
import logging

from essl_f22 import CommandError, ESSL22Error

log = logging.getLogger(__name__)

try:
    ...
except CommandError as exc:
    log.error("device command failed code=0x%04X", exc.code)
except ESSL22Error as exc:
    log.error("sdk failure type=%s message=%s", type(exc).__name__, exc)
```

## Next

- [Handle errors](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/handle-errors.md)
- [Troubleshooting](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/troubleshooting.md)
- [Device API](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/device-api.md)

---

### From [docs/reference/storage.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/storage.md)

# Storage

## Why this matters

Storage holds two different kinds of data:

- the **mirror**: a read-only copy of device records;
- the **block state**: the only copy of each blocked user's original access
  assignment.

Losing the mirror hurts reporting. Losing block state can prevent a correct
unblock. They may share a SQLite file, but they do not have the same recovery
requirements.

For choosing a backend, start with [Choose storage](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/choose-storage.md).

## `create_storage`

```python
from essl_f22 import create_storage

storage = create_storage(
    backend="sqlite",
    path="data/essl.db",
)
```

Signature:

```text
create_storage(
    backend: str = "sqlite",
    *,
    path: Path | str | None = None,
    options: Mapping[str, Any] | None = None,
) -> StorageBackend
```

| Backend name | Aliases | Required value |
| --- | --- | --- |
| `sqlite` | none | `path` optional; default `default_state_path()` |
| `json` | none | `path` optional; default `default_mirror_path()` |
| `memory` | none | none |
| `postgres` | `postgresql` | `options["dsn"]` or `path` |
| `mysql` | none | `options["dsn"]` or `path` |
| `mongo` | `mongodb` | `options["uri"]` or `path` |
| `redis` | none | `options["url"]` or `path` |

Names are case-insensitive. An unknown name raises
`StorageConfigurationError`.

For external backends, `options` takes precedence over `path`:

```python
storage = create_storage(
    "postgres",
    path="postgresql://ignored",
    options={"dsn": "postgresql://used@db/app"},
)
```

## Backend classes

All of these are exported from `essl_f22`:

| Class | Constructor |
| --- | --- |
| `SqliteStorage` | `SqliteStorage(path)` |
| `JsonFileStorage` | `JsonFileStorage(path)` |
| `MemoryStorage` | `MemoryStorage()` |
| `PostgresStorage` | `PostgresStorage(dsn)` |
| `MysqlStorage` | `MysqlStorage(dsn)` |
| `MongoStorage` | `MongoStorage(uri)` |
| `RedisStorage` | `RedisStorage(url)` |

`SqliteStorage(":memory:")` is supported and creates a process-local SQLite
database.

## `StorageBackend` protocol

`StorageBackend` combines the block-state and mirror protocols and adds
`close()`.

```python
class StorageBackend(BlockStateStore, MirrorStore, Protocol):
    def close(self) -> None: ...
```

A custom object can be passed as `Device(..., storage=...)` if it implements the
methods the device actually calls. For blocking and mirroring, that means the
full protocol below.

### Block-state methods

| Method | Purpose |
| --- | --- |
| `get_original_user_timezone(serial, uid)` | Read the saved original assignment. |
| `save_original_user_timezone(serial, uid, timezone)` | Save it before blocking. |
| `delete_original_user_timezone(serial, uid)` | Remove it after unblocking. |
| `list_blocked_uids(serial)` | List UIDs with saved state. |
| `get_block_timezone(serial)` | Read the saved deny-all slot. |
| `save_block_timezone(serial, slot)` | Save the deny-all slot. |

### Mirror methods

| Method | Purpose |
| --- | --- |
| `save_device_info(serial, info)` | Store device info. |
| `get_device_info(serial)` | Read device info. |
| `replace_users(serial, users)` | Replace all users. |
| `list_users(serial)` | List users. |
| `get_user(serial, uid)` | Read one user or `None`. |
| `replace_groups(serial, groups)` | Replace all groups. |
| `list_groups(serial)` | List groups. |
| `get_group(serial, group_id)` | Read one group or `None`. |
| `replace_timezones(serial, timezones)` | Replace all timezone slots. |
| `list_timezones(serial)` | Return slots as a dict. |
| `get_timezone(serial, slot)` | Read one slot or `None`. |
| `replace_fingerprints(serial, fingerprints)` | Replace metadata only. |
| `list_fingerprints(serial)` | List metadata. |
| `upsert_attendance(serial, entries)` | Insert new attendance keys; return new count. |
| `replace_attendance(serial, entries)` | Replace all attendance. |
| `list_attendance(serial, *, uid, since, until, limit)` | Query attendance. |
| `attendance_count(serial)` | Count stored attendance. |
| `save_sync_state(serial, state)` | Store sync metadata. |
| `get_sync_state(serial)` | Read sync metadata. |
| `clear_device(serial)` | Remove a device's stored data. |

`clear_device()` removes a device's mirror data and is part of the
`MirrorStore` protocol. Treat it as a destructive maintenance operation and
test it before use.

## Backend details

### SQLite

- Durable local file; the default backend.
- Each operation opens a SQLite connection.
- Creates a `documents` table with `(namespace, key)` as the primary key.
- `:memory:` is process-local and disappears when the connection closes.
- Subject to normal SQLite locking and filesystem behaviour.

### JSON

- Loads the entire file at construction and rewrites it on each change.
- Stores a top-level object with `version` and `namespaces`.
- Unsupported format versions, invalid JSON, or invalid records raise
  `StateStoreError`.
- Not designed for multiple concurrent writers.
- Loads the whole snapshot into memory.

### Memory

- Process-local dictionaries.
- Lost on exit.
- `close()` does nothing.
- Use for tests and short-lived demos.

### PostgreSQL

- Requires `psycopg` from the `postgres` extra.
- Creates a `documents` table with `(namespace, key_name)` as the primary key.
- Accepts a psycopg-compatible DSN.
- Opens a new connection per operation.
- Missing driver or connection value raises `StorageConfigurationError`.

### MySQL

- Requires `pymysql` from the `mysql` extra.
- DSN must include a database name.
- Accepts `mysql://` and `mysql+pymysql://` schemes.
- Creates a `documents` table with `(namespace, key_name)` as the primary key.
- Uses `utf8mb4`.
- Opens a new connection per operation.

### MongoDB

- Requires `pymongo` from the `mongo` extra.
- URI must include a database.
- Uses a `documents` collection with a unique `(namespace, key_name)` index.
- Sets a 5-second server-selection timeout.
- Missing driver or invalid URI raises `StorageConfigurationError`.

### Redis

- Requires `redis` from the `redis` extra.
- Uses hashes named `essl_f22:documents:<namespace>`.
- Pings the server at construction.
- `close()` closes the client.
- Durability depends on the Redis configuration; verify persistence and
  eviction before using it for data you cannot lose.

## Default paths

```python
from essl_f22 import default_data_dir, default_mirror_path, default_state_path

print(default_data_dir())
print(default_state_path())
print(default_mirror_path())
```

| Function | Result |
| --- | --- |
| `default_data_dir()` | Platform application-data directory for `essl_f22`. |
| `default_state_path()` | `state.db` inside that directory. |
| `default_mirror_path()` | `mirror.json` inside that directory. |

Platform bases:

- Windows: `%LOCALAPPDATA%\essl_f22` (or `~/AppData/Local/essl_f22`);
- macOS: `~/Library/Application Support/essl_f22`;
- Linux: `$XDG_DATA_HOME/essl_f22` or `~/.local/share/essl_f22`.

## Storage ownership

- `Device` creates storage lazily if you do not inject it.
- `Device.close()` closes owned storage.
- Injected storage is not closed by `Device`.
- `create_storage()` returns an object you own; close it yourself.

```python
from essl_f22 import SqliteStorage

storage = SqliteStorage("shared.db")
try:
    ...
finally:
    storage.close()
```

## Document format

The built-in backends store JSON documents in namespaces keyed by device serial
and record identity. The JSON file also has a format version.

This is an implementation detail, not a stable public API. Do not write or
migrate `documents` rows by hand unless you have read the code and tested the
change. Use `Device.sync()` to populate a new backend instead of copying rows
between database products.

## What storage does not do

- It does not write data back to a device.
- It does not store fingerprint template bytes.
- It stores full user records, including device user password fields. Protect
  it as a credential store.
- It does not encrypt data for you. Use filesystem/database encryption and
  access controls.
- It does not provide retention or deletion policy.
- It does not make a sync atomic across collections.
- It does not add cross-process locking beyond the underlying backend.

## Environment variables

The SDK runtime does not read storage connection values from environment
variables automatically. Pass them explicitly.

The test suite reads:

```text
ESSL_F22_POSTGRES_DSN
ESSL_F22_MYSQL_DSN
ESSL_F22_MONGO_URI
ESSL_F22_REDIS_URL
```

for the opt-in storage contract tests.

## Errors

| Error | When |
| --- | --- |
| `StorageConfigurationError` | Unknown backend, missing driver, missing/invalid connection value. |
| `StateStoreError` | Local file, SQLite, JSON, or state operation failed. |
| `StorageError` | Base class for storage failures. |
| `MirrorRecordNotFoundError` | A mirror timezone/group record is absent. |
| `SyncError` | Unsupported mode or serial mismatch. |

See [Errors](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/errors.md).

## Next

- [Choose storage](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/choose-storage.md)
- [Mirror and storage](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/mirror-and-storage.md)
- [Models](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/models.md#storage-models)

---

### From [docs/reference/protocol.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/protocol.md)

# Protocol internals

## Why this matters

Most users never need this page. It exists for maintainers, test authors, and
integrators who need to understand a malformed response, a firmware difference,
or a captured packet. The protocol modules are public Python modules, but the
wire details are **not** a stable compatibility promise.

Use `Device` for application code. Use this page to diagnose and extend, not to
replace the high-level API casually.

## Transport

- TCP, default port `4370`.
- No TLS and no SDK-added encryption.
- Frames are little-endian.
- The device can close the connection at any time.

Run the protocol only on a trusted, segmented network.

## Frame layout

A frame begins with an 8-byte TCP header:

| Field | Size | Value/meaning |
| --- | --- | --- |
| `magic_1` | 2 | `0x5050` |
| `magic_2` | 2 | `0x7D82` |
| `payload_length` | 4 | Length of the payload that follows |

The payload starts with an 8-byte command header:

| Field | Size | Meaning |
| --- | --- | --- |
| `command` | 2 | Command/status code. |
| `checksum` | 2 | ZKTeco-style checksum. |
| `session_id` | 2 | Device-assigned session. |
| `reply_id` | 2 | Reply sequence. |
| `data` | variable | Command-specific bytes. |

`payload_length` is `8 + len(data)`. A complete frame is
`8 + payload_length` bytes.

```python
from essl_f22.protocol import build_frame, parse_frame

frame, next_reply_id = build_frame(
    command=1000,
    data=b"",
    session_id=0,
    reply_id=0xFFFE,
)
response = parse_frame(frame)
```

`build_frame()` advances the reply ID for the next request. `parse_frame()`
validates the magic, minimum payload length, and exact frame length.

## Checksum

`checksum(payload)` computes a one's-complement checksum over 16-bit
little-endian words:

1. Sum each pair of bytes as a 16-bit word.
2. Fold carries above `0xFFFF`.
3. Add a trailing odd byte if present.
4. Fold again.
5. Invert the result and normalize it to the 16-bit range.

The checksum is used when building frames. Do not invent a different checksum
for a custom command and expect the device to accept it.

## Commands

| Constant | Value | Used for |
| --- | ---: | --- |
| `CMD_USER_WRQ` | 8 | Write a user record. |
| `CMD_USERTEMP_RRQ` | 9 | Read users or fingerprint templates, selected by `fct`. |
| `CMD_OPTIONS_RRQ` | 11 | Read a device option. |
| `CMD_ATTLOG_RRQ` | 13 | Read attendance. |
| `CMD_DELETE_USER` | 18 | Delete a user. |
| `CMD_USERGRP_RRQ` | 21 | User-group read (defined constant). |
| `CMD_USERGRP_WRQ` | 22 | User-group write (defined constant). |
| `CMD_USERTZ_RRQ` | 23 | Read a user-timezone assignment. |
| `CMD_USERTZ_WRQ` | 24 | Write a user-timezone assignment. |
| `CMD_GRPTZ_RRQ` | 25 | Read a group. |
| `CMD_GRPTZ_WRQ` | 26 | Write a group. |
| `CMD_TZ_RRQ` | 27 | Read a timezone slot. |
| `CMD_TZ_WRQ` | 28 | Write a timezone slot. |
| `CMD_GET_FREE_SIZES` | 50 | Read counts and capacities. |
| `CMD_VERIFY_RRQ` | 80 | Verify (defined constant). |
| `CMD_GET_TIME` | 201 | Read device time. |
| `CMD_SET_TIME` | 202 | Write device time. |
| `CMD_CONNECT` | 1000 | Open a session. |
| `CMD_EXIT` | 1001 | Exit (defined constant). |
| `CMD_ENABLEDEVICE` | 1002 | Enable device (defined constant). |
| `CMD_DISABLEDEVICE` | 1003 | Disable device (defined constant). |
| `CMD_REFRESHDATA` | 1013 | Ask the device to refresh data. |
| `CMD_GET_VERSION` | 1100 | Read firmware version. |
| `CMD_AUTH` | 1102 | Authenticate with the communication key. |
| `CMD_PREPARE_DATA` | 1500 | Prepared-data response. |
| `CMD_DATA` | 1501 | Data response. |
| `CMD_FREE_DATA` | 1502 | Release the device buffer. |
| `CMD_DATA_WRRQ` | 1503 | Request a buffered read. |
| `CMD_DATA_RDY` | 1504 | Read a chunk. |
| `CMD_ACK_OK` | 2000 | Success. |
| `CMD_ACK_ERROR` | 2001 | Generic error. |
| `CMD_ACK_UNAUTH` | 2005 | Authentication required/failed. |

## Connection and authentication

The session starts with `CMD_CONNECT` at session ID `0` and a starting reply ID
of `0xFFFE`.

If the response is `CMD_ACK_OK`, the session ID is accepted and the session is
connected.

If the response is `CMD_ACK_UNAUTH`, the device requires a communication key.
The SDK sends `CMD_AUTH` with the encoded key. A non-OK response raises
`DeviceAuthenticationError`.

The key encoding (`make_comm_key`) is firmware-specific:

- reverse the key bits;
- add the session ID;
- XOR the resulting bytes with `Z`, `K`, `S`, `O`;
- swap the two 16-bit words;
- replace the third byte with the tick byte (`50` in the SDK) and XOR the
  other three bytes with that tick byte.

This is a shared-secret handshake, not strong authentication.

## Buffered reads

Large buffers are read through a request/chunk/free sequence:

1. Send `CMD_DATA_WRRQ` with `struct.pack("<bhii", 1, command, fct, ext)`.
2. If the response is `CMD_DATA`, the data is returned directly.
3. Otherwise, read the total size from the response:
   - 5 bytes if the first byte is `0` (size in bytes 1–4);
   - otherwise 4 bytes.
4. Repeatedly send `CMD_DATA_RDY` with `(start, size)`.
5. Accept `CMD_DATA` or a prepared-data sequence (`CMD_PREPARE_DATA` followed by
   `CMD_DATA` frames and a final `CMD_ACK_OK`).
6. Verify each chunk length.
7. Send `CMD_FREE_DATA` in a `finally` block.

Chunks are capped at `MAX_CHUNK = 0xFFC0`.

The `fct` value selects the data family. The device API uses:

- `CMD_USERTEMP_RRQ` with `fct=5` for users;
- `CMD_USERTEMP_RRQ` with `fct=2` for fingerprint templates;
- `CMD_ATTLOG_RRQ` for attendance.

## Record formats

### User record

72 bytes, little-endian:

```text
<HB8s24sIBHHHH24s
```

| Field | Type |
| --- | --- |
| `uid` | `uint16` |
| `privilege` | `uint8` |
| `password` | 8 bytes |
| `name` | 24 bytes |
| `card` | `uint32` |
| `group_id` | `uint16` |
| `timezone_flag` | `uint16` |
| `tz1` | `uint16` |
| `tz2` | `uint16` |
| `tz3` | `uint16` |
| `user_id` | 24 bytes |

Fixed strings are NUL-padded and decoded up to the first NUL. Encoding rejects
values that do not leave room for at least one NUL byte.

### Attendance record

40 bytes, little-endian:

```text
<H24sB4sB8s
```

| Field | Type |
| --- | --- |
| `uid` | `uint16` |
| `user_id` | 24 bytes |
| `status` | `uint8` |
| `timestamp` | 4-byte packed time |
| `punch` | `uint8` |
| reserved | 8 bytes |

The parser removes a known 9-byte attendance prefix if present. It uses the
device's attendance count to confirm the record size is 40 before parsing.

### Fingerprint entry

6-byte header followed by template bytes:

```text
<HHBB
```

| Field | Type |
| --- | --- |
| `size` | `uint16` (total entry size, including the 6-byte header) |
| `uid` | `uint16` |
| `fid` | `uint8` |
| `flag` | `uint8` |

The template payload is `size - 6` bytes.

### Timezone record

32 bytes: a 2-byte slot followed by seven 4-byte day intervals. Each interval is
`<BBBB` (`start_hour`, `start_minute`, `end_hour`, `end_minute`).

### Group record

8 bytes: `<BHHHB` (`group_id`, `tz1`, `tz2`, `tz3`, flags). The flags byte holds
`verify_style` in the low 7 bits and `holiday_enabled` in bit `0x80`.

### User-timezone record

The response is 8 bytes: `<HHHH` (`flag`, `tz1`, `tz2`, `tz3`). The request is
20 bytes: `<IIIII` (`uid`, personal flag, `tz1`, `tz2`, `tz3`).

### Free sizes

At least 80 bytes, parsed as `<20i`. The high-level API maps:

| Field | Index |
| --- | ---: |
| `users` | 4 |
| `fingerprints` | 6 |
| `attendance` | 8 |
| `users_capacity` | 15 |
| `fingerprints_capacity` | 14 |
| `attendance_capacity` | 16 |

## Device time encoding

The compact time encoding is:

```text
value = (((((year - 2000) * 12 + (month - 1)) * 31 + (day - 1))
          * 24 + hour) * 60 + minute) * 60 + second
```

Decoding reverses the arithmetic. The result is a naive `datetime` in device
local time.

## Buffer size parsing

`_buffer_size` accepts two shapes:

- a 5-byte form where the first byte is `0` and bytes 1–4 are the size;
- a 4-byte little-endian size.

A response shorter than 5 bytes (or 4 bytes for the second form) raises
`ProtocolError`.

## Stability and security

- Treat command values, record layouts, and the key algorithm as firmware
  details, not a stable API.
- The high-level `Device` methods are the supported interface.
- The protocol has no TLS, no message authentication beyond the checksum, and
  no modern identity model.
- Do not expose port `4370` to the internet.
- Capture only what you need when debugging; captures can contain personal data.

## Next

- [Device API](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/device-api.md)
- [Models](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/models.md)
- [Troubleshooting](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/troubleshooting.md)

---

### From [docs/help/troubleshooting.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/troubleshooting.md)

# Troubleshooting

## Why this matters

A good diagnosis separates four layers:

```text
Python environment -> network -> device protocol -> data/semantics
```

Most “SDK errors” are one of the first three. Fixing the wrong layer wastes time
and can make a device problem worse. Work from the outside in.

## Quick triage

| Symptom | First check |
| --- | --- |
| `ModuleNotFoundError: essl_f22` | Wrong interpreter or virtual environment. |
| `DeviceTimeoutError` on connect | IP, port, firewall, device power. |
| `DeviceConnectionError` / refused | Nothing listening on that TCP port. |
| `DeviceAuthenticationError` | Communication key. |
| `ProtocolError` | Model/firmware/protocol mismatch. |
| `UserNotFoundError` | UID versus user ID confusion. |
| `ValueError` on write | UID range or encoded field length. |
| `NoFreeTimeZoneSlotError` | No eligible timezone slot. |
| `StorageConfigurationError` | Missing extra, DSN, URI, or URL. |
| `StateStoreError` | File permissions, disk, corrupt JSON, SQLite failure. |
| `SyncError` | Wrong mirror serial or unsupported mode. |
| Garbled names | Encoding mismatch. |
| Hardware test skipped | `ESSL_F22_HOST` is unset. |

## The import fails

Check which interpreter your editor or service is using:

```bash
python -c "import sys; print(sys.executable)"
python -c "import essl_f22; print(essl_f22.__version__)"
```

If the import fails:

- activate the virtual environment where you installed the package;
- install into the same interpreter your program uses;
- avoid mixing `pip` from one Python with `python` from another;
- do not rely on `pipx` or `uvx` to make a library importable in your project.

Correct project installation:

```bash
python -m pip install Essl_F22_SDK
# or
uv add Essl_F22_SDK
```

If you are before the first public release, install the built wheel explicitly.
See [Installation](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/getting-started/installation.md).

## The package name looks wrong

`pip` and `uv` may display `essl-f22-sdk` because package normalization treats
hyphens, underscores, and periods as equivalent. The distribution name is
`Essl_F22_SDK`; the import name is `essl_f22`. Check with:

```bash
python -m pip show Essl_F22_SDK
python -c "import essl_f22; print(essl_f22.__file__)"
```

If both commands find the package, the normalized spelling is only a display
convention.

## Cannot connect: timeout

```text
DeviceTimeoutError: device connection timed out
```

Check, in order:

1. **Address.** Is `192.168.1.50` (or your host) correct and reachable?
2. **Route.** Is the computer on the same LAN, VLAN, or VPN?
3. **Port.** Is TCP `4370` (or the configured port) open?
4. **Power.** Is the device on and connected to the network?
5. **Firewall.** Is a host, VLAN, or VPN firewall dropping the traffic?
6. **Timeout.** Is the network slow enough that 10 seconds is too short?

Commands:

```bash
ping -c 3 DEVICE_IP
nc -vz DEVICE_IP 4370
```

```powershell
Test-NetConnection -ComputerName DEVICE_IP -Port 4370
```

Ping success does not prove the TCP port works. Ping failure does not always
prove the port is closed, because some devices block ICMP.

## Cannot connect: refused or closed

```text
DeviceConnectionError: [Errno 61] Connection refused
```

The host is reachable, but nothing is accepting connections on that port.
Confirm the device's TCP port in its settings. Do not change the port blindly;
update the SDK and the firewall together.

If the connection drops during a read:

- check for duplicate IP addresses;
- check Wi-Fi instability;
- check whether another process is resetting the device session;
- retry once with a new `Device` instance;
- capture the exact error and the operation that was running.

## Authentication fails

```text
DeviceAuthenticationError: authentication rejected with 0x...
```

The communication key is wrong or the device's authentication mode is not what
the SDK expects.

- Ask the device administrator for the key.
- Do not try a long list of guesses.
- Confirm the key belongs to this device, not another site.
- Confirm the device is not in a mode that blocks the SDK's connect sequence.

Repeated authentication failures may be logged as a security event.

## Protocol errors

```text
ProtocolError: invalid frame magic
ProtocolError: frame length does not match its header
ProtocolError: unsupported attendance record size ...
```

This usually means the device is not speaking the expected dialect, the response
was truncated, or the wrong data family was requested.

Collect:

- device model;
- platform string (`get_option("~Platform")`);
- firmware version;
- exact operation;
- full traceback;
- whether it reproduces consistently.

Do not loop retries. A deterministic layout mismatch will not heal.

## Names look garbled

The device may use a different text encoding from the SDK's default UTF-8.

- Confirm the expected encoding with the vendor or device documentation.
- Try an alternative only on test data.
- Remember that field limits are **bytes**, not characters.
- Do not “fix” names by truncating bytes in the middle of a multibyte character.

```python
device = Device("192.168.1.50", comm_key=0, encoding="...")
```

## User not found

```text
UserNotFoundError: user uid 295 was not found
```

Check whether you are using the internal UID or the visible user ID:

```python
device.get_user(295)  # UID
device.get_user_by_user_id("1001")  # user ID
```

`get_user_by_user_id()` is a linear scan over `list_users()`. It is not a
device-side index.

## Value errors on write

```text
ValueError: user uid must fit in an unsigned 16-bit field
ValueError: value of 28 bytes does not fit in 24 bytes
```

- UID must be `0`–`65535`.
- `user_id` and `name` allow at most 23 encoded bytes.
- `password` allows at most 7 encoded bytes.
- Non-ASCII characters can use multiple bytes.

Read [Users](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/concepts/users.md#field-length-limits) for the limits.

## No free timezone slot

```text
NoFreeTimeZoneSlotError: no free default-allow-all timezone slot is available
```

Blocking needs a slot that is:

- not referenced by any group's `tz1`–`tz3`;
- not referenced by a user with `timezone_flag` set;
- currently a default allow-all schedule.

The blocker chooses the highest eligible slot. If none exists, it stops before
changing the user. Free a slot deliberately or use another access-control
method. Do not overwrite a referenced schedule just to make the error go away.

## Storage configuration errors

```text
StorageConfigurationError: PostgreSQL storage requires psycopg ...
StorageConfigurationError: postgres storage requires a non-empty 'dsn' ...
```

- Install the matching extra: `Essl_F22_SDK[postgres]`, `[mysql]`, `[mongo]`, or
  `[redis]`.
- Provide `storage_options={"dsn": ...}`, `{"uri": ...}`, or `{"url": ...}`.
- For MySQL, include a database in the DSN.
- For MongoDB, include a database in the URI.
- Do not pass an empty string.

The error appears at the first storage operation because storage is created
lazily.

## State store errors

```text
StateStoreError: cannot initialize SQLite storage ...
StateStoreError: storage file ... is not valid JSON
StateStoreError: storage file ... has an unsupported format
```

Check:

- the directory exists and is writable;
- the disk is not full;
- the process has permission to create/read the file;
- the JSON file was not truncated or edited by hand;
- the application is not mixing incompatible storage formats;
- only one writer is using a JSON file.

If the state store is corrupt and you use blocking, stop. Restore from backup or
reconstruct the state before changing access schedules.

## Sync errors

```text
SyncError: device serial 'NEW' does not match mirror serial 'OLD'
```

You are using a mirror for a different device. Create a new mirror or use the
correct device/storage path.

```text
SyncError: unsupported sync mode '...'
```

Use `"full"` or `"incremental"`.

If a sync fails midway:

- do not trust the mirror as a complete snapshot;
- fix the storage/network problem;
- run a full sync;
- verify counts and samples before reporting.

## The hardware test is skipped

The hardware test is opt-in:

```bash
ESSL_F22_HOST=192.168.1.50 \
ESSL_F22_PORT=4370 \
ESSL_F22_COMM_KEY=0 \
uv run pytest -m hardware
```

Without `ESSL_F22_HOST`, it is skipped by design. It is read-only; it does not
test block/unblock or writes.

## Docs build fails

Build the handbook with the pinned extra:

```bash
uv sync --extra docs
uv run mkdocs build --strict
```

Common causes:

- a navigation entry points to a missing file;
- an internal link points to a missing page or heading;
- a malformed table or code fence;
- a warning promoted to an error by `--strict`.

Fix the link or heading; do not remove `--strict` to hide the problem.

## What to include in a bug report

Provide:

- `Essl_F22_SDK` version;
- Python version and OS;
- device model, platform, firmware, and serial (redact if needed);
- exact operation and a minimal reproduction;
- full traceback;
- whether the operation was read or write;
- storage backend and version;
- what you expected and what happened.

Do not include:

- communication keys;
- database passwords or DSNs;
- fingerprint templates;
- full attendance or user exports;
- personal data that is not necessary.

## Next

- [FAQ](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/faq.md)
- [Compatibility](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/compatibility.md)
- [Handle errors](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/handle-errors.md)

---

### From [docs/help/faq.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/faq.md)

# FAQ

## Is this an official eSSL or ZKTeco SDK?

No. It is an independent, open-source Python library for F22-compatible
terminals. It is not endorsed by or affiliated with eSSL or ZKTeco. Device
behaviour and compatibility are validated by the project, not guaranteed by the
vendor.

## Which devices are supported?

F22-compatible devices that implement the command set and record layouts used by
the SDK. The project has been exercised against an F22-class device reporting
the `ZLM60_TFT` platform and firmware in the 6.60 line. Other models, OEM
variants, and firmware revisions may differ.

See [Compatibility](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/compatibility.md) before using a new device.

## Does it work over the internet?

Technically it uses TCP, so it can cross a routed network. Operationally, do not
expose port `4370` to the public internet. The protocol has no TLS, and the
communication key is not a modern authentication system.

Use a VPN, a dedicated VLAN, a jump host, and firewall rules that allow only
approved hosts.

## Can I enroll a fingerprint with the SDK?

No. Enrollment is a device workflow. The SDK can read fingerprint templates and
metadata, but it has no public template-write or enrollment API.

## Can I match fingerprints in Python?

No. The device performs matching. The SDK is not in the door-opening path.

## Does the mirror store fingerprint templates?

No. It stores only `uid`, `fid`, `flag`, and `size` metadata. Raw template bytes
are deliberately excluded.

## Does the mirror store user passwords?

Yes. Full `User` records include the device `password` field. The mirror does
not store the device communication key, but it is still sensitive. Encrypt the
storage and restrict access to it.

## Can I restore a device from the mirror?

No. The mirror is read-only. It cannot write users, attendance, schedules, or
templates back to a device. It is a reporting and comparison copy, not a restore
tool.

## Why is there no CLI?

The project is a library. It is designed to be imported by an application that
owns business rules, credentials, scheduling, and audit policy. A generic CLI
would make destructive device writes too easy to run accidentally.

## Can I use pipx or uvx?

`pipx` and `uvx` are application runners. They do not make the library
importable in your project. Use `pip install Essl_F22_SDK` or `uv add
Essl_F22_SDK`.

For a one-off import check:

```bash
uvx --from Essl_F22_SDK python -c "from essl_f22 import Device; print(Device)"
```

## Why do some tools show `essl-f22-sdk` instead of `Essl_F22_SDK`?

PEP 503 normalization treats hyphens, underscores, and periods as equivalent. The
distribution name is `Essl_F22_SDK`; the import name is `essl_f22`. The normalized
spelling is `essl-f22-sdk`; the hyphenated spelling is a display convention, not a
different package.

## Which Python versions are supported?

Python 3.12 and newer. Metadata advertises 3.12, 3.13, and 3.14. CI currently
runs the quality gates on Python 3.14. Test your exact interpreter and platform
before a production rollout.

## Is it async?

No. The public API is synchronous and uses blocking sockets. Run it in a worker
thread or process if you need to integrate with an async application. Do not
share one `Device` across threads without locking.

## Can I talk to multiple devices?

Yes. Use one `Device` per physical device and per worker. Storage is scoped by
device serial, so mirrors and block state for different devices do not collide
in the same backend.

## Is `Device` thread-safe?

No. A session keeps request sequence and receive-buffer state. One `Device`
should be used by one thread at a time, or protected by your own lock.

## Does deleting a user delete their attendance?

It depends on the firmware. The SDK sends the delete command and does not assume
what happens to related records. Test on a non-production device before relying
on either behaviour.

## Does `set_user()` verify every field?

No. It validates the record locally, sends it, requires an acknowledgement, and
refreshes device data. It does not read the record back and compare every field.
Call `get_user()` if you need proof of the final state.

## What is the difference between blocking and deleting?

Blocking assigns a deny-all access schedule and saves the original assignment.
The user and fingerprint templates remain. Deleting removes the user record and
is destructive.

Blocking is not a security lock. Someone with device administrator access can
change the schedule.

## What happens if I unblock without saved state?

`unblock_user()` disables personal scheduling and reports `state_found=False`.
That may not be the person's original schedule. If the state store is lost, read
the current assignment and restore the intended schedule deliberately.

## Why are timestamps naive?

The device stores local wall-clock time without a timezone. The SDK preserves
that. Attach the device's timezone at ingestion if you need UTC.

## Why does incremental sync read the whole attendance log?

The device protocol and public API do not expose a reliable attendance cursor.
The SDK reads the log and merges it by a stable record hash. “Incremental” refers
to the storage merge, not a network delta.

## Why did attendance get replaced?

Incremental sync replaces attendance when the device's count is lower than the
mirror's count. That usually means the device log was cleared or reset. Check
`result.attendance_replaced` and archive the previous snapshot before accepting
the replacement.

## Can I query attendance by date on the device?

No public device-side date filter exists. `list_attendance()` reads the full
log. Use the mirror for `since`/`until` queries, while remembering that SQLite
and JSON still load matching records into memory.

## Where is the default database?

SQLite uses `default_state_path()` and JSON uses `default_mirror_path()`, both
inside the platform application-data directory for `essl_f22`. Use an explicit
path in production.

## Can multiple processes use SQLite?

SQLite supports normal multi-process locking, but the safe assumption is one
writer per file. Do not put the database on a network filesystem unless you know
its locking semantics. For shared multi-host use, choose PostgreSQL, MySQL, or
MongoDB.

## Is Redis durable?

Only if your Redis deployment is configured for durability and you have reviewed
the eviction policy. The SDK uses Redis hashes; it does not make Redis durable
for you.

## Is data encrypted?

The device protocol is not TLS, and the SDK does not encrypt storage. Use a
trusted network, database/filesystem encryption, access controls, and encrypted
backups.

## What is error code `0x1381`?

It is the device's “not found” response for timezone and group scans. The SDK's
`list_timezones()` and `list_groups()` skip it. A direct `get_timezone()` or
`get_group()` can still raise `CommandError` with that code.

## Can I use this for payroll?

You can use it to read attendance, but the SDK does not provide payroll policy,
rounding, approval, dispute handling, or legal compliance. Validate the data,
timezone handling, retention, and audit requirements with your organisation.

## Is commercial use allowed?

The project is licensed under Apache License 2.0. That permits commercial use
under the license terms, with no warranty. Review the `LICENSE` file and your
organisation's open-source policy.

## How do I contribute?

Read [Development](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/contributing/development.md) and the repository `AGENTS.md`.
Changes follow the issue → branch → PR → `dev` → `stag` → `prod` flow and must
pass tests, ruff, mypy, and documentation checks.

## Next

- [Troubleshooting](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/troubleshooting.md)
- [Glossary](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/glossary.md)
- [Compatibility](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/compatibility.md)

---

### From [docs/help/glossary.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/glossary.md)

# Glossary

Plain-language definitions for terms used in this handbook.

**Essl F22 SDK**<br>
The Python library described by this handbook. Its distribution name is
`Essl_F22_SDK` and its import name is `essl_f22`.

## Device terms

**Terminal / device**<br>
The physical attendance or access unit. It stores users, templates,
attendance, groups, and schedules, and it decides whether to open a door.

**F22**<br>
A family of eSSL/ZKTeco terminals. “F22-compatible” means a device that speaks
the command set and record layouts used by this SDK. It is not a guarantee that
every model or firmware behaves identically.

**Communication key (comm key)**<br>
A shared secret used during the device handshake. The default is often `0`, but
the actual value is a device setting. It is not a strong authentication system.

**Serial number**<br>
The device's unique identifier. Mirrors and block state are scoped by serial.

**UID**<br>
The internal user slot number, 16 bits. Write and delete operations address
users by UID. It is not the same as the visible user ID.

**User ID**<br>
The device-visible identifier for a person, stored as a string. Attendance
records carry the user ID as it was at punch time.

**Attendance record**<br>
One punch event: UID, user ID, timestamp, status, and punch value.

**Punch / status**<br>
Device-specific values attached to an attendance event. The SDK reads them but
does not interpret them.

**Fingerprint template**<br>
The device's proprietary biometric representation of a fingerprint. It is not
an image and cannot be enrolled or matched by this SDK.

**FID**<br>
The device's finger identifier for a template. The SDK does not map it to a
named finger.

**Fingerprint metadata**<br>
The non-biometric description of a template: UID, FID, flag, and size. The
mirror stores only this.

**Group**<br>
A device grouping that carries access timezone assignments and verification
flags.

**Timezone slot**<br>
A numbered access schedule on the device. A slot contains seven day intervals.

**Day interval**<br>
A start and end time for one weekday. The SDK's model uses inclusive minutes
and does not support an interval crossing midnight.

**Allow-all**<br>
A schedule that permits access all day, represented in the SDK as
`00:00–23:59` on every day.

**Deny-all**<br>
A schedule that permits no access, represented as an interval whose start is
greater than or equal to its end.

**Personal timezone**<br>
A per-user access assignment that can override or supplement the group schedule.
The device exposes it separately from the `User` record fields.

**Block**<br>
A reversible access change that points a user at a deny-all schedule. It does
not delete the user or templates.

**Unblock**<br>
Restoring the saved access assignment. If the saved state is missing, the SDK
falls back to disabling personal scheduling.

## Software terms

**SDK**<br>
Software development kit. A library that provides tools for a specific platform
or protocol.

**Library**<br>
Importable code used by another program. This project is a library, not a
standalone application.

**CLI**<br>
Command-line interface. This project does not provide one.

**TCP**<br>
The network transport used to reach the device. It provides a reliable byte
stream, not encryption.

**Port**<br>
A numbered network endpoint. The default device port is `4370`.

**IP address**<br>
The network address of the device or the computer running the SDK.

**Session**<br>
The connected state between the SDK and one device, including the session ID,
reply sequence, and receive buffer.

**Frame**<br>
One protocol message: a TCP header plus a command header plus data.

**Checksum**<br>
A small arithmetic value used to detect some transmission errors.

**Buffer**<br>
A block of data returned by the device. Large buffers are read in chunks.

**Protocol**<br>
The rules for command numbers, frame layout, authentication, and record
encoding.

**Socket**<br>
The operating-system network connection used by the transport.

## Storage terms

**Mirror**<br>
A read-only copy of device data in a storage backend.

**Snapshot**<br>
A point-in-time copy. In this SDK, a mirror sync produces a snapshot, but it is
not atomic across all collections.

**Sync**<br>
Reading device data and writing it to the mirror.

**Full sync**<br>
Replaces all mirrored collections and attendance.

**Incremental sync**<br>
Replaces non-attendance collections, inserts new attendance keys, and replaces
attendance if the device count dropped.

**Storage backend**<br>
The implementation that stores mirror and block state: SQLite, JSON, memory,
PostgreSQL, MySQL, MongoDB, or Redis.

**State store**<br>
The part of storage that saves each blocked user's original access assignment
and the deny-all slot.

**SQLite**<br>
A file-based relational database built into Python. The default local backend.

**JSON**<br>
A text format. The JSON backend stores the entire snapshot in one file.

**Memory backend**<br>
Process-local storage that disappears when the process exits.

**DSN**<br>
Data source name, a connection string for a database. PostgreSQL and MySQL use
`dsn`.

**URI**<br>
A connection identifier. MongoDB uses `uri`.

**URL**<br>
A connection address. Redis uses `url`.

**Serialization**<br>
Converting objects to a storable format such as JSON.

## Data and security terms

**Naive datetime**<br>
A Python `datetime` without timezone information. Attendance timestamps are
naive and represent device-local wall-clock time.

**PII**<br>
Personally identifiable information. Names, user IDs, attendance, and biometric
data can all be PII or sensitive personal data.

**Biometric data**<br>
Data derived from a person's physical characteristics. Fingerprint templates are
biometric data.

**Metadata**<br>
Data about data. Fingerprint metadata describes a template without containing
the biometric bytes.

**VLAN**<br>
A segmented network. Useful for isolating devices from general-purpose
networks.

**VPN**<br>
An encrypted tunnel between networks. Useful for remote administration without
exposing the device port publicly.

**TLS**<br>
Transport Layer Security, used to encrypt network connections. The device
protocol in this SDK does not use TLS.

**Least privilege**<br>
Granting only the permissions needed for a task. Apply it to database users,
network access, and SDK credentials.

## Packaging terms

**Wheel**<br>
A built Python package file (`.whl`) that can be installed directly.

**sdist**<br>
A source distribution archive.

**Extra**<br>
An optional dependency group, such as `Essl_F22_SDK[postgres]`.

**PEP 503**<br>
The Python packaging normalization rule that treats `-`, `_`, and `.` as
equivalent in project names. It is why tools may display `essl-f22-sdk`.

**uv**<br>
A Python package and environment manager used by this project.

**pipx / uvx**<br>
Tools for running applications in isolated environments. They do not make a
library importable in your project.

## Next

- [FAQ](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/faq.md)
- [Compatibility](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/compatibility.md)
- [Troubleshooting](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/troubleshooting.md)

---

### From [docs/help/compatibility.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/compatibility.md)

# Compatibility

## Why this matters

“F22-compatible” is a family description, not a certificate. Firmware revisions
can change option names, record layouts, timezone behaviour, and command
responses. This page states what has actually been exercised and how to validate
a new device safely.

## Supported Python versions

The package declares:

```toml
requires-python = ">=3.12"
```

Metadata advertises Python 3.12, 3.13, and 3.14. CI currently runs the quality
gates and package build on Python 3.14.

Before production:

- run the test suite on your exact Python version;
- run an import and a read-only device sync;
- verify optional storage drivers if you use them.

## Operating systems

The SDK uses standard-library sockets and `pathlib`. It is not tied to a
particular OS.

| Environment | Status |
| --- | --- |
| Ubuntu (CI) | Quality gates and package build run here. |
| macOS (development) | Used for development and read-only hardware validation. |
| Windows | Path handling and socket support exist; not exercised by CI. Test before deployment. |

Default data paths follow platform conventions; see
[Storage](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/reference/storage.md#default-paths).

## Device validation

The project has been exercised against an F22-class terminal reporting:

- platform `ZLM60_TFT`;
- firmware in the 6.60 line;
- TCP port `4370`;
- a communication key configured for the test device.

Validated behaviours include:

- read-only hardware test: device info, counts, users, fingerprint metadata,
  and a memory mirror;
- manual create, read, and delete of a test user;
- attendance, group, timezone, and user-timezone reads;
- mirror sync into the supported storage backends during development.

Not yet validated on hardware:

- updating an existing user through `set_user()`;
- block/unblock against a production access policy;
- multiple firmware branches and OEM variants;
- every capacity and timezone-slot layout.

The hardware test is read-only and opt-in:

```bash
ESSL_F22_HOST=192.168.1.50 \
ESSL_F22_PORT=4370 \
ESSL_F22_COMM_KEY=0 \
uv run pytest -m hardware
```

It is skipped when `ESSL_F22_HOST` is unset. It does not test writes,
block/unblock, or destructive operations.

## Feature support

| Feature | Support |
| --- | --- |
| Device info and serial | Yes |
| Users read | Yes |
| Users create/update/delete | Create and delete validated; update implemented but not hardware-validated. Writes are real and destructive where noted. |
| Attendance read | Yes |
| Fingerprint templates read | Yes |
| Fingerprint metadata in mirror | Yes |
| Fingerprint enrollment | No |
| Fingerprint template write | No |
| Fingerprint matching | No |
| Groups read/write | Yes |
| Timezones read/write | Yes |
| User-timezone assignment read/write | Yes |
| Non-destructive block/unblock | Yes, with state-store caveats |
| Mirror/sync | Yes, read-only copy |
| Restore mirror to device | No |
| Firmware/network management | No |
| GUI/CLI | No |
| TLS/encryption | No; use a trusted network |

## Firmware caveats

These are the areas most likely to vary:

- exact option names and response formats;
- user record field semantics, especially privilege and personal timezone
  fields;
- attendance status and punch meanings;
- timezone “allow-all” and “deny-all” representation;
- group verification flags and holiday behaviour;
- capacity counts and maximum slot/group IDs;
- behaviour when deleting a user with attendance or templates;
- authentication mode and communication-key handling.

The SDK raises `ProtocolError` or `CommandError` when a response does not fit
its expectations. Do not “fix” those errors by guessing new offsets or silently
ignoring fields. Capture the device details and test a deliberate change.

## Validating a new device

Use this sequence:

1. **Network check.** Confirm the IP and TCP port.
2. **Read-only connect.** Read device info and free sizes.
3. **Count check.** Compare users, fingerprints, and attendance with the device
   display or vendor software.
4. **Sample check.** Compare one user and one attendance record.
5. **Structure check.** Read groups and timezones; confirm the slot and group
   ranges.
6. **Mirror check.** Sync into `memory` or a temporary SQLite file; verify
   counts.
7. **Write test.** Create a dedicated test user, read it back, update one field,
   read it back, then delete it.
8. **Block test.** On a test user, confirm the slot choice, block, door
   behaviour, unblock, and door behaviour.
9. **Failure test.** Disconnect the network during a read; confirm the error is
   clear and recoverable.
10. **Documentation.** Record model, platform, firmware, serial, capacity, and
    any deviations.

Do not start with a bulk write or a production user.

## Optional storage compatibility

Core tests do not require external services. The storage contract tests are
opt-in:

```bash
ESSL_F22_POSTGRES_DSN=postgresql://user:pass@db/app \
ESSL_F22_MYSQL_DSN=mysql://user:pass@db/app \
ESSL_F22_MONGO_URI=mongodb://localhost/app \
ESSL_F22_REDIS_URL=redis://localhost/0 \
uv run pytest tests/test_storage_contract.py
```

Run them against the exact database versions, TLS settings, and permissions you
plan to use. A backend that passes locally may fail in production because of
networking, authentication, or schema permissions.

## Versioning and stability

The project is pre-1.0. Treat the public API as usable but still subject to
change. Pin the version in your lock file, read the changelog, and test upgrades
on a non-production device.

Protocol internals are especially likely to change as compatibility improves.
Use the high-level `Device`, `Mirror`, and storage APIs rather than importing
command constants or frame builders in application code.

## Reporting a compatibility issue

Include:

- package version;
- Python version and OS;
- device model, platform, firmware, and serial (redact as needed);
- exact command/method;
- full traceback;
- whether it is reproducible;
- a minimal read-only reproduction, if possible.

Do not include communication keys, database credentials, or fingerprint
template bytes.

## Next

- [FAQ](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/faq.md)
- [Troubleshooting](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/troubleshooting.md)
- [Production checklist](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/guides/production-checklist.md)

---

### From [docs/contributing/development.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/contributing/development.md)

# Development

## Why this matters

This project talks to real hardware and can change access control. A passing
unit test is necessary but not sufficient. The development workflow is designed
to keep speculative changes, untested writes, and unreviewed documentation out
of the integration branches.

## Before you start

- Read the repository `AGENTS.md`.
- Check open issues and pull requests.
- Confirm the target issue and branch.
- Do not push directly to `dev`, `stag`, or `prod`.

## Branch flow

```text
feature/issue branch  ->  dev  ->  stag  ->  prod
```

- Feature and fix branches start from `dev`.
- Pull requests target `dev`, except promotion PRs.
- Promotion is one hop at a time and PR-only:
  - `dev` → `stag`
  - `stag` → `prod`
- Never skip or reorder a hop.
- Never merge with `--delete-branch` when the head is an integration branch.

Branch naming:

```text
<type>/<issue#>-<slug>
```

Examples:

```text
feat/42-add-backend
fix/43-handle-timeout
docs/36-complete-handbook
```

## Setup

```bash
uv sync
```

This installs the development group and the project in editable mode. Optional
storage drivers are not installed unless you add their extras.

To work on documentation:

```bash
uv sync --extra docs
```

## The quality gates

Run all of these before opening a pull request:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest
```

And, for documentation changes:

```bash
uv run mkdocs build --strict
```

The gates must be clean. Do not disable a rule, add a blanket `type: ignore`, or
skip a test to make a change pass. Fix the cause.

## Tests

The default suite must not require a physical device:

```bash
uv run pytest
```

Use fake transports and sessions for unit tests. Put hardware-specific tests
behind the `hardware` marker.

### Hardware test

The hardware test is read-only:

```bash
ESSL_F22_HOST=192.168.1.50 \
ESSL_F22_PORT=4370 \
ESSL_F22_COMM_KEY=0 \
uv run pytest -m hardware
```

It is skipped when `ESSL_F22_HOST` is unset. It must not call block/unblock or
write to the device.

### Storage contract tests

External backends are opt-in:

```bash
ESSL_F22_POSTGRES_DSN=postgresql://user:pass@db/app \
ESSL_F22_MYSQL_DSN=mysql://user:pass@db/app \
ESSL_F22_MONGO_URI=mongodb://localhost/app \
ESSL_F22_REDIS_URL=redis://localhost/0 \
uv run pytest tests/test_storage_contract.py
```

Run the tests against the exact database versions and permissions you support.
Do not commit test credentials.

### Test naming

Test names should describe the behaviour, not the implementation. A reader
should know what broke from the failure message.

## Code style

- Python 3.12+.
- Ruff for lint and format.
- Mypy strict over `src/`.
- Follow the style of the module you touch.
- No comments unless they explain something the code cannot.
- No `TODO` markers, commented-out code, or dead files.
- No `v2`, `copy`, `.new`, `backup`, or `-final` variants.

## Architecture

```text
src/essl_f22/
  errors.py       exception hierarchy
  protocol.py     constants, checksums, frames, codecs
  transport.py    TCP socket transport
  session.py      connect/auth, command I/O, buffered reads
  models.py       dataclasses and record codecs
  device.py       high-level device API
  mirror.py       read-only mirror and sync
  access.py       block/unblock manager
  storage/        protocols, codecs, backends, factory
  state.py        SQLite block-state compatibility shim
  __init__.py     public exports
```

Keep layering intact:

- `device.py` orchestrates; it should not reimplement frame parsing.
- `session.py` handles command exchange and buffering.
- `protocol.py` owns constants and binary codecs.
- `storage/` owns persistence and backend selection.
- `mirror.py` and `access.py` depend on protocols, not concrete sockets.

## Documentation

This handbook lives in `docs/` and is built with MkDocs Material.

Preview locally:

```bash
uv run mkdocs serve
```

Validate strictly:

```bash
uv run mkdocs build --strict
```

### Publishing the handbook

GitHub Pages is not available for this private repository on the free plan.
Cloudflare Pages supports private GitHub repositories on its free plan, with
unlimited bandwidth and 500 builds per month.

To publish:

1. In the Cloudflare dashboard, open **Workers & Pages** and create a Pages
   project.
2. Connect the `mramitdas/Essl_F22_SDK` GitHub repository.
3. Set the production branch to `prod`.
4. Set the build command to
   `python -m pip install mkdocs-material && mkdocs build --strict`.
5. Set the build output directory to `site`.
6. Set `PYTHON_VERSION` to `3.13` if the build image does not select a supported
   version automatically.

The generated `site/` directory is ignored by git. Set `site_url` in
`mkdocs.yml` only after the public hostname is known.

Rules:

- Every behaviour or setup change updates the relevant page.
- Use plain language for operator-facing pages, then exact signatures in the
  reference.
- Do not document unverified device behaviour as fact.

## Pull request checklist

- [ ] One issue, one logical change.
- [ ] Branch targets `dev`.
- [ ] Tests cover the behaviour change.
- [ ] `uv run ruff check .` passes.
- [ ] `uv run ruff format --check .` passes.
- [ ] `uv run mypy src/` passes.
- [ ] `uv run pytest` passes.
- [ ] Documentation updated if setup, behaviour, or API changed.
- [ ] `uv run mkdocs build --strict` passes for docs changes.
- [ ] No secrets, `.env`, or credentials in the diff.
- [ ] `git diff` contains only intended changes.

## Commit and PR style

- Conventional commit type: `feat:`, `fix:`, `docs:`, `test:`, `chore:`.
- Subject at most 50 characters.
- Body ends with `refs #N`.
- PR targets the correct branch.
- Do not force-push or skip hooks.

## Reporting a bug

Include the package version, Python version, OS, device model/platform/firmware,
steps to reproduce, and the full traceback. Redact secrets and personal data.

See [Troubleshooting](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/troubleshooting.md) for what to collect.

## Next

- [Release](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/contributing/release.md)
- [Contributing source](https://github.com/mramitdas/Essl_F22_SDK/blob/dev/CONTRIBUTING.md)
- [Project rules](https://github.com/mramitdas/Essl_F22_SDK/blob/dev/AGENTS.md)

---

### From [docs/contributing/release.md](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/contributing/release.md)

# Release

## Why this matters

A Python release is immutable in practice: once a version is published to PyPI,
you should not reuse that version number. A bad tag or a missing trusted
publisher can block the release, and a partial release can leave users with a
wheel that does not match the tag.

This page is the release runbook. It assumes the branch flow and quality gates
in [Development](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/contributing/development.md) are already satisfied.

## Current release status

The `0.1.0` package is published to PyPI. Publication used Trusted Publishing;
do not reuse version `0.1.0`.

One-time trusted publisher setup is complete for this project.

Do not create the release tag until that setup is complete and verified.

## One-time PyPI setup

Configure a **pending trusted publisher** on PyPI:

| Field | Value |
| --- | --- |
| PyPI project | `Essl_F22_SDK` |
| Owner | `mramitdas` |
| Repository | `Essl_F22_SDK` |
| Workflow filename | `release.yml` |
| Environment | `pypi` |

Then create the matching `pypi` environment in the GitHub repository settings.
The workflow uses OpenID Connect, so no PyPI API token is stored in GitHub.

Until this is done, the release workflow cannot publish. A PyPI page returning
`404` is expected before the first successful release.

## Versioning

The version is defined in one place:

```python
# src/essl_f22/__init__.py
__version__ = "0.1.0"
```

`pyproject.toml` reads it dynamically through Hatch:

```toml
[tool.hatch.version]
path = "src/essl_f22/__init__.py"
```

Do not hard-code a second version in `pyproject.toml`.

The project follows Semantic Versioning. Before `1.0.0`, minor versions may
contain API changes; document them in the changelog.

## Release steps

### 1. Prepare the release change

- Update `__version__`.
- Update `CHANGELOG.md` with the release date and user-visible changes.
- Update documentation if setup, behaviour, or compatibility changed.
- Run every quality gate.
- Build and inspect the artifacts locally.

```bash
uv sync --extra docs
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest
uv run mkdocs build --strict
uv build
uvx twine check dist/*
```

### 2. Verify the artifacts

Install the wheel into a clean environment:

```bash
uv venv --python 3.14 /tmp/essl_f22-release
uv pip install --python /tmp/essl_f22-release/bin/python dist/*.whl
/tmp/essl_f22-release/bin/python -c \
  "from importlib.metadata import version; import essl_f22; from essl_f22 import Device; assert essl_f22.__version__ == version('Essl_F22_SDK'); print(essl_f22.__version__, Device)"
```

Check:

- the wheel imports;
- `essl_f22.__version__` matches the wheel metadata;
- `py.typed` is present;
- the sdist contains the source tree and expected metadata;
- no secrets, local databases, or build junk are included.

### 3. Merge through the branch chain

The release change must travel through the normal PR flow:

```text
feature/issue branch -> dev -> stag -> prod
```

- Merge the change into `dev` by PR.
- Promote `dev` to `stag` by PR.
- Promote `stag` to `prod` by PR.
- Do not merge with `--delete-branch` when the head is `dev` or `stag`.

Do not tag a commit that is not on `prod`.

### 4. Tag `prod`

```bash
git checkout prod
git pull --ff-only origin prod
git tag -a v0.1.0 -m "Essl F22 SDK 0.1.0"
git push origin v0.1.0
```

The release workflow triggers on tags matching `v*`.

Before pushing the tag, confirm:

- the working tree is clean;
- `prod` is at the intended commit;
- the version in `__init__.py` matches the tag;
- the changelog is updated;
- the trusted publisher and `pypi` environment exist.

### 5. Watch the workflow

The `release.yml` workflow:

1. checks out the tagged commit;
2. installs uv and Python 3.14;
3. builds the sdist and wheel with `uv build`;
4. checks metadata with `twine check`;
5. publishes with `pypa/gh-action-pypi-publish` using Trusted Publishing.

The job uses the `pypi` environment and has `id-token: write` permission.

If the workflow fails before publishing, fix the cause and push a new tag only
if the version has not been consumed. If PyPI accepted the files, do not reuse
the version.

### 6. Verify the published release

```bash
uv venv --python 3.14 /tmp/essl_f22-pypi
uv pip install --python /tmp/essl_f22-pypi/bin/python Essl_F22_SDK==0.1.0
/tmp/essl_f22-pypi/bin/python -c \
  "from importlib.metadata import version; import essl_f22; print(version('Essl_F22_SDK'), essl_f22.__version__)"
```

Also verify:

- PyPI shows the expected files and metadata;
- the project page renders the README;
- installation works with `pip` and `uv`;
- the import name is `essl_f22`;
- the `docs` extra installs.

## Failed or partial release

### Workflow failed before upload

Fix the cause, re-run the workflow, or delete and recreate the tag only if the
version was never published.

Deleting or force-moving a tag is a destructive operation. Get explicit
approval.

### Upload succeeded but the release is wrong

Do not reuse the version. Options:

- yank the release on PyPI if it must not be installed;
- publish a new patch version with the fix;
- document the issue in the changelog.

Yanking hides a release from resolution but does not delete it. Treat any PyPI
mutation as a release decision, not a routine edit.

### Trusted publishing rejects the workflow

Check:

- the PyPI pending publisher owner/repository/workflow/environment values;
- the GitHub environment name is exactly `pypi`;
- the workflow is running from the tagged `prod` commit;
- the repository has the expected permissions;
- the PyPI project name is `Essl_F22_SDK`.

A `404` on the PyPI project page before the first release is expected.

## Post-release

- Close the release issue only after the package is published and verified.
- Update any deployment pins to the new version.
- Announce changes according to your project process.
- Keep the built wheel and sdist if your retention policy requires a rollback
  artifact.
- Do not commit `dist/` to the repository.

## Release checklist

- [ ] Version updated in `src/essl_f22/__init__.py`.
- [ ] Changelog updated.
- [ ] Docs updated.
- [ ] Ruff, format, mypy, pytest pass.
- [ ] `mkdocs build --strict` passes.
- [ ] `uv build` succeeds.
- [ ] `twine check` passes.
- [ ] Clean wheel install and import succeed.
- [ ] Changes merged through `dev` → `stag` → `prod`.
- [ ] Trusted publisher and `pypi` environment verified.
- [ ] Tag created on `prod` and pushed.
- [ ] Release workflow succeeded.
- [ ] PyPI install verified.
- [ ] Issue closed only after verification.

## Next

- [Development](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/contributing/development.md)
- [Compatibility](https://github.com/mramitdas/Essl_F22_SDK/blob/prod/docs/help/compatibility.md)
- [CI workflow](https://github.com/mramitdas/Essl_F22_SDK/blob/dev/.github/workflows/ci.yml)
