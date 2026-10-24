# Glossary

Plain-language definitions for terms used in this handbook.

**Essl F22 SDK**<br>
The Python library described by this handbook. Its distribution and import name
is `essl_f22`.

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
An optional dependency group, such as `essl_f22[postgres]`.

**PEP 503**<br>
The Python packaging normalization rule that treats `-` and `_` as equivalent in
project names. It is why tools may display `essl-f22`.

**uv**<br>
A Python package and environment manager used by this project.

**pipx / uvx**<br>
Tools for running applications in isolated environments. They do not make a
library importable in your project.

## Next

- [FAQ](faq.md)
- [Compatibility](compatibility.md)
- [Troubleshooting](troubleshooting.md)
