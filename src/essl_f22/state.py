"""Compatibility module for block-state storage."""

from essl_f22.storage.base import BlockStateStore
from essl_f22.storage.models import BlockTimeZoneState
from essl_f22.storage.paths import default_state_path
from essl_f22.storage.sqlite import SqliteStorage

SqliteBlockStateStore = SqliteStorage

__all__ = [
    "BlockStateStore",
    "BlockTimeZoneState",
    "SqliteBlockStateStore",
    "default_state_path",
]
