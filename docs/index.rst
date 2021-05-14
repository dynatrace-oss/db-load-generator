Database Load Generator
=======================

``db-load-generator`` is a Python framework and toolbox for generating artificial database loads with as little code as necessary.
It uses Java and JDBC drivers to connect to the databases. And comes with a command line and ready-to-use scenarios out of the box.

.. raw:: html

   <p>
      <a href="https://pypi.org/project/db-load-generator/"><img alt="PyPI" src="https://img.shields.io/pypi/v/db-load-generator?color=blue&logo=pypi"></a>
      <a href='https://db-load-generator.readthedocs.io/en/latest/?badge=latest'><img src='https://readthedocs.org/projects/db-load-generator/badge/?version=latest' alt='Documentation Status' /></a>
      <a href="https://pypi.org/project/db-load-generator/"><img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/db-load-generator"></a>
   </p>

**What db-load-generator can do**

* Generate load scenarios out of annotated SQL code
* Provide convenient decorators to build queries and scenarios
* Fully compatible with Python's DBAPI2
* Invoke any scenario or query using powerful CLI tool
* Configurable through config files, environment variables, and CLI arguments
* Can run as a `Dramatiq`_ background task queue processor

**Supported databases**

* Microsoft SQL Server
* Oracle
* IBM DB2 (both LUW and z/OS)
* SAP Hana DB
* Teradata DB
* MySQL
* PostgreSQL
* SQLite
* *any other database that comes with a JDBC driver...*

Getting Started
---------------

Basic setup
^^^^^^^^^^^

Create an annotated SQL file with a couple of queires in it.
We are going to start with two queries, one of which creates a simple table and the other one drops it.

``queries.sql``:

.. literalinclude:: tutorial/step_1.sql
   :language: sql

Launch ``dbload`` CLI to see how the queries were parsed:

.. code:: bash

   dbload --sql queries.sql show queires

The output below shows that two queries were produced from the parsed SQL file:

.. program-output:: dbload -s tutorial/step_1.sql show queries

Launch ``dbload`` CLI once again to show what scenarios were parsed:

.. code:: bash

   dbload --sql queries.sql show scenarios

One scenario called ``setup`` and the other one called ``teardown`` were parsed and created based on the annotated SQL file.
In this case, each scenario contains a link to the query that mentioned it in the annotation.
These queries will be executed in the order specified by the ``auto_run_queries`` list belonging to the scenario.

.. program-output:: dbload -s tutorial/step_1.sql show scenarios

You can see that these scenarios were created implicitly (without being explicitly declared in a python module),
because they were specified in the ``scenario: setup`` and ``scenario: teardown`` parts of the query annotations.
Each annotated SQL query can mention several scenarios as part of its annotations and these
scenarios will be created automatically, if they were not explicitly declared before.
If a query mentions a scenario in its annotation, then that query will get executed as part of the mentioned scenario.
Since several queries can mention the same scenario, in that scenario they are executed in the order they were defined in the SQL file.
Alternatively, execution order can be specified in square brackets after the name of the scenario: ``scenario: setup[100]``.
The lower the number – the higher is priority of the execution of that query.
Any such queires are executed before any other logic inside the defined scenario proceeds.

Connect to database
^^^^^^^^^^^^^^^^^^^

It's time to connect to the actual database to run our scenarios and queries!
At least `Java`_ 8 must be installed and ``JAVA_HOME`` environment variable should point to the location of the JVM installation.
If no suitable JVM is found there, common directories based on the platform will be searched.
On windows the registry will be consulted.
**JDBC** driver for the destination database must be present on the system as well.

In this example we will connect to the **SQLite** database and a proper driver
``sqlite-jdbc-3.34.0.jar`` (latest GA release at the time of the writing)
can be downloaded from `SQLite JDBC Driver`_ GitHub.

In order to connect, a couple of parameters must be specified:
*DSN string (URI)* and *class path* to the driver files. Let's **test our connection**:

.. code:: bash

   dbload \
      --dsn jdbc:sqlite:sample.db \
      --classpath sqlite-jdbc-3.34.0.jar \
      test

More feature-rich databases such as SQL Server, Oracle, SAP Hana DB, and others might require additional parameters
to be specified: JDBC driver class name (``--driver com.ibm.db2.jcc.DB2Jcc``) or driver arguments such as password, user,
or database name (``--driver-arg user=sa``) might be required.
But for SQLite using just the ``dsn`` and ``classpath`` is enough. The connection was successful:

