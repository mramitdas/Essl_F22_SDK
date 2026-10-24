"""TCP transport for the eSSL F22 SDK."""

from __future__ import annotations

import socket
from typing import Protocol

from essl_f22.errors import DeviceConnectionError


class Transport(Protocol):
    """A byte-oriented connection to a device."""

    def open(self) -> None: ...

    def close(self) -> None: ...

    def send(self, data: bytes) -> None: ...

    def recv(self, size: int) -> bytes: ...


class SocketTransport:
    """A TCP socket transport."""

    def __init__(self, host: str, port: int = 4370, timeout: float = 10.0) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._socket: socket.socket | None = None

    def open(self) -> None:
        if self._socket is not None:
            return
        self._socket = socket.create_connection(
            (self._host, self._port), timeout=self._timeout
        )
        self._socket.settimeout(self._timeout)

    def close(self) -> None:
        if self._socket is None:
            return
        try:
            self._socket.close()
        finally:
            self._socket = None

    def send(self, data: bytes) -> None:
        if self._socket is None:
            raise DeviceConnectionError("transport is not open")
        self._socket.sendall(data)

    def recv(self, size: int) -> bytes:
        if self._socket is None:
            raise DeviceConnectionError("transport is not open")
        data = self._socket.recv(size)
        if not data:
            raise DeviceConnectionError("connection closed by device")
        return data
