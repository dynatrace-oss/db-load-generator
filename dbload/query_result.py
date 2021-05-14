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

from dbload.exceptions import CursorClosedError
from typing import Any, List, Tuple

from jpype.dbapi2 import Cursor
from prettytable import PrettyTable


class QueryResult:
    def __init__(
        self,
        rowcount: int = -1,
        rows: List[Tuple] = [],
        columns: List[Tuple] = [],
    ) -> None:
        self._rowcount: int = rowcount
        self._rows: List[Tuple] = rows
        self._columns: List[Tuple] = columns

    @staticmethod
    def from_cursor(cursor: Cursor):
        """Store results of the query execution from cursor.

        (Execute must already be called but nothing should be fetched.)

        This method preserves data from cursor. So that when cursor is
        closed, the data is preserved and can be used during the further
        calculations.

        This method calls ``fetchall()`` method of cursor to fetch all rows.

        Args:
            cursor: Cursor object for which ``execute()`` has already been
                called.
        """

        if cursor._closed:
            raise CursorClosedError("in QueryResult")

        qr = QueryResult()
        qr._rowcount = cursor.rowcount

        # Have to check for resultSet is not None here because
        # SQLite returns rowcount = 0 for update/delete/drop/create, etc
        # types of queries.
        if cursor.rowcount == -1 or cursor._resultSet is not None:
            qr._columns = cursor.description
            qr._rows = cursor.fetchall()

        return qr

    @property
    def rowcount(self) -> int:
        return self._rowcount

    @property
    def rows(self) -> List[Tuple]:
        """Get list of tuples representing rows."""
        return self._rows

    @property
    def columns(self) -> List[Tuple]:
        """Get list of tuples describing columns.

        Each tuple in the list contains:
        - Column name
        - Column type name
        - Display size
        - Internal size
        - Precision
        - Scale
        - Is nullable
        """
        return self._columns

    @property
    def first(self) -> Tuple:
        """Return first row if there are rows. Otherwise return None."""
        if self._rows:
            return self._rows[0]
        return None

    def get(self, row: int, default: Any = None):
        if self._rows and row < len(self._rows):
            return self._rows[row]
        return default

    def table(self, limit: int = 0) -> PrettyTable:
        """Get a printable table.

        Returns:
            PrettyTable: instance of ``PrettyTable`` suitable for
                printing in the terminal.
        """
        tbl = PrettyTable()

        if self._rowcount == -1 or self._columns or self._rows:
            tbl.field_names = ["#"] + [col[0] for col in self._columns]
            rows_to_add = self._rows[:limit] if limit else self._rows
            tbl.add_rows(
                [[i + 1] + list(row) for i, row in enumerate(rows_to_add)]
            )
        else:
            tbl.field_names = ["Rows affected"]
            tbl.add_row([self._rowcount])
        return tbl
