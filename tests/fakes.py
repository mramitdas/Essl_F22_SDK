from collections import deque

from essl_f22.protocol import Response
from essl_f22.transport import Transport


class FakeTransport(Transport):
    def __init__(self, responses: list[bytes]) -> None:
        self.responses = deque(responses)
        self.sent: list[bytes] = []
        self.closed = False

    def open(self) -> None: ...

    def send(self, data: bytes) -> None:
        self.sent.append(data)

    def recv(self, size: int) -> bytes:
        return self.responses.popleft()

    def close(self) -> None:
        self.closed = True


class FakeSession:
    def __init__(
        self,
        responses: dict[int, Response],
        buffers: dict[tuple[int, int], bytes] | None = None,
    ) -> None:
        self.responses = responses
        self.buffers = buffers or {}
        self.calls: list[tuple[int, bytes]] = []

    def connect(self) -> None: ...

    def close(self) -> None: ...

    def send_command(
        self, command: int, data: bytes = b"", response_size: int = 8
    ) -> Response:
        self.calls.append((command, data))
        return self.responses[command]

    def read_buffer(self, command: int, fct: int = 0, ext: int = 0) -> bytes:
        self.calls.append((command, bytes([fct, ext])))
        if (command, fct) in self.buffers:
            return self.buffers[(command, fct)]
        return self.responses[command].data

    def refresh_data(self) -> None:
        self.calls.append((1013, b""))
