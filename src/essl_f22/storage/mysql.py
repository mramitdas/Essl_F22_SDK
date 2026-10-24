"""MySQL storage backend using a JSON document table."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any
from urllib.parse import unquote, urlparse

from essl_f22.errors import StateStoreError, StorageConfigurationError
from essl_f22.storage.codec import (
    Document,
    document_from_json,
    document_to_json,
)
from essl_f22.storage.document import DocumentStorage

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    namespace VARCHAR(255) NOT NULL,
    key_name VARCHAR(255) NOT NULL,
    payload LONGTEXT NOT NULL,
    PRIMARY KEY (namespace, key_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

_INSERT = "INSERT INTO documents (namespace, key_name, payload) VALUES (%s, %s, %s)"

_UPSERT = """
INSERT INTO documents (namespace, key_name, payload)
VALUES (%s, %s, %s)
ON DUPLICATE KEY UPDATE payload = VALUES(payload)
"""

_INSERT_IGNORE = (
    "INSERT IGNORE INTO documents (namespace, key_name, payload) VALUES (%s, %s, %s)"
)


def _parse_dsn(dsn: str) -> dict[str, Any]:
    parsed = urlparse(dsn)
    if parsed.scheme not in ("mysql", "mysql+pymysql"):
        raise StorageConfigurationError("MySQL storage DSN must use mysql://")
    database = unquote(parsed.path.lstrip("/"))
    if not database:
        raise StorageConfigurationError("MySQL storage DSN must include a database")
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": database,
        "charset": "utf8mb4",
        "autocommit": False,
    }


class MysqlStorage(DocumentStorage):
    """A MySQL-backed storage backend."""

    def __init__(self, dsn: str) -> None:
        try:
            import pymysql
        except ImportError as exc:
            raise StorageConfigurationError(
                "MySQL storage requires pymysql from the 'mysql' extra: "
                "install Essl_F22_SDK[mysql]"
            ) from exc
        self._driver: Any = pymysql
        self._error: Any = pymysql.err.MySQLError
        self._config = _parse_dsn(dsn)
        self._closed = False
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(_SCHEMA)
        except self._error as exc:
            raise StateStoreError("cannot initialize MySQL storage") from exc

    @contextmanager
    def _connect(self) -> Iterator[Any]:
        if self._closed:
            raise StateStoreError("MySQL storage is closed")
        connection = self._driver.connect(**self._config)
        try:
            yield connection
        except BaseException:
            connection.rollback()
            raise
        else:
            connection.commit()
        finally:
            if connection.open:
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
            raise StateStoreError("cannot read from MySQL storage") from exc
        if row is None:
            return None
        return document_from_json(row[0])

    def write_document(
        self, namespace: str, key: str, document: Mapping[str, object]
    ) -> None:
        payload = document_to_json(dict(document))
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(_UPSERT, (namespace, key, payload))
        except self._error as exc:
            raise StateStoreError("cannot write to MySQL storage") from exc

    def delete_document(self, namespace: str, key: str) -> None:
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM documents WHERE namespace = %s AND key_name = %s",
                        (namespace, key),
                    )
        except self._error as exc:
            raise StateStoreError("cannot delete from MySQL storage") from exc

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
            raise StateStoreError("cannot list MySQL storage records") from exc
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
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM documents WHERE namespace = %s", (namespace,)
                    )
                    if rows:
                        cursor.executemany(_INSERT, rows)
        except self._error as exc:
            raise StateStoreError("cannot replace MySQL storage records") from exc

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
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT key_name FROM documents WHERE namespace = %s",
                        (namespace,),
                    )
                    existing = {row[0] for row in cursor.fetchall()}
                    if rows:
                        cursor.executemany(_INSERT_IGNORE, rows)
        except self._error as exc:
            raise StateStoreError("cannot upsert MySQL storage records") from exc
        return len(set(unique_documents) - existing)

    def clear_namespace(self, namespace: str) -> None:
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM documents WHERE namespace = %s", (namespace,)
                    )
        except self._error as exc:
            raise StateStoreError("cannot clear MySQL storage namespace") from exc

    def close(self) -> None:
        self._closed = True
