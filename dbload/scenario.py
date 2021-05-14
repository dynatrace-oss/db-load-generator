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
from typing import Any, List, Optional
from types import FunctionType

from loguru import logger
from jpype.dbapi2 import Connection

from .context_singleton import get_context
from .connection import get_connection
from dbload.exceptions import (
    ConnectionClosedError,
    ConnectionTypeError,
    NotFunctionTypeError,
    ScenarioExecutionError,
)


def scenario(
    _func: Optional[FunctionType] = None,
    *,
    name: Optional[str] = None,
    infuse: bool = True,
    auto: bool = False,
    auto_run_queries: List[str] = [],
):
    """Register a function as scenario in the context.

    Args:
        name (str): Name under which the scenario is registered. Defaults
            to the name of the decorated object.
        infuse (bool): Whether to infuse the decorated object with all
            parsed SQL queries in a form of easily callable "auto"
            query functions.
        auto_run_queries (List[str]): Lif of query names to run
            automatically when scenario in invoked. Only existing queries
            are launched. This happends before any other logic in scenario.

    Examples:
        Create a cursor within scenario and use it to manually execute a
        query::

            @context.scenario
            def create_users(connection):
                with connection.cursor() as cur:
                    stmt = "INSERT INTO USERS VALUES ('Alexander')"
                    cur.execute(stmt)
    """

    def decorator_scenario(func: FunctionType):

        if not isinstance(func, FunctionType):
            raise NotFunctionTypeError(func)

        __name: str = name or func.__name__
        func.__name__ = __name

        @functools.wraps(func)
        def wrapper_scenario(*args, ignore: bool = False, **kwargs):
            nonlocal func
            logger.debug(f"Executing '{func.__name__}' scenario.")

            ctx = get_context()

            # Connection is expected to be supplied as the first arrgument
            # to the executed function.
            connection: Optional[Connection] = None
            if not args:
                logger.debug(
                    (
                        "No connection argument has been supplied to the "
                        f"'{func.__name__}' scenario. Initiating a fresh "
                        "connection."
                    )
                )

                # Prepare context
                ctx.infuse()

                # Initiate a new connection
                connection = get_connection()

            else:
                connection = args[0]
                args = args[1:]

            if not isinstance(connection, Connection):
                raise ConnectionTypeError(connection)

            if connection._closed:
                raise ConnectionClosedError(__name)

            result: Any = None
            try:
                # Auto Run Queries.
                # If there is a list of query names that should be ran
                # automatically when this scenario is invoked, then run
                # them.
                query_names = ctx.scenarios[__name].auto_run_queries
                if query_names:
                    logger.debug(
                        f"Execuing auto-run queries for scenario '{__name}': {query_names}"
                    )
                    for q in query_names:
                        with connection.cursor() as cur:
                            ctx.queries[q].function(cur, ignore=ignore)

                if auto:
                    connection.commit()
                else:
                    result = func(connection, *args, **kwargs)

            except Exception as e:
                if ignore:
                    logger.warning(
                        f"Error occured in scenario but was handled: {e}"
                    )
                else:
                    raise ScenarioExecutionError(e) from None

            return result

        setattr(wrapper_scenario, "_is_decorated_by_scenario", True)

        ctx = get_context()
        ctx.register_scenario(
            wrapper_scenario,
            name=__name,
            infuse=infuse,
            auto=auto,
            auto_run_queries=auto_run_queries,
        )

        return wrapper_scenario

    if _func is None:
        return decorator_scenario
    else:
        return decorator_scenario(_func)
