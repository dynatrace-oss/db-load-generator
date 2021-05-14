import pytest

from dbload.exceptions import MatchingSqlQueryNotFoundError
from dbload import query, get_context


def test_name_taken_from_function():
    @query
    def name_from_function_query():
        pass

    ctx = get_context()
    assert "name_from_function_query" in ctx.queries
    assert "name_from_function_query" == name_from_function_query.__name__


def test_name_explicitly_specified():
    @query(name="other_name")
    def explicit_name_query():
        pass

    ctx = get_context()
    assert "other_name" in ctx.queries
    assert "other_name" == explicit_name_query.__name__


def test_manual_query(cursor):
    @query
    def manual_query(cur):
        return True

    assert manual_query(cursor) is True


# def test_auto_query(cursor):
#     @query(auto=True)
#     def create_departments_table(cur):
#         pass

#     result = create_departments_table(cursor)
#     assert result.rows == [(1, "John"), (2, "Ben")]
