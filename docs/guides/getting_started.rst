Getting Started
===============

After :doc:`/guides/installation` the ``dbload`` library can be imported
and built upon.

For the examples to run, you'd need:

- Python 3.9 or above
- ``db-load-generator`` package installed
- Java 8 or above
- JDBC driver for Microsoft SQL Server
- Docker or an actual SQL Server running

Simple example
--------------

Let's create a simple simulation which consists of a play, scenario, and
a query.

``play.py``:

.. code:: python

   import time
   from dbload import Context

   context = Context()

   @context.query
   def select_james(cursor):
       return cursor.execute("SELECT * FROM employees WHERE name = 'James'")

   @context.scenario
   def my_scenario(connection):
       with connection.cursor() as cur:
           select_james(cur)

   @context.play
   def my_play(config):
       while True:
           with context.connection() as conn:
               my_scenario(conn)
           time.sleep(1)

The example above does not use SQL files for storing any annotated queries.
Let's create a config file for our simulation. We are going to run it
against a local SQL Server database. The config can be stored in the
``dbload.cfg`` file in the same directory:

.. code:: json

   {
       "jdbc_driver_path": "mssql-jdbc-8.4.1.jre8.jar",
       "jdbc_driver_name": "jdbc:sqlserver",
       "jdbc_driver_class": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
       "database_host": "localhost",
       "database_port": 1433,
       "database_name": "master",
       "database_user": "sa",
       "database_pass": "StrongPassword!",
       "uri": "{{ jdbc_driver_name }}://{{ database_host }}:{{ database_port }}",
       "args": {
           "databaseName": "{{ database_name }}",
           "user": "{{ database_user }}",
           "password": "{{ database_pass }}"
       }
   }

The SQL Server database can be started locally using docker:

.. code:: bash

   docker run --rm -d                \
     --name mssql                    \
     --privileged                    \
     -e ACCEPT_EULA=Y                \
     -e SA_PASSWORD=StrongPassword!  \
     -p 1433:1433                    \
     mcr.microsoft.com/mssql/server:latest

Let's try to execute the query itself:

.. code:: bash

   # Run the query
   dbload run play:select_james

   # Execute scenario
   dbload run play:my_scenario

   # Run whole play
   dbload run play:my_play

Adding SQL queries file
-----------------------

Let's try to achieve the same thing we did above by introducing a file with
the annotated SQL queries. Having actual SQL queries in a separate file is
extremely convenient:

- you don't have to store them as string in Python;
- you can enable syntax highlighting and linter;
- you can reuse the queries from these files somewhere else.

``queries.sql``:

.. code:: sql

   -- name: select_james, scenario: my_scenario
   SELECT * FROM employees WHERE name = 'James';

With this SQL queries file, the Python file can be reduced to:

.. code:: python

   import time
   from dbload import Context
   context = Context()

   @context.play
   def my_play(config):
       while True:
           with context.connection() as conn:
               my_scenario(conn)
           time.sleep(1))

And now we can call all the same commands:

.. code:: bash

   # Run the query
   dbload run play:select_james

   # Execute scenario
   dbload run play:my_scenario

   # Run whole play
   dbload run play:my_play




Levels and scopes of objects
----------------------------

+----------------------------+-------------------------+-------------------------+-------------------+
| Object                     | Scope                   | Provided with           | Can be implicitly |
|                            |                         |                         | created?          |
+============================+=========================+=========================+===================+
| :class:`~.Context`         | Configuration, plays,   | Nothing.                | No                |
|                            | scenarios, and queries. |                         |                   |
+----------------------------+-------------------------+-------------------------+-------------------+
| :meth:`~.Context.play`     | Managing connections,   | Config, context, all    | No                |
|                            | launching scenarios.    | scenarios, all queries. |                   |
+----------------------------+-------------------------+-------------------------+-------------------+
| :meth:`~.Context.scenario` | Managing cursors,       | Open connection,        | Yes               |
|                            | launching queries.      | all queries.            |                   |
+----------------------------+-------------------------+-------------------------+-------------------+
| :meth:`~.Context.query`    | Executing query using   | Open cursor, SQL text.  | Yes               |
|                            | cursor.                 |                         |                   |
+----------------------------+-------------------------+-------------------------+-------------------+


Start RabbitMQ

.. code:: bash

   docker run --rm --name rabbitmq -p 5672:5672 --hostname my-rabbit rabbitmq

Start Dramatiq workers

.. code:: bash

   dramatiq play