.. program-output:: dbload test

Configuration sources
^^^^^^^^^^^^^^^^^^^^^

Specifying the connection parameters as command line arguments every time can get out of hands really quick.
Instead, let's put them in the config file.

``dbload.json``:

.. code:: json

   {
     "classpath": ["sqlite-jdbc-3.34.0.jar"],
     "dsn": "jdbc:sqlite:sample.db",
     "sql": ["queries.sql"]
   }

Every command line argument has its matching counterpart in the config file. If some of the arguments are not specified
in either of the locations, the default values are used.

By default, dbload looks for the ``dbload.json`` file in the current directory.
It is possible to specify a different configuration path using the ``--config other_dir/dbload.cfg`` option.
If non-default configuration file is not in the current directory, then any relative path in that file will be adjusted
according to the current working directory of dbload (directory from which dbload was launched).

Every configuration parameter can also be supplied as an environment variable with the ``DBLOAD_`` prefix.
For example:

.. code:: bash

   export DBLOAD_DSN="jdbc:sqlite:sample.db"

is equivalent to ``--dsn jdbc:sqlite:sample.db``.

Configurations are loaded in the following order **from least to most important**. Merging any new values on top of the old ones:

- Default values
- JSON file
- Environment variables
- Command line arguments

As mentioned above, more sophisticated databases require other parameters, such as driver arguments
with user names and passwords, to initiate a connection.
For some databases, the driver arguments must be presented as a dictionary and for others, as a list.
Both ways are supported. Choose based on what the particular database's driver needs.
Example for Microsoft SQL Server:

.. code:: json

   {
     "driver_arg": { "databaseName": "master", "user": "sa", "password": "StrongPassword!" }
   }

and for IBM DB2:

.. code:: json

   {
     "driver_arg": { "db2demo", "PaSsWoRdforDB2" }
   }

Execute a statement
^^^^^^^^^^^^^^^^^^^

You can execute a random statement against the database.
Let's see what tables we have in our fresh SQLite database. The database currently contains no tables:

.. command-output:: dbload execute "SELECT * FROM sqlite_master where type='table'"

Prepared statements with properties are also supported. This command will produce the exact same result:

.. command-output:: dbload execute "SELECT * FROM sqlite_master where type=?" --property table

Run queries
^^^^^^^^^^^

Let's run some of the queries we've declared earlier in the ``queries.sql`` file. Create a table:

.. code:: bash

   dbload query create_departments_table

.. program-output:: dbload -s tutorial/step_1.sql query create_departments_table

and then drop it:

.. code:: bash

   dbload query drop_departments_table

.. program-output:: dbload -s tutorial/step_1.sql query drop_departments_table

Run scenarios
^^^^^^^^^^^^^

Similarly, we can run entire scenarios from the command line.

.. code:: bash

   dbload scenario setup

.. program-output:: dbload -s tutorial/step_1.sql scenario setup

Our implicit scenario "setup" merely executes its ``auto_run_queries`` and does nothing else.
So, nothing besides the general "Executing..." is printed to the terminal.

Insert data
^^^^^^^^^^^

Let's insert some data into the table we've just created.
Add a new query that inserts data into the ``departments`` table:

.. literalinclude:: tutorial/step_2.sql
   :language: sql
   :emphasize-lines: 10,11

As you can see, ``add_department`` is a prepared statement.
It requires a property to be supplied before execution:

.. code:: bash

   dbload query add_department --property 'accounting'
   dbload query add_department -p 'r&d'

Notice how ``-p``  is a shortcut for ``--property``.
*dbload* CLI has shortcuts for almost all supported configuration properties.

.. program-output:: dbload -s tutorial/step_2.sql query add_department -p accounting && dbload -s tutorial/step_2.sql query add_department -p 'r&d'
   :shell:

The same approach with supplying data via properties can be applied to update and removal of data.

Select data
^^^^^^^^^^^

Now, to compose some queries that retrieve the data, let's add a query that retrieves all rows from ``departments`` table.

.. literalinclude:: tutorial/step_3.sql
   :language: sql
   :emphasize-lines: 13,14

