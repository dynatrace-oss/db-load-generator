from importlib import resources

import pytest
from jpype import dbapi2
from mapz import Mapz


@pytest.fixture
def cursor():
    class Cursor(dbapi2.Cursor):
        def __init__(self):
            self._closed = False
            self._rowcount = -1
            self._resultSet = [(1, "John"), (2, "Ben")]
            self._description = [("id",), ("name",)]
            self._num_execute_called = 0
            self._num_fetchall_called = 0

        def execute(self, operation, parameters, *, types=None, keys=False):
            self._num_execute_called += 1

        def fetchall(self, *, types=None, converters=None):
            self._num_fetchall_called += 1

        def __exit__(self, exception_type, exception_value, traceback):
            pass

    return Cursor()


@pytest.fixture
def connection(cursor):
    class Connection(dbapi2.Connection):
        def __init__(self):
            self._cur = cursor
            pass

        def cursor(self):
            return self._cur

    return Connection()


@pytest.fixture(scope="session", autouse=True)
def sources():
    # 20 queries
    # 4 of them = return_random
    source = ""
    with resources.open_text("dbload.resources", "sql-server.sql") as f:
        source = f.read()
    return [source]
