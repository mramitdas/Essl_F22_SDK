"""Storage backend selection."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from essl_f22.errors import StorageConfigurationError
from essl_f22.storage.base import StorageBackend
from essl_f22.storage.jsonfile import JsonFileStorage
from essl_f22.storage.memory import MemoryStorage
from essl_f22.storage.paths import default_mirror_path, default_state_path
from essl_f22.storage.sqlite import SqliteStorage


def create_storage(
    backend: str = "sqlite",
    *,
    path: Path | str | None = None,
    options: Mapping[str, Any] | None = None,
) -> StorageBackend:
    """Create a built-in storage backend by name."""

    del options
    name = backend.lower()
    if name == "memory":
        return MemoryStorage()
    if name == "json":
        return JsonFileStorage(path or default_mirror_path())
    if name == "sqlite":
        return SqliteStorage(path or default_state_path())
    raise StorageConfigurationError(f"unsupported storage backend {backend!r}")
