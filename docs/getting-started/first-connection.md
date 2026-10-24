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

!!! note "What the context manager does"
    `Device(...)` constructs the client but does not open the socket. Entering
    the `with` block calls `connect()`. Leaving the block calls `close()` even
    if an exception occurred. Use the context manager unless you have a good
    reason to manage the lifecycle manually.

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

See [Troubleshooting](../help/troubleshooting.md) for deeper diagnosis.

## Next step

Now that you can connect read-only, run the guided end-to-end example:
[Quickstart](quickstart.md).