But there is a new annotation tag: we've added ``option: return_random`` part to the annotation of the query.
That gives as an advangate by automatically generating an additional variant of the *get_departments* query,
which returns a single random row instead of all the rows.
That can come in handy when we need to quickly retrieve a random foreign key required for some other update or insert operation.

.. code:: bash

   dbload query get_departments

.. program-output:: dbload -s tutorial/step_3.sql query get_departments

Now, let's try the *"return_random"* variant of that query.

.. code:: bash

   dbload query get_departments_return_random

.. program-output:: dbload -s tutorial/step_3.sql query get_departments_return_random

Explicit scenarios
^^^^^^^^^^^^^^^^^^

We will now add employees to our database.
First, we'll add a couple more queries that will accomplish that.

.. literalinclude:: tutorial/step_4.sql
   :language: sql
   :emphasize-lines: 16-23,25-26

Now, let's define the first explicit scenario in a python module.

``scenarios.py``:

.. literalinclude:: tutorial/step_4.py
   :language: python
   :linenos:

Boy, that escalated quickly. Let's try to digest it line by line.
At first, two modules are imported: *dbload* and `Faker`_, a python package that generates fake data.

.. literalinclude:: tutorial/step_4.py
   :language: python
   :lines: 1,2
   :emphasize-lines: 1,2
   :linenos:

.. note::

   For all intents and purposes, the ``scenarios.py`` file we've created is a normal Python module.
   It can be a part of the package or contain any other logic or libraries.
   When we point ``dbload`` CLI to this file it imports the file as a module.

After that, we define a scenario using the ``@dbload.scenario`` decorator.
This decorator automatically registers the scenario within ``dbload`` and does some other things, like providing a valid open connection.

.. literalinclude:: tutorial/step_4.py
   :language: python
   :lines: 4-6
   :emphasize-lines: 1-3
   :linenos:
   :lineno-start: 4

For each employee we want to add to the database we'll open a new cursor and generate some fake data.
The department ID (``dep_id``), however, is a *foreign key* that has to reference an actual ID from the departments table.
That's where the *return_random* query variant will come handy. We will use it to retrieve a random department ID.

.. literalinclude:: tutorial/step_4.py
   :language: python
   :lines: 8-18
   :emphasize-lines: 7
   :linenos:
   :lineno-start: 8

Notice, how ``get_departments_return_random`` function is not actually defined anywhere in our python module.
But it was implicitly created from the annotated SQL file.
And by default, each scenario gets *infused* with all parsed queries, which are attached to the scenario function as attributes.
That's why we access that query as an attribute of the scenario.

The ``.first`` part then retrieves the first row returned by the query (and our *return_random* query returns only one row).
The first element in that tuple ``.first[0]`` is going to be the random department id we need.
We unpack the ``.first`` tuple to get both the department name and its ID.

Finally, we invoke the ``add_employee`` query and supply it with the data we've generated and collected.
Similarly, the ``add_employee`` query has been parsed from the SQL file and was attached to the scenario object as an attribute.

.. literalinclude:: tutorial/step_4.py
   :language: python
   :lines: 8-18
   :emphasize-lines: 10
   :linenos:
   :lineno-start: 8

.. note::

   You don't have to pass a new ``cursor`` argument to the query, when calling it.
   If no open cursor or connection are passed to a query or a scenario, then they will be created automatically.
   The downside to this is that in the scenario above a new connection will be created for each query
   invoked without a valid cursor.
   That would be 20 new connections sequentially opened and closed to invoke 2 queries x10 times.

Let's make sure the *employees* table is created and then add the employees to it by running the scenario we've created.

.. code:: bash

   dbload --ignore scenario setup

Since we've added a new query to the "setup" scenario and we want to run it again to create *employees* table we'll get errors,
because other tables (*departments*) already exist.
To ignore the errors we can specify the ``--ignore`` flag.
This flag works when invoking queries as well.

.. program-output:: dbload -s tutorial/step_4.sql -i scenario setup

Now, let's run the *load_employees* scenario:

.. code:: bash

   dbload --module scenarios.py scenario load_employees

.. program-output:: dbload -s tutorial/step_4.sql -m tutorial/step_4.py scenario load_employees


Explicit queries
^^^^^^^^^^^^^^^^

Let's add a new query but this time we will define it in the Python module.

