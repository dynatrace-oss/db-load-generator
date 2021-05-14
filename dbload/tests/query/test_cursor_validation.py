import pytest

from dbload import query
from dbload.exceptions import (
    CursorTypeError,
    CursorClosedError,
)


def test_cursor_type_error():
    @query
    def cursor_type_error_query(cursor):
        pass

    with pytest.raises(CursorTypeError):
        cursor_type_error_query("string")


def test_cursor_closed_error(cursor):
    @query
    def cursor_closed_error_query(cursor):
        pass

    cursor._closed = True
    with pytest.raises(CursorClosedError):
        cursor_closed_error_query(cursor)
