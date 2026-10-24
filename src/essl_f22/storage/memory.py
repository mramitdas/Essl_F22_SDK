"""In-memory storage backend."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from essl_f22.storage.codec import Document
from essl_f22.storage.document import DocumentStorage


class MemoryStorage(DocumentStorage):
    """A process-local storage backend. Data is lost when the process exits."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, Document]] = {}

    def read_document(self, namespace: str, key: str) -> Document | None:
        document = self._data.get(namespace, {}).get(key)
        return None if document is None else deepcopy(document)

    def write_document(
        self, namespace: str, key: str, document: Mapping[str, object]
    ) -> None:
        self._data.setdefault(namespace, {})[key] = deepcopy(dict(document))

    def delete_document(self, namespace: str, key: str) -> None:
        documents = self._data.get(namespace)
        if documents is None:
            return
        documents.pop(key, None)
        if not documents:
            self._data.pop(namespace, None)

    def list_documents(self, namespace: str) -> dict[str, Document]:
        return {
            key: deepcopy(document)
            for key, document in self._data.get(namespace, {}).items()
        }

    def replace_documents(
        self, namespace: str, documents: Mapping[str, Mapping[str, object]]
    ) -> None:
        self._data[namespace] = {
            key: deepcopy(dict(document)) for key, document in documents.items()
        }

    def upsert_documents(
        self, namespace: str, documents: Mapping[str, Mapping[str, object]]
    ) -> int:
        existing = self._data.setdefault(namespace, {})
        new_keys = set(documents) - set(existing)
        for key, document in documents.items():
            existing[key] = deepcopy(dict(document))
        return len(new_keys)

    def clear_namespace(self, namespace: str) -> None:
        self._data.pop(namespace, None)

    def close(self) -> None:
        return None
