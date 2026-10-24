import os

import pytest

from essl_f22 import Device
from essl_f22.storage import MemoryStorage

HOST = os.environ.get("ESSL_F22_HOST")

pytestmark = [
    pytest.mark.hardware,
    pytest.mark.skipif(not HOST, reason="ESSL_F22_HOST is not set"),
]


def test_read_only_mirror_matches_device() -> None:
    assert HOST is not None
    port = int(os.environ.get("ESSL_F22_PORT", "4370"))
    comm_key = int(os.environ.get("ESSL_F22_COMM_KEY", "0"))
    encoding = os.environ.get("ESSL_F22_ENCODING", "utf-8")
    timeout = float(os.environ.get("ESSL_F22_TIMEOUT", "30"))

    with Device(
        HOST,
        port,
        comm_key=comm_key,
        encoding=encoding,
        timeout=timeout,
        storage=MemoryStorage(),
    ) as device:
        result = device.sync("full")
        mirror = device.mirror()
        snapshot = mirror.snapshot()

        users = device.list_users()
        groups = device.list_groups()
        timezones = device.list_timezones()
        templates = device.list_fingerprints()
        sizes = device.get_free_sizes()

        assert mirror.device_serial == device.get_serial_number()
        assert snapshot.device_info == device.get_device_info()
        assert result.users == len(users) == len(snapshot.users)
        assert result.groups == len(groups) == len(snapshot.groups)
        assert result.timezones == len(timezones) == len(snapshot.timezones)
        assert result.fingerprints == len(templates) == len(snapshot.fingerprints)
        assert result.attendance == sizes.attendance
        assert result.attendance == len(snapshot.attendance)
        assert result.attendance_replaced is True
        assert result.new_attendance == result.attendance
        assert snapshot.sync_state is not None
        assert snapshot.sync_state.mode == "full"
        assert snapshot.sync_state.attendance == result.attendance

        if users:
            assert mirror.get_user(users[0].uid) == users[0]

        known_user = next((user for user in users if user.uid == 295), None)
        if known_user is not None:
            assert mirror.get_user(295) == known_user

        if templates:
            first = templates[0]
            assert any(
                metadata.uid == first.uid
                and metadata.fid == first.fid
                and metadata.flag == first.flag
                and metadata.size == first.size
                for metadata in snapshot.fingerprints
            )

        known_fingerprint = next(
            (
                template
                for template in templates
                if template.uid == 295 and template.fid == 9
            ),
            None,
        )
        if known_fingerprint is not None:
            metadata = [
                item
                for item in snapshot.fingerprints
                if item.uid == 295 and item.fid == 9
            ]
            assert len(metadata) == 1
            assert metadata[0].flag == known_fingerprint.flag
            assert metadata[0].size == known_fingerprint.size
