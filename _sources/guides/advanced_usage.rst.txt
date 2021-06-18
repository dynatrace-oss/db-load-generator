Advanced Usage
==============

Scenarios
---------

This decorator registers a function or a class as a scenario in the
given :class:`~dbload.context.Context`. Registered scenarios can
later be invoked and executed by a play or directly.

When invoked, each scenario gets a :class:`~jaydebeapi.Connection`
object with an active connection to the database. Scenarios can obtain
cursors from this object in order to pass them to the executed queries.

By default, each scenario gets "infused" with all the SQL queries
from the parsed SQL files. Every parsed query becomes an attribute
of the scenario object. This is done for the convenience
purposes and allows you to invoke any parsed SQL query within the
scenario. In the example below we invoke ``insert_department``
query which was declared in the SQL file:

.. code:: sql

   -- name: insert_department
   INSERT INTO DBL_DEPARTMENTS (NAME) VALUES (?);

It can be invoked like this:

.. code:: python

   @context.scenario
   def my_scenario(connection):
       with connection.cursor() as cur:
           my_scenario.insert_department(cur, "New Department")

Examples of scenarios
^^^^^^^^^^^^^^^^^^^^^

Register a function as a scenario in ``context`` under the name
"create_users":

.. code:: python

   @context.scenario
   def create_users(connection):
       print("Do something")

Register a class as a scenario in ``context`` under the name
"createusers":

.. code:: python

   @context.scenario
   class CreateUsers():
       def __call__(self, connection):
           print("Do something")

Register scenario under a name that differs from the decorated
object's name:

.. code:: python

   @context.scenario(name="create_users")
   class my_scenario(connection):
       print("Do something")

Create a cursor within scenario and use it to manually execute a
query:

.. code:: python

   @context.scenario
   def create_users(connection):
       with connection.cursor() as cur:
           stmt = "INSERT INTO USERS VALUES (USERS_SEQ.nextval, 'Alexander', 'Dortmund')"
           cur.execute(stmt)

Queries
-------

When a function decorated by the this decorator is called it gets
passed two arguments: ``cursor`` and ``sql``.

``cursor`` is an individual cursor object created by scenario that
executes this the query function. Cursor object has an ``execute``
method capable of running text queries against connected database.

``sql`` is a SQL query string that mathes this function. The match
is found either through the ``match`` parameter of the decorator or
by matching decorated function's or class's name.

The query might not have a matching SQL query. But if it does
you may use ``curosr.execute`` and ``sql`` arguments to run it.

You can also directly use the ``cursor.execute`` method to run your own
query. Below are few options to declare and invoke a function or a class
decorated with the ``query`` decorator.

This decorator also sets the ``_is_decorated_by_query`` attribute of
decorated function to True. This is later used during safety validation
to make sure that the method is decorated by the ``@context.query``
before being decorated further by such decorators as ``@context.simple``.

Examples of queries
^^^^^^^^^^^^^^^^^^^

Method that has a matching query called "create_table" in the SQL
queries file:

.. code:: python

   @context.query
   def create_table(cursor, sql):
       with cursor as c:
           c.execute(sql)

and its matching query from the SQL queries file, annotated by the
``-- name: create_table`` comment line:

.. code:: sql

   -- name: create_table
   CREATE TABLE DEPARTMENTS (
       ID INTEGER GENERATED ALWAYS AS IDENTITY,
       NAME VARCHAR(50) NOT NULL,
       PRIMARY KEY (ID),
       UNIQUE (NAME)
   );

The next method below simply uses cursor directly to execute some
text query and ignores any matching queries from the SQL file:

.. code:: python

   @context.query
   def do_whatever(cursor):
       rs = None
       with cursor as c:
           description, rs = c.execute("SELECT * FROM employees;")
           print(description)
       return rs

Method within a class:

.. code:: python

   @context.query
   def insert_sale(self, cursor, sql, amount=100):
       with cursor as c:
           c.execute("INSERT INTO SALES VALUES (?)", [amount])

Below is a method that does not use ``cursor`` or ``sql`` arguments
at all. This makes the decorator useless, because the main purpose of
the decorator is to pass the connection cursor and a matching SQL query
to the function during it's execution:

.. code:: python

   @context.query
   def some_logic():
       import time
       time.sleep(1)
       print("I do whatever I want")

This method will look for query that matches the ``match`` parameter
of the decorator and supply it via ``sql`` argument to the function:

.. code:: python

   @context.query(match="create_employees_index")
   def my_logic(cursor, sql):
       with cursor as c:
           c.execute(sql)

