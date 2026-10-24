import sys
from typing import Any, cast

import pytest

from essl_f22.errors import StorageConfigurationError
from essl_f22.storage import MongoStorage, RedisStorage, create_storage


def test_mongo_requires_a_uri() -> None:
    with pytest.raises(StorageConfigurationError, match="uri"):
        create_storage("mongo")


def test_redis_requires_a_url() -> None:
    with pytest.raises(StorageConfigurationError, match="url"):
        create_storage("redis")


def test_mongo_reports_missing_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "pymongo", cast(Any, None))

    with pytest.raises(StorageConfigurationError, match="pymongo") as exc_info:
        create_storage("mongo", options={"uri": "mongodb://localhost/app"})

    assert "install Essl_F22_SDK[mongo]" in str(exc_info.value)


def test_redis_reports_missing_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "redis", cast(Any, None))

    with pytest.raises(StorageConfigurationError, match="redis") as exc_info:
        create_storage("redis", options={"url": "redis://localhost/0"})

    assert "install Essl_F22_SDK[redis]" in str(exc_info.value)


def test_factory_selects_mongo(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeMongoStorage:
        def __init__(self, uri: str) -> None:
            self.uri = uri

    monkeypatch.setattr("essl_f22.storage.factory.MongoStorage", FakeMongoStorage)

    store = cast(Any, create_storage("mongo", options={"uri": "mongodb://db/app"}))

    assert isinstance(store, FakeMongoStorage)
    assert store.uri == "mongodb://db/app"


def test_factory_selects_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeRedisStorage:
        def __init__(self, url: str) -> None:
            self.url = url

    monkeypatch.setattr("essl_f22.storage.factory.RedisStorage", FakeRedisStorage)

    store = cast(Any, create_storage("redis", path="redis://db/0"))

    assert isinstance(store, FakeRedisStorage)
    assert store.url == "redis://db/0"


def test_redis_rejects_an_invalid_url() -> None:
    pytest.importorskip("redis")

    with pytest.raises(StorageConfigurationError, match="Redis URL"):
        create_storage("redis", options={"url": "not-a-url"})


def test_nosql_adapter_classes_are_exported() -> None:
    assert MongoStorage is not None
    assert RedisStorage is not None
