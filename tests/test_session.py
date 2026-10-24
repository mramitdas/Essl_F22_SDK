import pytest

from essl_f22.errors import DeviceAuthenticationError, DeviceTimeoutError
from essl_f22.protocol import build_frame, make_comm_key
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
