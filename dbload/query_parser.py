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

import re
from typing import List

from loguru import logger
from mapz import Mapz


class QueryParser:
    """SQL file parser.

    Parses annotated SQL files from provided paths. This class should not
    generally be used by itself. :class:`~dbload.context.Context` already
    invokes this parser during its initialization phase.

    QueryParser provides a single static method :meth:`~.QueryParser.parse`
    that performs the parsing. There is no need to create the QueryParser
    object itself.

    Examples:
        Use parser::

            from dbload import QueryParser
            parsed = QueryParser.parse(["./queries.sql"])
    """

    @staticmethod
    def parse(sources: List[str] = []) -> Mapz:
        """Parse text sources with annotated SQL queries.

        Args:
            sources (List[str]): List of text strings with
                annotated SQL queries to parse.

        Parser reads each string line by line (split by ``\\n`` symbol)
        and looks for annotated SQL queries in it. It does not verify
        the validity of SQL syntax.
        Parser understands annotation comments in SQL file that start
        with ``"--"`` comment identifier and contain ``name:`` tag in them.

        Returns:
            Mapz: Dictionary of parsed queries.

        Raises:
            SqlQueriesFileEmptyError: when provided text file with annotated
                SQL queries is empty.
        """

        parsed = Mapz()
        for source in sources:
            QueryParser._parse_queries(source, parsed)
        return parsed

    @staticmethod
    def _parse_queries(source: str, parsed: Mapz) -> None:
        name_regex = re.compile(r".*name:\s*([\w]+)")
        option_regex = re.compile(r"option:\s*([\w]+)")
        # re.findall(
        #     r"scenario:\s*([\w-]+)(?:\[([-\d]+)\])?",
        #     "--name:disi, scenario: sample[1], scenario: teardown[-90], scenario: name",
        # )
        # >>> [('sample', '1'), ('teardown', '-90'), ('name', '')]
        scenario_regex = re.compile(r"scenario:\s*([\w-]+)(?:\[([-\d]+)\])?")

        # After reading whole file, process the lines
        # one by one, assembling queries one by one
        current_query_name = None
        # current_query_kind = None
        current_query_content = ""

        lines = source.split("\n")
        for line in lines:
            line = line.strip("\n").replace("\t", " ").replace("\r", "")

            if "--" in line:
                # Detect start of the new query
                nm = name_regex.match(line)
                if nm:

                    # If we have a current query name, then append new content to it
                    if current_query_name:
                        parsed[
                            current_query_name
                        ].text = current_query_content
                        current_query_content = ""

                    # Detect if there are any options specified in the query
                    options = option_regex.findall(line)

                    # Detect if the querly explicitly wants to be called
                    # within a certain scenario
                    scenarios = scenario_regex.findall(line)
                    scenarios = [
                        (n, int(order) if order else 0)
                        for n, order in scenarios
                    ]

                    # Start new context for tracking the new query
                    current_query_name = nm.group(1)
                    current_query_content = ""

                    parsed[current_query_name] = Mapz(
                        # kind=current_query_kind,
                        options=options,
                        scenarios=scenarios,
                        text="",
                    )

            else:
                current_query_content += line

        # Add last "unseparrated" query to list
        parsed[current_query_name].text = current_query_content
