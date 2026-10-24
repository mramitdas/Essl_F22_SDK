from essl_f22.protocol import checksum, make_comm_key


def test_checksum_matches_device_compatible_variant() -> None:
    header = bytes.fromhex("e80300000000feff")
    assert checksum(header) == 0xFC17


def test_make_comm_key_for_zero_key_and_session() -> None:
    assert make_comm_key(0, 0) == bytes.fromhex("617d3279")
