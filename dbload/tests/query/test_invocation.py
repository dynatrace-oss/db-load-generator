import pytest

from dbload import query, get_context
from dbload.exceptions import QueryExecutionError, SqlFileEmptyError


def test_sql_error(cursor):
    @query
    def sql_error_query(cursor):
        raise Exception("bad")

    with pytest.raises(QueryExecutionError):
        sql_error_query(cursor)


def test_sql_error_ignore(cursor):
    @query
    def sql_error_ignored_query(cursor):
        raise Exception("not bad")

    assert sql_error_ignored_query(cursor, ignore=True) is None


# def test_read_files(tmp_path):
#     contents = "SELECT 1 FROM DUAL;"
#     test_file = tmp_path / "test_flie.sql"
#     test_file.write_text(contents)

#     # Items in list are pathlib.Path objects
#     texts = Context._read_files([test_file])
#     assert len(texts) == 1
#     assert texts[0] == contents

#     # Items in list are strings
#     texts = Context._read_files([str(test_file)])
#     assert len(texts) == 1
#     assert texts[0] == contents


# def test_read_files_empty_error(tmp_path):
#     test_file = tmp_path / "empty_file.sql"
#     test_file.write_text("")

#     with pytest.raises(SqlFileEmptyError):
#         Context._read_files([test_file])
