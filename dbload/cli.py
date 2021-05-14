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

import sys
import importlib
from pathlib import Path
from typing import Sequence

import click
from prettytable import PrettyTable
from mapz import Mapz

from .context_singleton import get_context
from .config_singleton import get_config
from .connection import get_connection
from .query_result import QueryResult


@click.group()
@click.option(
    "-C",
    "--config",
    help="Path to the config file.",
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "-m",
    "--module",
    help="Path from which to import the module with scenarios.",
    type=str,
)
@click.option(
    "-d",
    "--dsn",
    help="The database connection string for JDBC.",
    type=str,
)
@click.option(
    "-a",
    "--driver-arg",
    help="Arguments to the driver. This may either a list of key=value pairs or list of values.",
    multiple=True,
    type=str,
)
@click.option(
    "-s",
    "--sql",
    help="Paths to files with SQL queries.",
    multiple=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
)
@click.option(
    "-i",
    "--ignore",
    help="Ignore errors during query executions.",
    is_flag=True,
)
@click.option(
    "-c",
    "--classpath",
    help="Paths to libraries, including JDBC 4.0 database driver. Can include wildcard.",
    type=click.Path(exists=True),
)
@click.option(
    "-D",
    "--driver",
    help="Driver class name to instantiate (example: com.ibm.db2.jcc.DB2Jcc).",
    type=str,
)
@click.option(
    "-v",
    "--verbose",
    help="Log verbosity: 3 levels from error (default) to debug. Stack them up: -vvv to get debug.",
    count=True,
)
@click.option(
    "-q",
    "--quiet",
    help="Do not print any results. Errors are still printed.",
    is_flag=True,
)
def main(*args, **kwargs):

    # Initialize config
    cli_args = {}
    for k in kwargs:
        # Only take non empty CLI arguments
        if kwargs[k]:
            cli_args[k] = kwargs[k]
    config = get_config(cli_args)

    # Parse driver args, if present
    if config.driver_arg and isinstance(config.driver_arg, Sequence):
        driver_args_list = []
        driver_args_dict = {}

        for arg in config.driver_arg:
            if "=" in arg:
                key, value = arg.split("=")
                driver_args_dict[key] = value
            else:
                driver_args_list.append(arg)

        if driver_args_dict:
            config.driver_arg = driver_args_dict
        else:
            config.driver_arg = driver_args_list
        print(config.driver_arg.to_table())

    # Import the scenario
    if config.module is not None:
        if len(Path(config.module).parts) == 0:
            click.echo(
                f"Module with scenarios not specified. Got: '{config.module}'.",
                err=True,
            )
            return

        path = Path(config.module)
        modname = None
        if len(path.parts) > 1:
            parent_path = str(path.parent)
            sys.path.insert(0, parent_path)
            modname = path.stem
        else:
            modname = path.stem
        try:
            importlib.import_module(modname)
        except ModuleNotFoundError as e:
            if modname in f"{e}":
                click.echo(
                    f"Module {modname} not found in given module path: '{config.module}'.",
                    err=True,
                )
                return
            else:
                raise

    # Read SQL files and infuse context based on them
    ctx = get_context()
    ctx.infuse()


@main.command(help="Run a scenario.")
@click.argument("scenario_name", metavar="SCENARIO")
def scenario(scenario_name):

    ctx = get_context()
    if scenario_name not in ctx.scenarios:
        click.echo(f"Scenario '{scenario_name}' does not exist.", err=True)
        return

    cfg = get_config()
    if not cfg.quiet:
        click.echo(f"Executing: {scenario_name}")

    ctx.scenarios[scenario_name].function(ignore=cfg.ignore)


@main.command(help="Execute a query.")
@click.argument("query_name", metavar="QUERY")
@click.option(
    "-l",
    "--limit",
    help="Limit the number of rows displayed in the resulting tables.",
    type=int,
)
@click.option(
    "-p",
    "--property",
    help="Property for the prepared statement.",
    multiple=True,
)
def query(query_name, limit, property):

    ctx = get_context()
    if query_name not in ctx.queries:
        click.echo(f"Query '{query_name}' does not exist.", err=True)
        return

    cfg = get_config()
    limit = limit or cfg.limit

    if not cfg.quiet:
        click.echo(f"Executing: {query_name}")
        if property:
            click.echo(f"Properties: {list(property)}")

    connection = get_connection()
    with connection.cursor() as cur:
        result = ctx.queries[query_name].function(
            cur, *property, ignore=cfg.ignore
        )

        if not cfg.quiet:
            if isinstance(result, QueryResult):
                print(result.table(limit=limit))
            elif result is not None:
                print(result)


@main.command(help="Execute arbitrary SQL statement.")
@click.argument("statement")
@click.option(
    "-l",
    "--limit",
    help="Limit the number of rows displayed in the resulting tables.",
    type=int,
)
@click.option(
    "-p",
    "--property",
    help="Property for the prepared statement.",
    multiple=True,
)
def execute(statement, limit, property):

    cfg = get_config()
    limit = limit or cfg.limit

    if not cfg.quite:
        click.echo(f"Executing: {statement}")
        if property:
            click.echo(f"Properties: {list(property)}")

    connection = get_connection()
    with connection.cursor() as cur:
        cur.execute(statement, property)
        result = QueryResult.from_cursor(cur)

        if not cfg.quiet:
            print(result.table(limit))

    connection.commit()


@main.command(help="Test connection to the given database.")
def test():

    connection = get_connection()
    with connection.cursor():
        click.echo("Successfully connected to the database.")


@main.group(help="Show settings, queries, or scenarios.")
def show():
    pass


@show.command()
def settings():
    config = get_config()
    headers, rows = config.to_table()
    pt = PrettyTable(headers)
    pt.add_rows(rows)
    pt.align = "l"
    print(pt)


@show.command()
def queries():
    ctx = get_context()
    condensed_queries = Mapz()
    for q in ctx.queries:
        condensed_queries[f"{q}.sql"] = ctx.queries[q].sql

    headers, rows = condensed_queries.to_table()
    pt = PrettyTable(headers)
    pt.add_rows(rows)
    pt.align = "l"
    print(pt)


@show.command()
def scenarios():
    ctx = get_context()
    condensed_scenarios = Mapz()
    for s in ctx.scenarios:
        condensed_scenarios[f"{s}.auto_run_queries"] = ctx.scenarios[
            s
        ].auto_run_queries

    headers, rows = condensed_scenarios.to_table()
    pt = PrettyTable(headers)
    pt.add_rows(rows)
    pt.align = "l"
    print(pt)


if __name__ == "__main__":
    main()
