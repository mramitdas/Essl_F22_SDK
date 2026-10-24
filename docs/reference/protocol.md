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

- [Device API](device-api.md)
- [Models](models.md)
- [Troubleshooting](../help/troubleshooting.md)
