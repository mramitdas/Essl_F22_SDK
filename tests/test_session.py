import pytest

from essl_f22.errors import DeviceAuthenticationError, DeviceTimeoutError
from essl_f22.protocol import MAX_CHUNK, build_frame, make_comm_key
from essl_f22.session import Session
from tests.fakes import FakeTransport


def test_connect_authenticates_when_unauthorized() -> None:
    unauth, _ = build_frame(2005, b"", 7, 0)
    auth_ok, _ = build_frame(2000, b"", 7, 1)
    transport = FakeTransport([unauth, auth_ok])
    session = Session("127.0.0.1", transport=transport)
    session.connect()
    assert len(transport.sent) == 2
    second = transport.sent[1]
    assert second[8:10] == b"\x4e\x04"
    assert second[16:] == make_comm_key(0, 7)


def test_connect_raises_authentication_error_on_double_unauth() -> None:
    unauth1, _ = build_frame(2005, b"", 7, 0)
    unauth2, _ = build_frame(2005, b"", 7, 1)
    transport = FakeTransport([unauth1, unauth2])
    with pytest.raises(DeviceAuthenticationError):
        Session("127.0.0.1", transport=transport).connect()


def test_send_command_updates_reply_id() -> None:
    ok, _ = build_frame(2000, b"", 3, 9)
    transport = FakeTransport([ok])
    session = Session("127.0.0.1", transport=transport)
    session.connect = lambda: None  # type: ignore[method-assign]
    session._connected = True
    response = session.send_command(50)
    assert response.reply_id == 10


def test_send_command_converts_timeout() -> None:
    class TimeoutTransport(FakeTransport):
        def recv(self, size: int) -> bytes:
            raise TimeoutError

    session = Session("127.0.0.1", transport=TimeoutTransport([]))
    session._connected = True
    with pytest.raises(DeviceTimeoutError):
        session.send_command(50)


def test_read_buffer_returns_inline_data() -> None:
    inline, _ = build_frame(1501, b"payload", 1, 1)
    session = Session("127.0.0.1", transport=FakeTransport([inline]))
    session._connected = True
    assert session.read_buffer(9, 5) == b"payload"


def test_read_buffer_prepared_data_and_free() -> None:
    size_data = b"\x00" + (7).to_bytes(4, "little") + b"\x00" * 8
    ack, _ = build_frame(2000, size_data, 1, 1)
    prepare, _ = build_frame(1500, (7).to_bytes(4, "little") + b"\x00" * 4, 1, 2)
    data, _ = build_frame(1501, b"records", 1, 3)
    ok, _ = build_frame(2000, b"", 1, 4)
    transport = FakeTransport([ack, prepare, data, ok, ok])
    session = Session("127.0.0.1", transport=transport)
    session._connected = True
    assert session.read_buffer(9, 5) == b"records"
    commands = [int.from_bytes(frame[8:10], "little") for frame in transport.sent]
    assert commands == [1503, 1504, 1502]


def test_read_buffer_reads_multiple_chunks() -> None:
    total = MAX_CHUNK + 5
    first = b"a" * MAX_CHUNK
    second = b"b" * 5
    size_data = b"\x00" + total.to_bytes(4, "little") + b"\x00" * 8
    ack, _ = build_frame(2000, size_data, 1, 1)
    data1, _ = build_frame(1501, first, 1, 2)
    data2, _ = build_frame(1501, second, 1, 3)
    free_ack, _ = build_frame(2000, b"", 1, 4)
    transport = FakeTransport([ack, data1, data2, free_ack])
    session = Session("127.0.0.1", transport=transport)
    session._connected = True
    assert session.read_buffer(9, 5) == first + second
    commands = [int.from_bytes(frame[8:10], "little") for frame in transport.sent]
    assert commands == [1503, 1504, 1504, 1502]
