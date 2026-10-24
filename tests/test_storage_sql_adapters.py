from __future__ import annotations

import sys
import types
from typing import Any, cast

import pytest

from essl_f22.errors import StateStoreError, StorageConfigurationError
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

    with pytest.raises(StorageConfigurationError, match="psycopg") as exc_info:
        create_storage("postgres", options={"dsn": "postgresql://user:pass@db/app"})

    assert "install Essl_F22_SDK[postgres]" in str(exc_info.value)


def test_mysql_reports_missing_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "pymysql", cast(Any, None))

    with pytest.raises(StorageConfigurationError, match="pymysql") as exc_info:
        create_storage("mysql", options={"dsn": "mysql://user:pass@db/app"})

    assert "install Essl_F22_SDK[mysql]" in str(exc_info.value)


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


class _FakeMySQLError(Exception):
    pass


class _FakeCursor:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def execute(self, sql: str, params: object = None) -> None:
        if self._connection.fail_execute:
            raise _FakeMySQLError("execute failed")
        self._connection.executed.append((sql, params))

    def executemany(self, sql: str, params: object) -> None:
        self._connection.executed.append((sql, params))

    def fetchone(self) -> None:
        return None

    def fetchall(self) -> list[tuple[str, str]]:
        return []


class _FakeConnection:
    def __init__(self) -> None:
        self.open = True
        self.commits = 0
        self.rollbacks = 0
        self.closes = 0
        self.fail_execute = False
        self.executed: list[tuple[str, object]] = []

    def __enter__(self) -> _FakeConnection:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        if not self.open:
            raise _FakeMySQLError("already closed")
        self.open = False
        self.closes += 1


def _install_fake_pymysql(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[list[_FakeConnection], Any]:
    connections: list[_FakeConnection] = []
    module = types.ModuleType("pymysql")
    fake = cast(Any, module)
    fake.err = types.SimpleNamespace(MySQLError=_FakeMySQLError)
    fake.fail_execute = False

    def connect(**kwargs: object) -> _FakeConnection:
        connection = _FakeConnection()
        connection.fail_execute = bool(fake.fail_execute)
        connections.append(connection)
        return connection

    fake.connect = connect
    monkeypatch.setitem(sys.modules, "pymysql", module)
    return connections, fake


def test_mysql_commits_and_closes_each_operation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connections, _module = _install_fake_pymysql(monkeypatch)

    storage = MysqlStorage("mysql://user:pass@db/app")
    storage.write_document("users", "1", {"uid": 1})

    assert len(connections) == 2
    for connection in connections:
        assert connection.commits == 1
        assert connection.rollbacks == 0
        assert connection.closes == 1
    assert "INSERT INTO documents" in connections[1].executed[0][0]


def test_mysql_rolls_back_and_closes_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    connections, module = _install_fake_pymysql(monkeypatch)
    storage = MysqlStorage("mysql://user:pass@db/app")
    module.fail_execute = True

    with pytest.raises(StateStoreError, match="cannot write"):
        storage.write_document("users", "1", {"uid": 1})

    assert connections[-1].commits == 0
    assert connections[-1].rollbacks == 1
    assert connections[-1].closes == 1
