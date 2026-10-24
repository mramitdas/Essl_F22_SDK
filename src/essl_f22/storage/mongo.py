"""MongoDB storage backend using a JSON document collection."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from essl_f22.errors import StateStoreError, StorageConfigurationError
from essl_f22.storage.codec import (
    Document,
    document_from_json,
    document_to_json,
)
from essl_f22.storage.document import DocumentStorage


class MongoStorage(DocumentStorage):
    """A MongoDB-backed storage backend."""

    def __init__(self, uri: str) -> None:
        try:
            import pymongo
        except ImportError as exc:
            raise StorageConfigurationError(
                "MongoDB storage requires pymongo from the 'mongo' extra: "
                "install essl_f22[mongo]"
            ) from exc
        self._driver: Any = pymongo
        self._error: Any = pymongo.errors.PyMongoError
        self._closed = False
        try:
            self._client: Any = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        except pymongo.errors.ConfigurationError as exc:
            raise StorageConfigurationError("invalid MongoDB URI") from exc
        try:
            database = self._client.get_default_database()
        except pymongo.errors.ConfigurationError as exc:
            self._client.close()
            raise StorageConfigurationError(
                "MongoDB URI must include a database"
            ) from exc
        self._collection = database["documents"]
        try:
            self._collection.create_index(
                [("namespace", 1), ("key_name", 1)], unique=True
            )
        except self._error as exc:
            self._client.close()
            raise StateStoreError("cannot initialize MongoDB storage") from exc

    def _check_open(self) -> None:
        if self._closed:
            raise StateStoreError("MongoDB storage is closed")

    def read_document(self, namespace: str, key: str) -> Document | None:
        self._check_open()
        try:
            row = self._collection.find_one(
                {"namespace": namespace, "key_name": key}, {"_id": 0, "payload": 1}
            )
        except self._error as exc:
            raise StateStoreError("cannot read from MongoDB storage") from exc
        if row is None:
            return None
        return document_from_json(row["payload"])

    def write_document(
        self, namespace: str, key: str, document: Mapping[str, object]
    ) -> None:
        self._check_open()
        payload = document_to_json(dict(document))
        try:
            self._collection.update_one(
                {"namespace": namespace, "key_name": key},
                {"$set": {"payload": payload}},
                upsert=True,
            )
        except self._error as exc:
            raise StateStoreError("cannot write to MongoDB storage") from exc

    def delete_document(self, namespace: str, key: str) -> None:
        self._check_open()
        try:
            self._collection.delete_one({"namespace": namespace, "key_name": key})
        except self._error as exc:
            raise StateStoreError("cannot delete from MongoDB storage") from exc

    def list_documents(self, namespace: str) -> dict[str, Document]:
        self._check_open()
        try:
            rows = self._collection.find(
                {"namespace": namespace},
                {"_id": 0, "key_name": 1, "payload": 1},
            )
            return {row["key_name"]: document_from_json(row["payload"]) for row in rows}
        except self._error as exc:
            raise StateStoreError("cannot list MongoDB storage records") from exc

    def replace_documents(
        self, namespace: str, documents: Mapping[str, Mapping[str, object]]
    ) -> None:
        self._check_open()
        rows = [
            {
                "namespace": namespace,
                "key_name": key,
                "payload": document_to_json(dict(document)),
            }
            for key, document in documents.items()
        ]
        try:
            self._collection.delete_many({"namespace": namespace})
            if rows:
                self._collection.insert_many(rows)
        except self._error as exc:
            raise StateStoreError("cannot replace MongoDB storage records") from exc

    def upsert_documents(
        self, namespace: str, documents: Mapping[str, Mapping[str, object]]
    ) -> int:
        self._check_open()
        unique_documents = dict(documents)
        if not unique_documents:
            return 0
        keys = list(unique_documents)
        try:
            existing = {
                row["key_name"]
                for row in self._collection.find(
                    {"namespace": namespace, "key_name": {"$in": keys}},
                    {"_id": 0, "key_name": 1},
                )
            }
            operations = [
                self._driver.UpdateOne(
                    {"namespace": namespace, "key_name": key},
                    {"$set": {"payload": document_to_json(dict(document))}},
                    upsert=True,
                )
                for key, document in unique_documents.items()
            ]
            self._collection.bulk_write(operations, ordered=False)
        except self._error as exc:
            raise StateStoreError("cannot upsert MongoDB storage records") from exc
        return len(set(unique_documents) - existing)

    def clear_namespace(self, namespace: str) -> None:
        self._check_open()
        try:
            self._collection.delete_many({"namespace": namespace})
        except self._error as exc:
            raise StateStoreError("cannot clear MongoDB storage namespace") from exc

    def close(self) -> None:
        if not self._closed:
            self._client.close()
            self._closed = True
