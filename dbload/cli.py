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

import click
from dramatiq import broker
from prettytable import PrettyTable
from mapz import Mapz

from .context_singleton import get_context
from .config_singleton import get_config
from .connection import get_connection
from .query_result import QueryResult
from . import __version__


# Global CLI context for nested command line args
cli_args: Mapz = Mapz()


# def load_predefined_simulation(config: Mapz) -> None:
#     if config.predefined not in config.predefined_simulations:
#         click.echo(f"Unsupported predefined simulation. Got: '{config.predefined}'. Should be one of: {config.predefined_simulations}.", err=True)
#         sys.exit(1)

#     # Nullify parameters that can interfere
#     config.module = None
#     config.sql = []

#     # Import helper modules
#     try:
#         import importlib.resources as pkg_resources
#     except ImportError:
#         try:
#             import importlib_resources as pkg_resources
#         except:
#             click.echo("Module importlib.resources or importlib_resources not found.", err=True)
#             sys.exit(1)

#     try:
#         # SQL queries file gets imported from resources
#         from . import resources
#         sql_source = pkg_resources.read_text(resources, f"{config.predefined}.sql")
#         config.sources = [sql_source]  # Override any read sources
#         # and the scenario file is imported from there as well
#         from .resources import scenarios
#     except:
#         click.echo("Could not import predefined modules.", err=True)
#         sys.exit(1)


# def load_requested_scenario(path: str) -> None:
#     if len(Path(path).parts) == 0:
#         click.echo(f"Module containing scenarios improperly specified. Got: '{path}'.", err=True)
#         sys.exit(1)

#     path = Path(path)
#     modname = None
#     if len(path.parts) > 1:
#         parent_path = str(path.parent)
#         sys.path.insert(0, parent_path)
#         modname = path.stem
#     else:
#         modname = path.stem
#     try:
#         importlib.import_module(modname)
#     except ModuleNotFoundError as e:
#         if modname in f"{e}":
#             click.echo(f"Module {modname} not found in given module path: '{path}'.", err=True)
#             sys.exit(1)
#         else:
#             raise e


# def load_simulation(config: Mapz) -> None:
#     if config.predefined is not None:
#         # Import predefined simulation if requested
#         load_predefined_simulation(config)
#     elif config.module is not None:
#         # Import the scenario
#         load_requested_scenario(config.module)


def update_cli_args(kwargs) -> None:
    global cli_args
    non_empty_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    cli_args.merge(non_empty_kwargs)


def decorate_with_common_options(f):
    f = click.version_option(__version__)(f)
    f = click.option("-v", "--verbose", help="Log verbosity: 3 levels from error (default) to debug. Stack them up: -vvv to get debug.", count=True)(f)
    f = click.option("-q", "--quiet", help="Do not print any results. Errors are still printed.", is_flag=True)(f)
    f = click.option("-p", "--predefined", help="Name of the predefined simulation for one of the supported databases.", type=str)(f)
    f = click.option("-D", "--driver", help="Driver class name to instantiate (example: com.ibm.db2.jcc.DB2Jcc).", type=str)(f)
    f = click.option("-c", "--classpath", help="Paths to libraries, including JDBC 4.0 database driver. Can include wildcard.", multiple=True, type=click.Path(exists=True))(f)
    f = click.option("-i", "--ignore", help="Ignore errors during query executions.", is_flag=True)(f)
    f = click.option("-s", "--sql", help="Paths to files with SQL queries.", multiple=True, type=click.Path(exists=True, dir_okay=False, readable=True))(f)
    f = click.option("-a", "--driver-arg", help="Arguments to the driver. Can be key=value pairs or just values.", multiple=True, type=str)(f)
    f = click.option("-d", "--dsn", help="The database connection string for JDBC.", type=str)(f)
    f = click.option("-m", "--module", help="Path python module with scenarios to import.", type=str)(f)
    f = click.option("-C", "--config", help="Path to the config file.", type=click.Path(exists=True, dir_okay=False))(f)
    return f


@click.group()
@click.version_option(__version__)
@decorate_with_common_options
def main(**kwargs):
    update_cli_args(kwargs)


@main.command(help="Run a scenario.")
@click.argument("scenario_name", metavar="SCENARIO")
@decorate_with_common_options
def scenario(scenario_name, **kwargs):
    update_cli_args(kwargs)
    global cli_args
    config = get_config(cli_args)

    # Read SQL files and infuse context based on them
    ctx = get_context()
    ctx.infuse()

    if scenario_name not in ctx.scenarios:
        click.echo(f"Scenario '{scenario_name}' does not exist.", err=True)
        return

    if not config.quiet:
        click.echo(f"Executing: {scenario_name}")

    ctx.scenarios[scenario_name].function(ignore=config.ignore)


