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
trusted, segmented network. See [Protocol internals](../reference/protocol.md) if
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

See [Attendance](attendance.md) for the operational consequences.

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

- [Users](users.md)
- [Attendance](attendance.md)
- [Fingerprints](fingerprints.md)
- [Access control and blocking](access-control.md)
- [Mirror and storage](mirror-and-storage.md)
