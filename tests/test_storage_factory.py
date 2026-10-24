import sys
from pathlib import Path

import pytest

from essl_f22.errors import StateStoreError, StorageConfigurationError
from essl_f22.state import (
    BlockStateStore,
    SqliteBlockStateStore,
    default_state_path,
)
from essl_f22.storage import (
    JsonFileStorage,
    MemoryStorage,
    SqliteStorage,
    create_storage,
    default_data_dir,
    default_mirror_path,
)


def test_create_storage_selects_builtins(tmp_path: Path) -> None:
    assert isinstance(create_storage("memory"), MemoryStorage)
    assert isinstance(
        create_storage("json", path=tmp_path / "mirror.json"), JsonFileStorage
    )
    assert isinstance(
        create_storage("sqlite", path=tmp_path / "state.db"), SqliteStorage
    )


def test_create_storage_rejects_unknown_backend() -> None:
    with pytest.raises(StorageConfigurationError):
        create_storage("unknown")


def test_state_module_is_a_compatibility_shim() -> None:
    assert SqliteBlockStateStore is SqliteStorage
    assert BlockStateStore is not None


def test_default_state_path_uses_xdg_data_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))

    assert default_state_path() == tmp_path / "essl_f22" / "state.db"
    assert default_mirror_path() == tmp_path / "essl_f22" / "mirror.json"
    assert default_data_dir() == tmp_path / "essl_f22"


def test_default_state_path_uses_macos_application_support(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setenv("HOME", str(tmp_path))

    assert (
        default_state_path()
        == tmp_path / "Library" / "Application Support" / "essl_f22" / "state.db"
    )


def test_default_state_path_uses_localappdata_on_windows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert default_state_path() == tmp_path / "essl_f22" / "state.db"


def test_sqlite_batch_replace_does_not_leave_partial_data(tmp_path: Path) -> None:
    storage = SqliteStorage(tmp_path / "state.db")
    storage.replace_documents("example", {"a": {"value": 1}})

    with pytest.raises(StateStoreError):
        storage.replace_documents(
            "example", {"b": {"value": 2}, "c": {"value": object()}}
        )

    assert storage.list_documents("example") == {"a": {"value": 1}}
    storage.close()


def test_sqlite_memory_path_is_supported() -> None:
    storage = SqliteStorage(":memory:")
    storage.save_block_timezone("JJA1242200334", 50)

    assert storage.get_block_timezone("JJA1242200334") is not None
    storage.close()


def test_json_rejects_malformed_file(tmp_path: Path) -> None:
    path = tmp_path / "mirror.json"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(StateStoreError):
        JsonFileStorage(path)


def test_json_rejects_unsupported_file_version(tmp_path: Path) -> None:
    path = tmp_path / "mirror.json"
    path.write_text('{"version": 2, "namespaces": {}}', encoding="utf-8")

    with pytest.raises(StateStoreError):
        JsonFileStorage(path)


def test_json_atomic_save_keeps_previous_file_on_replace_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "mirror.json"
    storage = JsonFileStorage(path)
    storage.save_block_timezone("JJA1242200334", 50)
    original = path.read_text(encoding="utf-8")

    def fail_replace(source: object, destination: object) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr("essl_f22.storage.jsonfile.os.replace", fail_replace)

    with pytest.raises(StateStoreError):
        storage.save_block_timezone("JJA1242200334", 49)

    assert path.read_text(encoding="utf-8") == original
    assert JsonFileStorage(path).get_block_timezone("JJA1242200334") is not None
