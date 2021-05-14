# Copyright 2020-2021 Dynatrace LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import random
from typing import Optional, Union, Any
from types import FunctionType

from loguru import logger
from jpype.dbapi2 import Cursor, Connection

from .query_result import QueryResult
from .context_singleton import get_context
from .connection import get_connection
from .exceptions import (
    NotQueryResultTypeError,
    QueryExecutionError,
    CursorClosedError,
    CursorTypeError,
    NotFunctionTypeError,
    NotDecoratedByQueryError,
)


def query(
    _func: Optional[FunctionType] = None,
    *,
    name: Optional[str] = None,
    match: Optional[str] = None,
    auto: bool = False,
) -> FunctionType:
    """Register function as a query in the context.

    Args:
        name (str): Name to register the query with (decorator's argument).
        match (str): Name of the matching annotated SQL query (decorator's
            argument).
        auto (bool): Whether this query is an "auto" query function. Auto
            queries ignore any logic inside the decorated function and
            instead simply execute the matching SQL query and return
            the results (decorator's argument).
        ignore (bool): Ignore any errors during query execution (invocation
            argument).

    Examples:
        Method that has a matching query called "create_table" in the SQL
        queries file::

            >>> @query
            ... def create_table(cursor):
            ...     with cursor as c:
            ...         c.execute(create_table.sql)
            ...     print("Executed:")
            ...     print(create_table.sql)

        and its matching query from the SQL queries file, annotated by the
        ``-- name: create_table`` comment line::

            -- name: create_table
            CREATE TABLE DEPARTMENTS (
                ID INTEGER GENERATED ALWAYS AS IDENTITY,
                NAME VARCHAR(50) NOT NULL,
                PRIMARY KEY (ID)
            );

        When invoked, the ``create_table`` function must be manually
        supplied with a valid cursor::

            >>> create_table(cursor)
            Executed:
            CREATE TABLE DEPARTMENTS (
                ID INTEGER GENERATED ALWAYS AS IDENTITY,
                NAME VARCHAR(50) NOT NULL,
                PRIMARY KEY (ID)
            );

        Ignore any errors during execution like this::

            >>> create_table(cursor, ignore=True)

    Raises:
        NotFunctionTypeError: when decorated object is not a function.
        CursorArgumentMissingError: when cursor argument is not supplied
            during function's invocation.
        CursorTypeError: when first argument is not a cursor.
        CursorClosedError: when closed cursor is passed to the query
            function during invocation.
        QueryExecutionError: when exception occurs during execution of the
            query.
    """

    def decorator_query(func: FunctionType):

        if not isinstance(func, FunctionType):
            raise NotFunctionTypeError(func)

        __name: str = name or func.__name__
        func.__name__ = __name

        # query_name: str = match or __name
        # self._infuse_obj_with_matching_sql_query(
        #     obj, query_name, raise_on_missing=auto
        # )

        @functools.wraps(func)
        def wrapper_query(
            *args,
            ignore: bool = False,
            **kwargs,
        ):
            # nonlocal, because otherwise interpreter does not know that
            # the `obj` variable exists in `decorator_query` and throws
            # "local variable 'obj' referenced before assignment" error.
            # See: https://docs.python.org/3/faq/programming.html#why-am-i-getting-an-unboundlocalerror-when-the-variable-has-a-value
            nonlocal func
            logger.debug(f"Executing '{func.__name__}' query.")

            # Cursor is expected be supplied as the first argument to the
            # invoked function.
            cursor: Optional[Cursor] = None
            if not args:
                logger.debug(
                    (
                        "No cursor argument has been passed to the "
                        f"'{__name}' query. Initiating a fresh connection."
                    )
                )

                # Prepare context
                ctx = get_context()
                ctx.infuse()

                # Initiate a new connection ang get a curosr from it.
                connection = get_connection()
                cursor = connection.cursor()

            else:
                cursor = args[0]
                args = args[1:]

            if not isinstance(cursor, Cursor):
                raise CursorTypeError(cursor)

            if cursor._closed:
                raise CursorClosedError(f"in query {__name}")

            result: Union[QueryResult, Any] = None
            try:
                # Auto queries ignore whatever logic was present in
                # the decorated object.
                if auto:
                    # At this point the object should already have an
                    # "sql" attribute assigned.
                    parameters = list(args) + list(kwargs.values())

                    ctx = get_context()
                    sql = ctx.queries[__name].sql

                    cursor.execute(sql, parameters)
                    result = QueryResult.from_cursor(cursor)

                    connection = cursor._connection
                    connection.commit()

                else:
                    result = func(cursor, *args, **kwargs)

            except Exception as e:
                if ignore:
                    logger.warning(
                        f"Error occured in query but was handled: {e}"
                    )
                else:
                    raise QueryExecutionError(e) from None

            return result

        setattr(wrapper_query, "_is_decorated_by_query", True)

        ctx = get_context()
        ctx.register_query(
            wrapper_query, name=__name, match=match or __name, auto=auto
        )

        return wrapper_query

    if _func is None:
        return decorator_query
    else:
        return decorator_query(_func)


def return_random(
    _func: Optional[FunctionType] = None,
    *,
    name: Optional[str] = None,
    match: Optional[str] = None,
    auto: bool = False,
) -> FunctionType:
    """Create a variety of the given function that returns a random row.

    Modifies the :class:`~.QueryResult` returned by the decorated function
    by leaving only 1 or ``num`` random rows in it.

    Decorated query is registered in the context under a different name::

        <original_name>_return_random

    Args:
        num (int): How many random rows to return (invocation argument).

    Examples:
        Modify query so that it returns a random row::

            >>> @return_random
            ... @query
            ... def select_employees(cursor):
            ...     with cursor as c:
            ...         c.execute(select_employees.sql)
            ...         return QueryResult.from_cursor(c)
            ...
            >>> results = select_employees(cursor)
            >>> assert len(results.rows) == 1

    Raises:
        NotDecoratedByQueryError: when trying to decorate a function that
            is not already decorated by :meth:`~.query` decorator.
        NotQueryResultTypeError: when decorated query returns a result that
            is not an instance of :class:`~.QueryResult` class.
    """

    def decorator_return_random(func: FunctionType):

        if not isinstance(func, FunctionType):
            raise NotFunctionTypeError(func)

        if not hasattr(func, "_is_decorated_by_query"):
            raise NotDecoratedByQueryError(func)

        @functools.wraps(func)
        def wrapper_return_random(*args, num: int = 1, **kwargs):

            nonlocal func
            result = func(*args, **kwargs)

            if not isinstance(result, QueryResult):
                raise NotQueryResultTypeError(result)

            if len(result.rows) > 1:
                logger.debug(
                    f"Returning random rows from the results of the '{func.__name__}' query."
                )
                if num == 1:
                    random_rows = [random.choice(result.rows)]
                else:
                    random_rows = random.choices(result.rows, k=num)
                result._rows = random_rows

            return result

        setattr(wrapper_return_random, "_is_decorated_by_return_random", True)

        ctx = get_context()
        __name = name or f"{func.__name__}_return_random"
        __match = match or ctx.queries[func.__name__].match
        ctx.register_query(
            wrapper_return_random, name=__name, match=__match, auto=auto
        )

        return wrapper_return_random

    if _func is None:
        return decorator_return_random
    else:
        return decorator_return_random(_func)
