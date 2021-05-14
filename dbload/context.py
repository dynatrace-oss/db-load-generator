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

from collections import defaultdict
from types import FunctionType
from typing import List, Optional

from loguru import logger
from mapz import Mapz

from .config_singleton import get_config
from .query_parser import QueryParser
from .exceptions import (
    QueryAlreadyExistsError,
    ScenarioAlreadyExistsError,
    MatchingSqlQueryNotFoundError,
)


class Context:
    """Execution context.

    Context holds within itself all registered scenarios, queries, and plays.
    It assembles these objects both from annotated text files with SQL
    queries and from Python files with decorated objects and functions.

    Attributes:
        scenarios (:obj:`Mapz`): Dictionary of parsed and generated
            scenarios.
        queries (:obj:`Mapz`): Dictionary of parsed queries.

    Examples:
        Create a new context::

            from dbload import Context
            context = Context()
    """

    def __init__(self) -> None:
        self.scenarios = Mapz()
        self.queries = Mapz()
        self._is_infused = False

    def register_query(
        self,
        query: FunctionType,
        name: Optional[str] = None,
        match: Optional[str] = None,
        auto: bool = False,
    ) -> None:
        """Register a query in the context."""

        registration_name = name or query.__name__
        logger.debug(
            f"Registering '{registration_name}' query in the context."
        )

        if registration_name in self.queries:
            raise QueryAlreadyExistsError(registration_name)

        self.queries[registration_name] = Mapz(
            function=query, name=name, match=match, auto=auto
        )

    def register_scenario(
        self,
        scenario: FunctionType,
        name: Optional[str] = None,
        infuse: bool = False,
        auto: bool = False,
        auto_run_queries: List[str] = [],
    ) -> None:
        """Register a scneario in the context."""

        registration_name = name or scenario.__name__
        logger.debug(
            f"Registering '{registration_name}' scenario in the context."
        )

        if registration_name in self.scenarios:
            raise ScenarioAlreadyExistsError(registration_name)

        self.scenarios[registration_name] = Mapz(
            function=scenario,
            name=name,
            infuse=infuse,
            auto_run_queries=auto_run_queries,
        )

    def infuse(self) -> None:

        if self._is_infused:
            logger.debug(
                "Context was already infused. Skipping infuse stage."
            )
            return
        else:
            logger.debug("Infusing context.")

        cfg = get_config()
        parsed = QueryParser.parse(cfg.sources)

        self._implicit_query(parsed)
        self._implicit_scenario(parsed)

        for q in self.queries:
            self._infuse_query_with_matching_sql(parsed, q)

        for s in self.scenarios:
            self._infuse_scenario_with_queries(s)

        self._is_infused = True

    def _implicit_query(self, parsed: Mapz):
        """Create pre-requested queries.

        Generate queries based on the annotated sql statements from the
        parsed SQL files.
        """

        from .query import query, return_random

        def _gen(query_name: str):
            def _empty_query(*args, **kwargs):
                pass  # pragma: no cover

            _empty_query.__name__ = query_name
            return _empty_query

        for query_name in parsed:

            # Annotated statements can create implicit queries that were not
            # declared explicitly in an accompanying python module.
            # We have to register such queries.
            if query_name not in self.queries:
                # Create an empty function that does nothing
                empty_query = _gen(query_name)
                # Wrap resulting function as query method
                empty_query = query(name=query_name, auto=True)(empty_query)

            # Infuse additional optional query modifications
            for option in parsed[query_name].options:

                if f"{query_name}_{option}" not in self.queries:
                    if option == "return_random":
                        return_random(auto=True)(empty_query)
                    else:
                        logger.warning(
                            f"Unrecognized option in SQL query: {option}"
                        )

    def _implicit_scenario(self, parsed: Mapz):
        """Create pre-requested scenarios.

        Generate scenarios based on the "scenario" keyword in query
        metadata from SQL file.
        """

        from .scenario import scenario

        def _gen(scenario_name: str):
            def _empty_scenario(*args, **kwargs):
                pass  # pragma: no cover

            _empty_scenario.__name__ = scenario_name
            return _empty_scenario

        auto_run_queries_per_scenario = defaultdict(list)

        # Each parsed query
        for query_name, params in parsed.items():
            # Might have several scenarios assigned
            for name, order in params.scenarios:
                auto_run_queries_per_scenario[name].append(
                    (query_name, order)
                )

        for name in auto_run_queries_per_scenario:
            ordered_tuples = sorted(
                auto_run_queries_per_scenario[name], key=lambda i: i[1]
            )
            ordered_query_names = [t[0] for t in ordered_tuples]

            # Annotated queries can create implicit scenarios that were not
            # declared explicitly in an accompanying python module.
            # We have to register such scenarios.
            if name not in self.scenarios:
                empty_scenario = _gen(name)
                scenario(
                    name=name,
                    infuse=False,
                    auto=True,
                    auto_run_queries=ordered_query_names,
                )(empty_scenario)

            # Otherwise, just change the auto_run_queries list for the
            # already registered scenario.
            else:
                self.scenarios[name].auto_run_queries = ordered_query_names

    def _infuse_query_with_matching_sql(self, parsed: Mapz, query_name: str):
        """Infuse query object with SQL text attribute.

        This is a helper method for the ``query`` decorator.
        """

        # Fetch matching SQL query text from parsed queries
        match = self.queries[query_name].match
        query_text: Optional[str] = parsed[match].get("text", None)
        if not query_text:
            if self.queries[query_name].auto:
                raise MatchingSqlQueryNotFoundError(
                    self.queries[query_name].function.__name__, query_name
                )
            else:
                logger.warning(
                    f"'{self.queries[query_name].function.__name__}' has no matching SQL query."
                )

        self.queries[query_name].sql = query_text or None
        setattr(self.queries[query_name].function, "sql", query_text or None)

    def _infuse_scenario_with_queries(self, scenario_name: str):
        if self.scenarios[scenario_name].infuse:
            for query_name, q in self.queries.items():
                setattr(
                    self.scenarios[scenario_name].function,
                    query_name,
                    q.function,
                )