.. literalinclude:: tutorial/step_5.py
   :language: python
   :lines: 1-10
   :emphasize-lines: 4-10

In this query we are not relying on the annotated SQL file at all, instead doing everything manually:
defining SQL statement in a string, executing it in the cursor, and fetching the results.
We could automate the result fetching part in the same way it happens within implicit queries.
In order to do that we are going to feed the cursor with executed statement to the ``QueryResult`` class.

.. literalinclude:: tutorial/step_6.py
   :language: python
   :lines: 1-10
   :emphasize-lines: 1,4,9,10

We've changed the import line to include *QueryResult*.
Now, when building a query result instance from the cursor, we get its convenience in return, e.g. using such methods as ``.first``.

.. code:: bash

   dbload --module scenarios.py query sort_employees

.. program-output:: dbload -m tutorial/step_6.py query sort_employees

How about we combine both annotated SQL and explicitly defined query?
It's convenient to store actual SQL statements in the SQL file, because we get a proper syntax highlighting,
reusability (use same ``.sql`` file in any SQL IDE), and keep our Python code more clean.

``queries.sql``:

.. literalinclude:: tutorial/step_7.sql
   :language: sql
   :lines: 28-29
   :emphasize-lines: 1-2

``scenarios.py``:

.. literalinclude:: tutorial/step_7.py
   :language: python
   :lines: 4-9
   :emphasize-lines: 4

The annotated SQL query *sort_employees* got matched with the explicitly defined query with the same name in the Python module.
The queires are created implicitly only when they were not defined in the python module.
In this case, the query was defined, so the annotated SQL statement got attached to the query function as a ``.sql`` attribute
that contains the actual statement.

By executing the rewritten query we'll get the same result:

.. code:: bash

   dbload --module scenarios.py query sort_employees

.. program-output:: dbload -m tutorial/step_7.py -s tutorial/step_7.sql query sort_employees

Standalone script
^^^^^^^^^^^^^^^^^

It's not required to use ``dbload`` CLI to invoke queries and scenarios.
Instead, we can turn our *scenarios.py* into a standalone script.

.. literalinclude:: tutorial/step_8.py
   :language: python
   :emphasize-lines: 1-10,36-47

We can run it as a normal Python script:

.. code:: bash

   python scenarios.py

.. program-output:: python tutorial/step_8.py

Background tasks
^^^^^^^^^^^^^^^^

It is possible to turn each query and scenario into a background task queue processor by using `Dramatiq`_.
All you need to do is to decorate the required objects with the ``@dramatiq.actor`` decorator.

Installation
------------

``db-load-generator`` can be installed from PyPI.
It needs `Java`_ installed and a `JDBC`_ driver to connect to the actual database.
For other installation options and :ref:`installation requirements` please see :doc:`/guides/installation`.

.. code:: bash

   pip install db-load-generator

Documentation
-------------

.. toctree::
   :caption: Guides
   :maxdepth: 1

   guides/installation
   guides/getting_started
   guides/advanced_usage

.. toctree::
   :caption: API reference
   :maxdepth: 1

   api/context
   api/query_parser
   api/exceptions


Attributions
------------

- DBLoad is built on top of the Python, Java/JDBC, and the excellent `JPype library <https://jpype.readthedocs.io/en/latest/>`_.
- Icons made by `Nikita Golubev <https://www.flaticon.com/authors/nikita-golubev>`_ and `Smashicons <https://smashicons.com/>`_ from `Flaticon <https://www.flaticon.com/>`_.
- `SQLite JDBC Driver`_ by `xerial <https://github.com/xerial>`_.


.. _Java: https://openjdk.java.net/install/index.html
.. _JDBC: https://en.wikipedia.org/wiki/Java_Database_Connectivity
.. _Official SQL Server driver: https://docs.microsoft.com/en-us/sql/connect/jdbc/download-microsoft-jdbc-driver-for-sql-server?view=sql-server-ver15
.. _SQL Server Docker: https://hub.docker.com/_/microsoft-mssql-server
.. _SQLite JDBC Driver: https://github.com/xerial/sqlite-jdbc
.. _Sphinx: https://www.sphinx-doc.org/
.. _ilexconf: https://github.com/ilexconf/ilexconf
.. _Faker: https://faker.readthedocs.io/en/stable/index.html
.. _Dramatiq: https://dramatiq.io