from collections import deque

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
