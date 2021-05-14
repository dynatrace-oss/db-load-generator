import pytest

from dbload import query, return_random
from dbload.exceptions import NotDecoratedByQueryError


def test_return_random_not_decorated_by_query_error():
    with pytest.raises(NotDecoratedByQueryError):

        @query
        @return_random
        def not_decorated_query(cursor):
            pass
