"""Redis storage backend using hashes per namespace."""

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


class RedisStorage(DocumentStorage):
    """A Redis-backed storage backend."""

    def __init__(self, url: str) -> None:
        try:
            import redis
        except ImportError as exc:
            raise StorageConfigurationError(
                "Redis storage requires redis from the 'redis' extra: "
                "install essl_f22[redis]"
            ) from exc
        self._error: Any = redis.RedisError
        self._closed = False
        try:
            self._client: Any = redis.Redis.from_url(url, decode_responses=True)
        except ValueError as exc:
            raise StorageConfigurationError("invalid Redis URL") from exc
        try:
            self._client.ping()
        except self._error as exc:
            self._client.close()
            raise StateStoreError("cannot initialize Redis storage") from exc

    def _hash_key(self, namespace: str) -> str:
        if self._closed:
            raise StateStoreError("Redis storage is closed")
        return f"essl_f22:documents:{namespace}"

    def read_document(self, namespace: str, key: str) -> Document | None:
        hash_key = self._hash_key(namespace)
        try:
            payload = self._client.hget(hash_key, key)
        except self._error as exc:
            raise StateStoreError("cannot read from Redis storage") from exc
        if payload is None:
            return None
        return document_from_json(payload)

    def write_document(
        self, namespace: str, key: str, document: Mapping[str, object]
    ) -> None:
        hash_key = self._hash_key(namespace)
        payload = document_to_json(dict(document))
        try:
            self._client.hset(hash_key, key, payload)
        except self._error as exc:
            raise StateStoreError("cannot write to Redis storage") from exc

    def delete_document(self, namespace: str, key: str) -> None:
        hash_key = self._hash_key(namespace)
        try:
            self._client.hdel(hash_key, key)
        except self._error as exc:
            raise StateStoreError("cannot delete from Redis storage") from exc

    def list_documents(self, namespace: str) -> dict[str, Document]:
        hash_key = self._hash_key(namespace)
        try:
            rows = self._client.hgetall(hash_key)
        except self._error as exc:
            raise StateStoreError("cannot list Redis storage records") from exc
        return {key: document_from_json(payload) for key, payload in rows.items()}

    def replace_documents(
        self, namespace: str, documents: Mapping[str, Mapping[str, object]]
    ) -> None:
        hash_key = self._hash_key(namespace)
        rows = {
            key: document_to_json(dict(document)) for key, document in documents.items()
        }
        try:
            pipeline = self._client.pipeline(transaction=True)
            pipeline.delete(hash_key)
            if rows:
                pipeline.hset(hash_key, mapping=rows)
            pipeline.execute()
        except self._error as exc:
            raise StateStoreError("cannot replace Redis storage records") from exc

    def upsert_documents(
        self, namespace: str, documents: Mapping[str, Mapping[str, object]]
    ) -> int:
        hash_key = self._hash_key(namespace)
        unique_documents = dict(documents)
        if not unique_documents:
            return 0
        rows = {
            key: document_to_json(dict(document))
            for key, document in unique_documents.items()
        }
        try:
            existing = set(self._client.hkeys(hash_key))
            pipeline = self._client.pipeline(transaction=True)
            pipeline.hset(hash_key, mapping=rows)
            pipeline.execute()
        except self._error as exc:
            raise StateStoreError("cannot upsert Redis storage records") from exc
        return len(set(unique_documents) - existing)

    def clear_namespace(self, namespace: str) -> None:
        hash_key = self._hash_key(namespace)
        try:
            self._client.delete(hash_key)
        except self._error as exc:
            raise StateStoreError("cannot clear Redis storage namespace") from exc

    def close(self) -> None:
        if not self._closed:
            self._client.close()
            self._closed = True
