# SAP Hana DB Demo

## Requirements

* SAP Hana DB docker image pulled from the docker store: `store/saplabs/hanaexpress:2.00.045.00.20200121.1`
* SAP Hana DB JDBC driver (`ngdbc-2.7.15.jar`) placed locally in the `demo/sap-hana` directory

## Usage

1. `cd` into demo directory

   ```shell
   cd demo/sap-hana
   ```

1. Launch the database and RabbitMQ using docker compose

   ```shell
   docker compose up -d
   ```

1. Wait a few minutes and monitor database logs through docker for a message that database is ready

1. Setup the database structure using predefined `setup` scenario.

   This will create the `DBLOAD` schema along with the tables and indexes.

   ```shell
   dbload --predefined sap-hana scenario setup
   ```

1. (Optionally) Enable management web UI for RabbitMQ

   ```shell
   docker exec some-rabbit rabbitmq-plugins enable rabbitmq_management
   ```

1. Launch dbload worker process in a separate terminal window

   ```shell
   dbload worker --predefined sap-hana --processes 1 --threads 1
   ```

1. Launch dbload scheduler process in another terminal window.

   This will work as a CRON job by periodically sending everything scheduled in the `schedule` section of the config to the RabbitMQ broker.
   Which in turn gets picked up by the worker process.

   ```shell
   dbload scheduler --predefined sap-hana
   ```

1. Observe changes in the database

   You can launch a separate terminal window to check if sales get added to the `DBLOAD.SALES` table:

   ```shell
   dbload execute "select * from DBLOAD.SALES"
   ```

1. Shutdown the scheduler and the worker

1. Cleanup the database

   ```shell
   dbload -p sap-hana scenario teardown
   ```

1. Power off docker compose

   ```shell
   docker compose down
   ```