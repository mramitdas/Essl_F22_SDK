"""JSON file storage backend with atomic replacement."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path

from essl_f22.errors import StateStoreError
from essl_f22.storage.codec import Document
from essl_f22.storage.document import DocumentStorage

_FILE_VERSION = 1


class JsonFileStorage(DocumentStorage):
    """A single JSON document containing all mirror and block-state namespaces."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path).expanduser()
        self._data = self._load()

    @property
    def path(self) -> Path:
        return self._path

    def _load(self) -> dict[str, dict[str, Document]]:
        try:
            text = self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {}
        except OSError as exc:
            raise StateStoreError(f"cannot read storage file {self._path}") from exc
        if not text.strip():
            return {}
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise StateStoreError(
                f"storage file {self._path} is not valid JSON"
            ) from exc
        if not isinstance(raw, dict) or raw.get("version") != _FILE_VERSION:
            raise StateStoreError(
                f"storage file {self._path} has an unsupported format"
            )
        namespaces = raw.get("namespaces")
        if not isinstance(namespaces, dict):
            raise StateStoreError(f"storage file {self._path} is missing namespaces")
        data: dict[str, dict[str, Document]] = {}
        for namespace, documents in namespaces.items():
            if not isinstance(namespace, str) or not isinstance(documents, dict):
                raise StateStoreError(
                    f"storage file {self._path} has invalid namespaces"
                )
            parsed: dict[str, Document] = {}
            for key, document in documents.items():
                if not isinstance(key, str) or not isinstance(document, dict):
                    raise StateStoreError(
                        f"storage file {self._path} has invalid records"
                    )
                parsed[key] = document
            data[namespace] = parsed
        return data

    def _save(self) -> None:
        payload = {"version": _FILE_VERSION, "namespaces": self._data}
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                dir=self._path.parent,
                prefix=f".{self._path.name}.",
                suffix=".tmp",
            )
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                    json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary_name, self._path)
            except Exception:
                try:
                    os.unlink(temporary_name)
                except FileNotFoundError:
                    pass
                raise
        except OSError as exc:
            raise StateStoreError(f"cannot write storage file {self._path}") from exc
        except (TypeError, ValueError) as exc:
            raise StateStoreError(
                f"cannot serialize storage file {self._path}"
            ) from exc

    def read_document(self, namespace: str, key: str) -> Document | None:
        document = self._data.get(namespace, {}).get(key)
        return None if document is None else deepcopy(document)

    def write_document(
        self, namespace: str, key: str, document: Mapping[str, object]
    ) -> None:
        self._data.setdefault(namespace, {})[key] = deepcopy(dict(document))
        self._save()

    def delete_document(self, namespace: str, key: str) -> None:
        documents = self._data.get(namespace)
        if documents is None:
            return
        documents.pop(key, None)
        if not documents:
            self._data.pop(namespace, None)
        self._save()

    def list_documents(self, namespace: str) -> dict[str, Document]:
        return {
            key: deepcopy(document)
            for key, document in self._data.get(namespace, {}).items()
        }

    def replace_documents(
        self, namespace: str, documents: Mapping[str, Mapping[str, object]]
    ) -> None:
        if documents:
            self._data[namespace] = {
                key: deepcopy(dict(document)) for key, document in documents.items()
            }
        else:
            self._data.pop(namespace, None)
        self._save()

    def upsert_documents(
        self, namespace: str, documents: Mapping[str, Mapping[str, object]]
    ) -> int:
        existing = self._data.setdefault(namespace, {})
        new_keys = set(documents) - set(existing)
        for key, document in documents.items():
            existing[key] = deepcopy(dict(document))
        self._save()
        return len(new_keys)

    def clear_namespace(self, namespace: str) -> None:
        self._data.pop(namespace, None)
        self._save()

    def close(self) -> None:
        return None