@main.command(help="Execute a query.")
@click.argument("query_name", metavar="QUERY")
@click.option("-l", "--limit", help="Limit the number of rows displayed in the resulting tables.", type=int)
@click.option("-p", "--property", help="Property for the prepared statement.", multiple=True)
@decorate_with_common_options
def query(query_name, limit, property, **kwargs):
    update_cli_args(kwargs)
    global cli_args
    config = get_config(cli_args)

    # Read SQL files and infuse context based on them
    ctx = get_context()
    ctx.infuse()

    if query_name not in ctx.queries:
        click.echo(f"Query '{query_name}' does not exist.", err=True)
        sys.exit(1)

    if not config.quiet:
        click.echo(f"Executing: {query_name}")
        if property:
            click.echo(f"Properties: {list(property)}")

    connection = get_connection()
    with connection.cursor() as cur:
        result = ctx.queries[query_name].function(cur, *property, ignore=config.ignore)

        if not config.quiet:
            if isinstance(result, QueryResult):
                limit = limit or config.limit
                print(result.table(limit=limit))
            elif result is not None:
                print(result)


@main.command(help="Execute arbitrary SQL statement.")
@click.argument("statement")
@click.option("-l", "--limit", help="Limit the number of rows displayed in the resulting tables.", type=int)
@click.option("-p", "--property", help="Property for the prepared statement.", multiple=True)
@decorate_with_common_options
def execute(statement, limit, property, **kwargs):
    update_cli_args(kwargs)
    global cli_args
    config = get_config(cli_args)

    if not config.quite:
        click.echo(f"Executing: {statement}")
        if property:
            click.echo(f"Properties: {list(property)}")

    connection = get_connection()
    with connection.cursor() as cur:
        cur.execute(statement, property)
        result = QueryResult.from_cursor(cur)

        if not config.quiet:
            limit = limit or config.limit
            print(result.table(limit))

    connection.commit()


@main.command(help="Test connection to the given database.")
@decorate_with_common_options
def test(**kwargs):
    update_cli_args(kwargs)
    global cli_args
    get_config(cli_args)

    connection = get_connection()
    with connection.cursor():
        click.echo("Successfully connected to the database.")


@main.group(help="Show settings, queries, or scenarios.")
@decorate_with_common_options
def show(**kwargs):
    update_cli_args(kwargs)


@show.command()
@decorate_with_common_options
def settings(**kwargs):
    update_cli_args(kwargs)
    global cli_args
    config = get_config(cli_args)

    # Read SQL files and infuse context based on them
    ctx = get_context()
    ctx.infuse()

    headers, rows = config.to_table()
    pt = PrettyTable(headers)
    pt.add_rows(rows)
    pt.align = "l"
    print(pt)


@show.command()
@decorate_with_common_options
def queries(**kwargs):
    update_cli_args(kwargs)
    global cli_args
    config = get_config(cli_args)

    # Read SQL files and infuse context based on them
    ctx = get_context()
    ctx.infuse()

    condensed_queries = Mapz()
    for q in ctx.queries:
        condensed_queries[f"{q}.sql"] = ctx.queries[q].sql

    headers, rows = condensed_queries.to_table()
    pt = PrettyTable(headers)
    pt.add_rows(rows)
    pt.align = "l"
    print(pt)


@show.command()
@decorate_with_common_options
def scenarios(**kwargs):
    update_cli_args(kwargs)
    global cli_args
    config = get_config(cli_args)

    # Read SQL files and infuse context based on them
    ctx = get_context()
    ctx.infuse()

    condensed_scenarios = Mapz()
    for s in ctx.scenarios:
        condensed_scenarios[f"{s}.auto_run_queries"] = ctx.scenarios[s].auto_run_queries

    headers, rows = condensed_scenarios.to_table()
    pt = PrettyTable(headers)
    pt.add_rows(rows)
    pt.align = "l"
    print(pt)


@main.command(help="Enqueue dramatiq actor for execution.")
@click.argument("actor_name", metavar="ACTOR")
@decorate_with_common_options
def send(actor_name, **kwargs):
    update_cli_args(kwargs)
    global cli_args
    config = get_config(cli_args)

    # Read SQL files and infuse context based on them
    ctx = get_context()
    ctx.infuse()

    try:
        from dramatiq import get_broker, actor as register_actor
        broker = get_broker()

        # Decorate all queries and scenarios as actors
        for query_name in ctx.queries:
            register_actor(ctx.queries[query_name].function)
        for scenario_name in ctx.scenarios:
            register_actor(ctx.scenarios[scenario_name].function)

        actors = broker.get_declared_actors()
        if actor_name in actors:
            actor = broker.get_actor(actor_name)
            actor.send()
            if not config.quiet:
                click.echo(f"Execution of {actor_name} has been added to the broker queue.")
        else:
            click.echo(f"Actor {actor_name} is not registered in dramatiq.", err=True)
            sys.exit(1)

    except ImportError:
        click.echo("Cannot enqueue because dramatiq cannot be imported.", err=True)
        sys.exit(1)


