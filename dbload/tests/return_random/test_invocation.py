import pytest

from dbload import query, return_random
from dbload.query_result import QueryResult
from dbload.exceptions import NotQueryResultTypeError


def test_return_random_not_query_result_error(cursor):
    @return_random
    @query
    def not_query_result_query(cursor):
        return True

    with pytest.raises(NotQueryResultTypeError):
        _ = not_query_result_query(cursor)


# def test_return_random_one(cursor):
#     @return_random
#     @query
#     def get_one(cursor):
#         return QueryResult.from_cursor(cursor)

#     result = get_one(cursor)
#     assert len(result.rows) == 1
#     assert result.rowcount == -1
#     assert len(result.columns) == 2


# def test_return_random_many(cursor):
#     @return_random
#     @query
#     def get_many(cursor):
#         return QueryResult.from_cursor(cursor)

#     result = get_many(cursor, num=2)
#     assert len(result.rows) == 2


# def test_return_random_no_rows(cursor):
#     @return_random
#     @query
#     def get_one_no_rows(cursor):
#         return QueryResult.from_cursor(cursor)

#     cursor._resultSet = []
#     result = get_one_no_rows(cursor)
#     assert len(result.rows) == 0
