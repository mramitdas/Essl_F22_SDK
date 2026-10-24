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

- [Access control and blocking](access-control.md)
- [Mirror and storage](mirror-and-storage.md)
- [Models reference](../reference/models.md#fingerprinttemplate)
