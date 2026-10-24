"""SQLite storage backend using a JSON document table."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

from essl_f22.errors import StateStoreError
from essl_f22.storage.codec import (
    Document,
    document_from_json,
    document_to_json,
)
from essl_f22.storage.document import DocumentStorage

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    namespace TEXT NOT NULL,
    key TEXT NOT NULL,
    payload TEXT NOT NULL,
    PRIMARY KEY (namespace, key)
)
"""

_INSERT = "INSERT INTO documents (namespace, key, payload) VALUES (?, ?, ?)"

_UPSERT = """
INSERT INTO documents (namespace, key, payload)
VALUES (?, ?, ?)
ON CONFLICT (namespace, key) DO UPDATE SET payload = excluded.payload
"""

_INSERT_IGNORE = """
INSERT INTO documents (namespace, key, payload)
VALUES (?, ?, ?)
ON CONFLICT (namespace, key) DO NOTHING
"""


class SqliteStorage(DocumentStorage):
    """A durable local storage backend. This is the default SDK backend."""

    def __init__(self, path: Path | str) -> None:
        self._memory = str(path) == ":memory:"
        self._path: Path | None = None
        self._memory_connection: sqlite3.Connection | None = None
        if self._memory:
            self._memory_connection = sqlite3.connect(":memory:")
        else:
            self._path = Path(path).expanduser()
            self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._connect() as connection:
                with connection:
                    connection.execute(_SCHEMA)
        except sqlite3.Error as exc:
            raise StateStoreError(f"cannot initialize SQLite storage {path}") from exc

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        if self._memory_connection is not None:
            yield self._memory_connection
            return
        if self._path is None:
            raise StateStoreError("SQLite storage has no path")
        try:
            connection = sqlite3.connect(self._path)
        except sqlite3.Error as exc:
            raise StateStoreError(f"cannot open SQLite storage {self._path}") from exc
        try:
            yield connection
        finally:
            connection.close()

    def read_document(self, namespace: str, key: str) -> Document | None:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT payload FROM documents WHERE namespace = ? AND key = ?",
                    (namespace, key),
                ).fetchone()
        except sqlite3.Error as exc:
            raise StateStoreError("cannot read from SQLite storage") from exc
        if row is None:
            return None
        return document_from_json(row[0])

    def write_document(
        self, namespace: str, key: str, document: Mapping[str, object]
    ) -> None:
        payload = document_to_json(dict(document))
        try:
            with self._connect() as connection:
                with connection:
                    connection.execute(_UPSERT, (namespace, key, payload))
        except sqlite3.Error as exc:
            raise StateStoreError("cannot write to SQLite storage") from exc

    def delete_document(self, namespace: str, key: str) -> None:
        try:
            with self._connect() as connection:
                with connection:
                    connection.execute(
                        "DELETE FROM documents WHERE namespace = ? AND key = ?",
                        (namespace, key),
                    )
        except sqlite3.Error as exc:
            raise StateStoreError("cannot delete from SQLite storage") from exc

    def list_documents(self, namespace: str) -> dict[str, Document]:
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    "SELECT key, payload FROM documents WHERE namespace = ?",
                    (namespace,),
                ).fetchall()
        except sqlite3.Error as exc:
            raise StateStoreError("cannot list SQLite storage records") from exc
        return {row[0]: document_from_json(row[1]) for row in rows}

    def replace_documents(
        self, namespace: str, documents: Mapping[str, Mapping[str, object]]
    ) -> None:
        rows = [
            (namespace, key, document_to_json(dict(document)))
            for key, document in documents.items()
        ]
        try:
            with self._connect() as connection:
                with connection:
                    connection.execute(
                        "DELETE FROM documents WHERE namespace = ?", (namespace,)
                    )
                    if rows:
                        connection.executemany(_INSERT, rows)
        except sqlite3.Error as exc:
            raise StateStoreError("cannot replace SQLite storage records") from exc

    def upsert_documents(
        self, namespace: str, documents: Mapping[str, Mapping[str, object]]
    ) -> int:
        unique_documents = dict(documents)
        rows = [
            (namespace, key, document_to_json(dict(document)))
            for key, document in unique_documents.items()
        ]
        try:
            with self._connect() as connection:
                with connection:
                    existing = {
                        row[0]
                        for row in connection.execute(
                            "SELECT key FROM documents WHERE namespace = ?",
                            (namespace,),
                        ).fetchall()
                    }
                    if rows:
                        connection.executemany(_INSERT_IGNORE, rows)
        except sqlite3.Error as exc:
            raise StateStoreError("cannot upsert SQLite storage records") from exc
        return len(set(unique_documents) - existing)

    def clear_namespace(self, namespace: str) -> None:
        try:
            with self._connect() as connection:
                with connection:
                    connection.execute(
                        "DELETE FROM documents WHERE namespace = ?", (namespace,)
                    )
        except sqlite3.Error as exc:
            raise StateStoreError("cannot clear SQLite storage namespace") from exc

    def close(self) -> None:
        if self._memory_connection is not None:
            self._memory_connection.close()
            self._memory_connection = None
