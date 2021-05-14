#!/usr/bin/env python

from dbload import (
    query,
    scenario,
    QueryResult,
    get_context,
    get_connection,
    get_config,
)
from faker import Faker

@query
def sort_employees(cursor):
    with cursor:
        cursor.execute(sort_employees.sql)
        name = QueryResult.from_cursor(cursor).first[1]
        print(f"Alphabetically first employee: {name}")

@scenario
def load_employees(connection):
    fake = Faker()

    for _ in range(10):
        name = fake.name()
        title = fake.job()
        dep_id = dep_name = None

        with connection.cursor() as c:
            dep_id, dep_name = load_employees.get_departments_return_random(c).first

        with connection.cursor() as c:
            load_employees.add_employee(c, name, title, dep_id)
            print(f"New employee: {name} working as '{title}' in '{dep_name}'.")

if __name__ == "__main__":
    # Initialize config: will search and parse config file, env vars, etc.
    config = get_config({"driver": "org.sqlite.JDBC", "verbose": 0})
    # Get global context
    context = get_context()
    # Infuse context with content parsed from annotated SQL file
    context.infuse()
    # Initialize new connection
    connection = get_connection(config)
    # Invoke something...
    with connection.cursor() as cur:
        sort_employees(cur)