This method achieves the exact same result. But instead of
looking up the query using the ``match`` parameter it find the
matching query using the ``__name__`` of the decorated function
by default (in this case it's "create_employees_index"):

.. code:: python

   @context.query
   def create_employees_index(cursor, sql):
       cursor.execute(sql)
       print(cursor.fetchall())
       cursor.close()

SQL files
---------

The ``name:`` tag
^^^^^^^^^^^^^^^^^

When parser detects a comment that starts with ``--`` and contains
``name: my_query`` somewhere in the line, it treats every next line
as a part of the query named ``my_query``:

.. code:: sql

   -- name: select_all
   SELECT *
     FROM EMPLOYEES
    ORDER BY NAME;

When parser encounters another line that contains the ``name:`` tag,
it takes all accumulated lines, glues them together, and saves them
in the context under their annotated name:

.. code:: sql

   -- name: select_all
   SELECT *
     FROM EMPLOYEES
    ORDER BY NAME;

   -- name: select_james
   /*
    * At this moment, right after encountering another line with the "name:"
    * tag, parser takes everything between the lines "-- name: select_all"
    * and "-- name: select_james" and saves it as the contents of the
    * "select_all" query.
   */
   SELECT * FROM EMPLOYEES WHERE NAME = 'James';

If there was some text or other queries that were not annotated
at the beginning of the file, then they will be skipped and thrown
out. The parser only considers queries that start with the comment
line that contains ``name:`` tag in it:

.. code:: sql

   -- file: SQL Queries

   SELECT 1 FROM DUAL;

   /* All this text above will be ignored, including this comment */

   -- name: select_all
   SELECT *
     FROM EMPLOYEES
    ORDER BY NAME;

Name tag can contain any alphanumeric characters or, generally
speaking, any characters that matches ``\w`` regex:
``[a-zA-Z0-9_]``. It permits lowercase and uppercase characters as
well as numbers and underscore:

.. code:: sql

   -- name: my_query
   -- name: c0oL_qUeRy
   ... etc

Comments without ``name:`` tag
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If parser encounters a comment line that starts with the ``--``
but does not contain a ``name:`` tag it will just skip it as if
it this line does not exist:

.. code:: sql

   -- name: my_query
   SELECT *
     -- this comment will be ignored
     FROM MY_TABLE;

Parser also ignores multiline-format comments that start with the
``/*`` and end with the ``*/`` symbols:

.. code:: sql

   SELECT *
     /* this will be ignored even with "name: my_query" inside */
     FROM MY_TABLE;

The ``scenario:`` tag
^^^^^^^^^^^^^^^^^^^^^

The ``scenario:`` tag is **optional**. It tells the parser which implicit
scenario this query should belong to. Implicit scenario is a scenario that
was not explicitly declared in the python file where :class:`~.Context`
object is defined. Implicit scenarios declared in the query annotations are
automatically created in the :class:`~.Context` object:

.. code:: sql

   -- name: select_james, scenario: single_select
   SELECT * FROM EMPLOYEES WHERE NAME = 'James';

The example above will implicitly create a scenario called ``single_select``.
When executed directly or inside a play, the ``single_select`` scenario will
run a query called ``select_james`` and that's all. This demonstrates that
defining scenarios explicitly in Python is not mandatory. It is possible to
just mention the scenario across one or many queries in the SQL files and
it will get automatically created and populated with those queries.

A query can belong to multiple implicit scenarios, by specifying the
``scenario:`` tag multiple times:

.. code:: sql

   -- name: select_all, scenario: run_all, scenario: show_deps
   SELECT * FROM DEPARTMENTS;

   -- name: insert_employee, scenario: run_all, scenario: insert
   INSERT INTO EMPLOYEES(ID) VALUES(EMP_SEQ.NEXT);

In the example above 3 scenarios will be auto-generated and added
to the :class:`~.Context` object: ``run_all``, ``show_deps``, and
``insert``. All of them do not exist in the python file but they
will now be created in the context.
When executed, ``run_all`` scenario will run 2 queries one after the
other. First, it will execute the ``select_all`` query. Then it will
execute the ``insert_employee`` query.

All return values for queries executed within implicitly generated
scenarios are ignored.

Since every explicitly defined scenario is already infused with all
the parsed SQL queries, then there is no need to use scenario tag
for queries used in explicitly defined scenarios.

Main purpose of the ``scenario:`` tag is to create implicit scenarios
that are burdensome to declare in python and mostly represent
boilerplate code. For example, a scenario that pre-creates or
destroys all tables, schema, sequences, and data required for running
the simulated load.

Ordered ``scenario[30]``
^^^^^^^^^^^^^^^^^^^^^^^^

By default, when two or more queries mention the same
scenario in their annotation, these queries get executed in the
order in which they were declared in the SQL file.

When mentioning implicit scenarios in the annotation of the SQL
queries it is possible to specify the order of execution of this
particular query within the generated scenario.

For example, these two queries mention the same implicit scenario
called ``teardown``:

.. code:: sql

   -- name: drop_dbload_schema, simulation: teardown[900]
   DROP SCHEMA DBLOAD;

   -- name: drop_departments_table, simulation: teardown[100]
   DROP TABLE DBLOAD.DBL_DEPARTMENTS;

But because they specify the order in the square brackets, the
``drop_department_table`` query will get executed before the
``drop_dbload_schema`` query, since it's "priority" within the
``teardown`` scenario is higher (``100 < 900`` – the smaller the number,
the higher is priority).

Order numbers in the square brackets are sorted in the ascending order,
which means that ``-100`` will be executed before ``0``. And ``4`` will be
executed before ``10``.
