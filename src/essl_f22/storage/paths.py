"""Platform-specific default storage locations."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_APP_DIRECTORY = "essl_f22"
_STATE_FILE = "state.db"
_MIRROR_FILE = "mirror.json"


def default_data_dir() -> Path:
    """Return the platform-appropriate application data directory."""

    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        base = (
            Path(local_app_data)
            if local_app_data
            else Path.home() / "AppData" / "Local"
        )
        return base / _APP_DIRECTORY
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / _APP_DIRECTORY
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data_home) if xdg_data_home else Path.home() / ".local" / "share"
    return base / _APP_DIRECTORY


def default_state_path() -> Path:
    """Return the default SQLite block-state path."""

    return default_data_dir() / _STATE_FILE


def default_mirror_path() -> Path:
    """Return the default JSON mirror path."""

    return default_data_dir() / _MIRROR_FILE