@main.command(help="Launch scheduler (beat) process.")
@click.argument("actor_name", metavar="ACTOR", type=str, required=False)
@click.argument("cron", type=str, required=False)
@decorate_with_common_options
def scheduler(actor_name, cron, **kwargs):
    update_cli_args(kwargs)
    global cli_args
    config = get_config(cli_args)

    # Read SQL files and infuse context based on them
    ctx = get_context()
    ctx.infuse()

    try:
        from dramatiq import get_broker, actor as register_actor
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger

        # Decorate all queries and scenarios as actors
        for query_name in ctx.queries:
            register_actor(ctx.queries[query_name].function)
        for scenario_name in ctx.scenarios:
            register_actor(ctx.scenarios[scenario_name].function)

        # Form a schedule if explicitly requested.
        # Otherwise schedule from config will be used
        broker = get_broker()
        actors = broker.get_declared_actors()
        if actor_name in actors:
            cron = cron or "* * * * *"
            config.schedule = { actor_name: cron }

        if not config.schedule:
            click.echo("There is nothing to schedule. Schedule is empty.", err=True)
            sys.exit(1)

        if not isinstance(config.schedule, Mapz):
            click.echo("Wrong format of schedule configuration. Must be dict with actor_name:cron_schedule items.", err=True)
            sys.exit(1)

        scheduler = BackgroundScheduler()
        for name, crontab in config.schedule.items():
            actor = broker.get_actor(name)

            scheduler.add_job(actor.send, CronTrigger.from_crontab(crontab))
            if not config.quiet:
                click.echo(f"Actor {name} is scheduled with crontab: '{crontab}'.")

        try:
            scheduler.start()
            if not config.quiet:
                click.echo("Scheduler has been started.")

            import time
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
            if not config.quiet:
                click.echo("Scheduler has been shut down.")

    except ImportError:
        click.echo("Cannot schedule because dramatiq cannot be imported.", err=True)
        sys.exit(1)


# TODO: add arguments from dramatiq/cli.py
@main.command(help="Launch dramatiq worker")
@click.option("--processes", help="Number of worker processes to run", type=int)
@click.option("--threads", help="Number of worker threads per process", type=int, default=8)
@click.option("--queues", help="Listen to a subset of queues", multiple=True)
@click.option("--pid-file", help="Write PID file pf the master process to a file", type=str)
@click.option("--log-file", help="Write all logs to a file", type=str)
@click.option("--skip-logging", help="Do not call logging configuration", is_flag=True, default=False)
@click.option("--use-spawn", help="Start processes by spawning", is_flag=True, default=False)
@click.option("--fork-function", help="Fork a subprocess to run the given function", multiple=True, default=[])
@click.option("--worker-shutdown-timeout", help="Timeout for worker shutdown in ms", type=int, default=600000)
@decorate_with_common_options
def worker(**kwargs):
    from argparse import Namespace
    dramatiq_args = Namespace()
    dramatiq_args.broker = "dbload.resources.scenarios"  # Import any module to satisfy dramatiq main() function
    dramatiq_args.modules = []
    dramatiq_args.processes = kwargs.pop("processes")
    dramatiq_args.threads = kwargs.pop("threads")
    dramatiq_args.path = []
    dramatiq_args.queues = kwargs.pop("queues") or None
    dramatiq_args.pid_file = kwargs.pop("pid_file")
    dramatiq_args.log_file = kwargs.pop("log_file")
    dramatiq_args.skip_logging = kwargs.pop("skip_logging")
    dramatiq_args.use_spawn = kwargs.pop("use_spawn")
    dramatiq_args.forks = list(kwargs.pop("fork_function"))
    dramatiq_args.worker_shutdown_timeout = kwargs.pop("worker_shutdown_timeout")
    dramatiq_args.verbose = kwargs["verbose"]
    dramatiq_args.watch =  None

    update_cli_args(kwargs)
    global cli_args
    config = get_config(cli_args)

    try:
        from dramatiq import get_broker, actor as register_actor
        from dramatiq.cli import main as dramatiq_main, CPUS
        # from dramatiq.brokers.rabbitmq import RabbitmqBroker

        # broker = RabbitmqBroker(host="localhost", port="5672", heartbeat=5, blocked_connection_timeout=60)
        # dramatiq.set_broker(broker)

        if dramatiq_args.processes is None:
            dramatiq_args.processes = CPUS

        #broker = get_broker()

        # # Read SQL files and infuse context based on them
        # ctx = get_context()
        # ctx.infuse()

        # # Decorate all queries and scenarios as actors
        # for query_name in ctx.queries:
        #     register_actor(ctx.queries[query_name].function)
        # for scenario_name in ctx.scenarios:
        #     register_actor(ctx.scenarios[scenario_name].function)

        # print(broker.get_declared_actors())
        # print(broker.get_declared_queues())

        # import dbload.tests.debug
        dramatiq_main(args=dramatiq_args)
        # dramatiq_main()
    except ImportError:
        click.echo("Cannot launch worker because dramatiq cannot be imported", err=True)
        sys.exit(1)


@main.command(help="Display version of dbload")
def version():
    click.echo(f"{__version__}")


if __name__ == "__main__":
    main()
