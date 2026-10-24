"""Pluggable local storage for block state and the offline mirror."""

from essl_f22.storage.base import BlockStateStore, MirrorStore, StorageBackend
from essl_f22.storage.factory import create_storage
from essl_f22.storage.jsonfile import JsonFileStorage
from essl_f22.storage.memory import MemoryStorage
from essl_f22.storage.models import (
    AttendanceEntry,
    BlockTimeZoneState,
    FingerprintMetadata,
    SyncMode,
    SyncResult,
    SyncState,
)
from essl_f22.storage.mysql import MysqlStorage
from essl_f22.storage.paths import (
    default_data_dir,
    default_mirror_path,
    default_state_path,
)
from essl_f22.storage.postgres import PostgresStorage
from essl_f22.storage.sqlite import SqliteStorage

__all__ = [
    "AttendanceEntry",
    "BlockStateStore",
    "BlockTimeZoneState",
    "FingerprintMetadata",
    "JsonFileStorage",
    "MemoryStorage",
    "MirrorStore",
    "MysqlStorage",
    "PostgresStorage",
    "SqliteStorage",
    "StorageBackend",
    "SyncMode",
    "SyncResult",
    "SyncState",
    "create_storage",
    "default_data_dir",
    "default_mirror_path",
    "default_state_path",
]
