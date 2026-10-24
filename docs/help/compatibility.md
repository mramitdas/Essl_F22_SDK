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
[Storage](../reference/storage.md#default-paths).

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

- [FAQ](faq.md)
- [Troubleshooting](troubleshooting.md)
- [Production checklist](../guides/production-checklist.md)
