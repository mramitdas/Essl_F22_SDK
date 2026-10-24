"""PostgreSQL storage backend using a JSON document table."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any

from essl_f22.errors import StateStoreError, StorageConfigurationError
from essl_f22.storage.codec import (
    Document,
    document_from_json,
    document_to_json,
)
from essl_f22.storage.document import DocumentStorage

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    namespace TEXT NOT NULL,
    key_name TEXT NOT NULL,
    payload TEXT NOT NULL,
    PRIMARY KEY (namespace, key_name)
)
"""

_INSERT = "INSERT INTO documents (namespace, key_name, payload) VALUES (%s, %s, %s)"

_UPSERT = """
INSERT INTO documents (namespace, key_name, payload)
VALUES (%s, %s, %s)
ON CONFLICT (namespace, key_name) DO UPDATE SET payload = EXCLUDED.payload
"""

_INSERT_IGNORE = """
INSERT INTO documents (namespace, key_name, payload)
VALUES (%s, %s, %s)
ON CONFLICT (namespace, key_name) DO NOTHING
"""


class PostgresStorage(DocumentStorage):
    """A PostgreSQL-backed storage backend."""

    def __init__(self, dsn: str) -> None:
        try:
            import psycopg
        except ImportError as exc:
            raise StorageConfigurationError(
                "PostgreSQL storage requires psycopg from the 'postgres' extra: "
                "install essl_f22[postgres]"
            ) from exc
        self._driver: Any = psycopg
        self._error: Any = psycopg.Error
        self._dsn = dsn
        self._closed = False
        try:
            with self._connect() as connection:
                with connection:
                    with connection.cursor() as cursor:
                        cursor.execute(_SCHEMA)
        except self._error as exc:
            raise StateStoreError("cannot initialize PostgreSQL storage") from exc

    @contextmanager
    def _connect(self) -> Iterator[Any]:
        if self._closed:
            raise StateStoreError("PostgreSQL storage is closed")
        connection = self._driver.connect(self._dsn)
        try:
            yield connection
        finally:
            connection.close()

    def read_document(self, namespace: str, key: str) -> Document | None:
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT payload FROM documents "
                        "WHERE namespace = %s AND key_name = %s",
                        (namespace, key),
                    )
                    row = cursor.fetchone()
        except self._error as exc:
            raise StateStoreError("cannot read from PostgreSQL storage") from exc
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
                    with connection.cursor() as cursor:
                        cursor.execute(_UPSERT, (namespace, key, payload))
        except self._error as exc:
            raise StateStoreError("cannot write to PostgreSQL storage") from exc

    def delete_document(self, namespace: str, key: str) -> None:
        try:
            with self._connect() as connection:
                with connection:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "DELETE FROM documents "
                            "WHERE namespace = %s AND key_name = %s",
                            (namespace, key),
                        )
        except self._error as exc:
            raise StateStoreError("cannot delete from PostgreSQL storage") from exc

    def list_documents(self, namespace: str) -> dict[str, Document]:
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT key_name, payload FROM documents WHERE namespace = %s",
                        (namespace,),
                    )
                    rows = cursor.fetchall()
        except self._error as exc:
            raise StateStoreError("cannot list PostgreSQL storage records") from exc
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
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "DELETE FROM documents WHERE namespace = %s", (namespace,)
                        )
                        if rows:
                            cursor.executemany(_INSERT, rows)
        except self._error as exc:
            raise StateStoreError("cannot replace PostgreSQL storage records") from exc

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
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT key_name FROM documents WHERE namespace = %s",
                            (namespace,),
                        )
                        existing = {row[0] for row in cursor.fetchall()}
                        if rows:
                            cursor.executemany(_INSERT_IGNORE, rows)
        except self._error as exc:
            raise StateStoreError("cannot upsert PostgreSQL storage records") from exc
        return len(set(unique_documents) - existing)

    def clear_namespace(self, namespace: str) -> None:
        try:
            with self._connect() as connection:
                with connection:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "DELETE FROM documents WHERE namespace = %s", (namespace,)
                        )
        except self._error as exc:
            raise StateStoreError("cannot clear PostgreSQL storage namespace") from exc

    def close(self) -> None:
        self._closed = True
