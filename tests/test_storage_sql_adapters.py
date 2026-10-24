import sys
from typing import Any, cast

import pytest

from essl_f22.errors import StorageConfigurationError
from essl_f22.storage import MysqlStorage, PostgresStorage, create_storage
from essl_f22.storage.mysql import _parse_dsn


def test_postgres_requires_a_dsn() -> None:
    with pytest.raises(StorageConfigurationError, match="dsn"):
        create_storage("postgres")


def test_mysql_requires_a_dsn() -> None:
    with pytest.raises(StorageConfigurationError, match="dsn"):
        create_storage("mysql")


def test_postgres_reports_missing_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "psycopg", cast(Any, None))

    with pytest.raises(StorageConfigurationError, match="psycopg"):
        create_storage("postgres", options={"dsn": "postgresql://user:pass@db/app"})


def test_mysql_reports_missing_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "pymysql", cast(Any, None))

    with pytest.raises(StorageConfigurationError, match="pymysql"):
        create_storage("mysql", options={"dsn": "mysql://user:pass@db/app"})


def test_factory_selects_postgres(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakePostgresStorage:
        def __init__(self, dsn: str) -> None:
            self.dsn = dsn

    monkeypatch.setattr("essl_f22.storage.factory.PostgresStorage", FakePostgresStorage)

    store = cast(
        Any,
        create_storage("postgres", options={"dsn": "postgresql://db/app"}),
    )

    assert isinstance(store, FakePostgresStorage)
    assert store.dsn == "postgresql://db/app"


def test_factory_selects_mysql(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeMysqlStorage:
        def __init__(self, dsn: str) -> None:
            self.dsn = dsn

    monkeypatch.setattr("essl_f22.storage.factory.MysqlStorage", FakeMysqlStorage)

    store = cast(Any, create_storage("mysql", path="mysql://db/app"))

    assert isinstance(store, FakeMysqlStorage)
    assert store.dsn == "mysql://db/app"


def test_sql_adapter_classes_are_exported() -> None:
    assert PostgresStorage is not None
    assert MysqlStorage is not None


def test_mysql_dsn_is_parsed() -> None:
    config = _parse_dsn("mysql://user:p%40ss@db.example:3307/app%2Ddb")

    assert config == {
        "host": "db.example",
        "port": 3307,
        "user": "user",
        "password": "p@ss",
        "database": "app-db",
        "charset": "utf8mb4",
        "autocommit": False,
    }


def test_mysql_rejects_non_mysql_dsn() -> None:
    with pytest.raises(StorageConfigurationError, match="mysql://"):
        _parse_dsn("postgresql://db/app")


def test_mysql_requires_a_database() -> None:
    with pytest.raises(StorageConfigurationError, match="database"):
        _parse_dsn("mysql://db")
