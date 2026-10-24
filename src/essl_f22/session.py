"""Device session handling connect, authentication, and commands."""

from __future__ import annotations

import struct
from typing import Self

from essl_f22.errors import (
    CommandError,
    DeviceAuthenticationError,
    DeviceConnectionError,
    DeviceTimeoutError,
    ProtocolError,
)
from essl_f22.protocol import (
    CMD_ACK_OK,
    CMD_ACK_UNAUTH,
    CMD_AUTH,
    CMD_CONNECT,
    CMD_REFRESHDATA,
    MACHINE_PREPARE_DATA_1,
    MACHINE_PREPARE_DATA_2,
    Response,
    build_frame,
    make_comm_key,
    parse_frame,
)
from essl_f22.transport import SocketTransport, Transport


class Session:
    """A connected device session."""

    def __init__(
        self,
        host: str,
        port: int = 4370,
        timeout: float = 10.0,
        comm_key: int = 0,
        transport: Transport | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._comm_key = comm_key
        self._transport = transport
        self._session_id = 0
        self._reply_id = 0
        self._connected = False
        self._recv_buffer = bytearray()

    def connect(self) -> None:
        if self._connected:
            return
        if self._transport is None:
            self._transport = SocketTransport(self._host, self._port, self._timeout)

        try:
            try:
                self._transport.open()
            except TimeoutError as exc:
                raise DeviceTimeoutError("device connection timed out") from exc
            except OSError as exc:
                raise DeviceConnectionError(str(exc)) from exc
            self._session_id = 0
            self._reply_id = 0xFFFF - 1
            response = self._send_and_receive(CMD_CONNECT)

            if response.command == CMD_ACK_OK:
                self._session_id = response.session_id
                self._connected = True
                return

            if response.command != CMD_ACK_UNAUTH:
                raise DeviceAuthenticationError(
                    f"unexpected connect response 0x{response.command:04X}"
                )

            self._session_id = response.session_id
            auth_response = self._send_and_receive(
                CMD_AUTH,
                make_comm_key(self._comm_key, self._session_id),
            )
            if auth_response.command != CMD_ACK_OK:
                raise DeviceAuthenticationError(
                    f"authentication rejected with 0x{auth_response.command:04X}"
                )
            self._session_id = auth_response.session_id
            self._connected = True
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        self._connected = False
        self._recv_buffer.clear()
        if self._transport is not None:
            self._transport.close()

    def send_command(
        self, command: int, data: bytes = b"", response_size: int = 8
    ) -> Response:
        del response_size
        if not self._connected:
            raise DeviceConnectionError("session is not connected")
        return self._send_and_receive(command, data)

    def refresh_data(self) -> None:
        response = self.send_command(CMD_REFRESHDATA)
        if response.command != CMD_ACK_OK:
            raise CommandError(response.command)

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def _send_and_receive(self, command: int, data: bytes = b"") -> Response:
        if self._transport is None:
            raise DeviceConnectionError("session has no transport")

        try:
            frame, self._reply_id = build_frame(
                command, data, self._session_id, self._reply_id
            )
            self._transport.send(frame)
            return self._read_frame()
        except TimeoutError as exc:
            raise DeviceTimeoutError("device operation timed out") from exc
        except OSError as exc:
            raise DeviceConnectionError(str(exc)) from exc
        except struct.error as exc:
            raise ProtocolError("malformed device frame") from exc

    def _read_frame(self) -> Response:
        header = self._read_exact(8)
        magic_1, magic_2, payload_length = struct.unpack("<HHI", header)
        if magic_1 != MACHINE_PREPARE_DATA_1 or magic_2 != MACHINE_PREPARE_DATA_2:
            raise ProtocolError("invalid frame magic")
        payload = self._read_exact(payload_length)
        return parse_frame(header + payload)

    def _read_exact(self, size: int) -> bytes:
        if self._transport is None:
            raise DeviceConnectionError("session has no transport")
        while len(self._recv_buffer) < size:
            chunk = self._transport.recv(size - len(self._recv_buffer))
            if not chunk:
                raise DeviceConnectionError("connection closed by device")
            self._recv_buffer.extend(chunk)
        data = bytes(self._recv_buffer[:size])
        del self._recv_buffer[:size]
        return data
