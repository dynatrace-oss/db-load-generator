# db-load-generator

`db-load-generator` is a Python framework and toolbox for generating artificial database loads with as little code as necessary.
It uses Java and JDBC drivers to connect to the databases.

<p>
    <a href="https://pypi.org/project/db-load-generator/"><img alt="PyPI" src="https://img.shields.io/pypi/v/db-load-generator?color=blue&logo=pypi"></a>
    <a href="https://pypi.org/project/db-load-generator/"><img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/db-load-generator?color=blue&logo=pypi"></a>
    <a href="https://github.com/dynatrace-oss/db-load-generator/actions/workflows/build-test-release.yml"><img alt="Build Status" src="https://img.shields.io/github/workflow/status/dynatrace-oss/db-load-generator/Build%20Test%20Release?logo=github" /></a>
    <a href="https://dbload.org"><img src="https://img.shields.io/github/workflow/status/dynatrace-oss/db-load-generator/Build%20Docs?label=docs&logo=github" alt="Documentation Build Status" /></a>
    <a href="https://github.com/dynatrace-oss/db-load-generator/blob/main/LICENSE"><img alt="GitHub" src="https://img.shields.io/github/license/dynatrace-oss/db-load-generator"></a>
</p>

## Getting Started

New to `db-load-generator`? Checkout our official [Getting Started](https://db-load-generator.readthedocs.io/) guide.


## Requirements

* Python 3.9 or above.
* Java 8 or above.
* JDBC driver for your database.

## Features

* Test connection to the database using `dbload test`
* Execute a query using `dbload execute`
* Configure db-load-generator via
  * command line arguments
  * environment variables
  * default config file `dbload.json`
  * custom path config file
* Print current parsed configuration using `dbload show settings`
* Use decorators from `dbload` library to create scenarios and queries
* Write annotated SQL queries in the `.sql` file and feed them using `dbload --sql myfile.sql`
* Show current parsed queries using `dbload show queries`
* Run any defined query using `dbload query`
* Write full-fledged complex simulation scenarios using `dbload` library
* Show current parsed scenarios using `dbload show scenarios`
* Run any defined scenarios using `dbload scenario`
* Use predefined simulations for popular databases using `dbload --predefined <db-name> ACTION`
* Run db-load-generator as a background worker using [dramatiq](https://dramatiq.io)
  * ensure there is a RabbitMQ running as a message broker
  * runs scenarios as service workers `dbload worker`
  * enqueue executions into broker using `dbload send <scenario name or actor name>`
  * start beats/scheduler process using `dbload scheduler`

## Development & Contributions

Contributions are welcome!
If you are interested in contributing to the project please read our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

[Apache Version 2.0](LICENSE)
