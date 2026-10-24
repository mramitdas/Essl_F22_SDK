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

See [Compatibility](compatibility.md) before using a new device.

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
importable in your project. Use `pip install essl_f22` or `uv add essl_f22`.

For a one-off import check:

```bash
uvx --from essl_f22 python -c "from essl_f22 import Device; print(Device)"
```

## Why do some tools show `essl-f22` instead of `essl_f22`?

PEP 503 normalization treats hyphens and underscores as equivalent. The
distribution and import name are `essl_f22`. The hyphenated spelling is a
display convention, not a different package.

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

Read [Development](../contributing/development.md) and the repository `AGENTS.md`.
Changes follow the issue → branch → PR → `dev` → `stag` → `prod` flow and must
pass tests, ruff, mypy, and documentation checks.

## Next

- [Troubleshooting](troubleshooting.md)
- [Glossary](glossary.md)
- [Compatibility](compatibility.md)
