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
python -m pip install essl_f22
# or
uv add essl_f22
```

If you are before the first public release, install the built wheel explicitly.
See [Installation](../getting-started/installation.md).

## The package name looks wrong

`pip` and `uv` may display `essl-f22` because package normalization treats `-`
and `_` as equivalent. The distribution and import name are `essl_f22`. Check
with:

```bash
python -m pip show essl_f22
python -c "import essl_f22; print(essl_f22.__file__)"
```

If both commands find the package, the hyphen is only a display convention.

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

Read [Users](../concepts/users.md#field-length-limits) for the limits.

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

- Install the matching extra: `essl_f22[postgres]`, `[mysql]`, `[mongo]`, or
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

- `essl_f22` version;
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

- [FAQ](faq.md)
- [Compatibility](compatibility.md)
- [Handle errors](../guides/handle-errors.md)
