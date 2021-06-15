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


from pathlib import Path
from typing import Any


class SqlFileEmptyError(RuntimeError):
    """File with annotated SQL queries is empty.

    Raised when a text file with annotated SQL queries is empty.
    """

    def __init__(self, path: Path) -> None:
        super().__init__(f"File with SQL queries is mepty: {path}")


class QueryExecutionError(RuntimeError):
    """Exception while executing a query.

    Raised when an error happens during executing of the function decorated by
    :meth:`~.query.query` decorator.
    """

    pass


class ScenarioExecutionError(RuntimeError):
    """Exception while executing a scenario.

    Raised when an error happens during executing of the function decorated by
    :meth:`~.scenario.scenario` decorator.
    """

    pass


class ConnectionOpeningError(RuntimeError):
    """Exception while connecting to database."""

    pass


class ConnectionClosingError(RuntimeError):
    """Exception while closing the connection to database."""

    pass


class CommitError(RuntimeError):
    """Exception during transaction commit to database."""

    pass


class RollbackError(RuntimeError):
    """Exception during transaction rollback in database."""

    pass


class CursorClosedError(RuntimeError):
    """Closed cursor is passed."""

    def __init__(self, msg: str = "") -> None:
        super().__init__(f"Closed cursor passed {msg if msg else ''}.")


class CursorTypeError(TypeError):
    """Cursor object is of wrong type."""

    def __init__(self, obj: Any) -> None:
        super().__init__(
            f"Wrong type of object received. Expected 'Cursor', instead got: {type(obj)}."
        )


class ConnectionClosedError(RuntimeError):
    """Closed connection passed to scenario."""

    def __init__(self, scenario_name: str) -> None:
        super().__init__(
            f"Closed connection passed to scenario '{scenario_name}'."
        )


class ConnectionTypeError(TypeError):
    """Connection object is of wrong type."""

    def __init__(self, connection: Any) -> None:
        super().__init__(
            f"Wrong type of connection object: {type(connection)}."
        )


class MatchingSqlQueryNotFoundError(RuntimeError):
    """Matching SQL query does not exist."""

    def __init__(self, name: str, match: str) -> None:
        super().__init__(
            f"Matching SQL query '{match}' not found for '{name}'."
        )


class NotDecoratedByQueryError(TypeError):
    """Object must be decorated by query decorator first."""

    def __init__(self, func: Any) -> None:
        super().__init__(
            f"Object '{func.__name__}' must be decorated by query decorator first."
        )


class NotFunctionTypeError(TypeError):
    """Decorated object is not a function."""

    def __init__(self, obj: Any) -> None:
        super().__init__(
            f"Decorated object must be a function. Instead got: '{type(obj)}'."
        )


class NotQueryResultTypeError(TypeError):
    """Returned result is not a QueryResult."""

    def __init__(self, obj: Any) -> None:
        super().__init__(
            f"Expected QueryResult to be returned, instead got: {type(obj)}."
        )


class DsnNotFoundError(AttributeError):
    """DSN connection string is missing from config."""

    def __init__(self) -> None:
        super().__init__(f"Config must contain a 'dsn` connection string.")


class QueryAlreadyExistsError(RuntimeError):
    """Attempting to register query that already exists."""

    def __init__(self, registration_name: str) -> None:
        super().__init__(
            f"Attempting to register query that already exists in the context: '{registration_name}'."
        )


class ScenarioAlreadyExistsError(RuntimeError):
    """Attempting to register scenario that already exists."""

    def __init__(self, registration_name: str) -> None:
        super().__init__(
            f"Attempting to register scenario that already exists in the context: '{registration_name}'."
        )


class UnsupportedPredefinedSimulationError(RuntimeError):
    """Attempting to load predefined simulation that does not exit."""

    def __init__(self, simulation_name) -> None:
        super().__init__(f"Attempting to load predefined simulation '{simulation_name}' that does not exist.")


class ImportlibResourcesNotFoundError(RuntimeError):
    """Required module importlib.resources or importlib_resources not found."""

    def __init__(self) -> None:
        super().__init__("Neither importlib.resources not importlib_resources module is found.")


class PredefinedSimulationImportError(RuntimeError):
    """Could not import predefined simulation."""

    def __init__(self) -> None:
        super().__init__("Could not import predefined simulation")


class EmptyPathToModuleError(RuntimeError):
    """Empty path to module with scenarios is provided."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"Empty path to module is provided: {path}.")
