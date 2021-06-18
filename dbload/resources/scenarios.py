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
# limitations under the License

from faker import Faker
from loguru import logger

from dbload import scenario, query

faker = Faker()


@scenario
def update_employee(con):

    # Fire or hire, restore
    choice = faker.random_element(elements=("fire", "hire", "restore"))

    if "hire" == choice:
        name = faker.name()
        birthday = faker.date_of_birth(minimum_age=20, maximum_age=75).strftime("%Y-%m-%d")
        dep_id = dep_name = None

        logger.info(f"Attempting to hire new employee: {name} ({birthday})")

        with con.cursor() as c:
            dep = update_employee.get_departments_return_random(c).first
            if not dep:
                logger.info(f"Cannot hire {name} ({birthday}) because there are no departments")
                return
            dep_id, dep_name = dep

        with con.cursor() as c:
            update_employee.add_employee(c, name=name, birthday=birthday, dep_id=dep_id)

            logger.info(f"New employee {name} ({birthday}) hired into department {dep_name}")

    elif "fire" == choice:
        emp_id = None

        with con.cursor() as c:
            emp = update_employee.find_employees_by_terminated_return_random(c, terminated=False).first
            if not emp:
                logger.info("Cannot fire anyone because there are no active employees")
                return

            emp_id = emp[0]
            logger.info(f"Attempting to fire {emp_id}")

        with con.cursor() as c:
            update_employee.terminate_employee(c, emp_id)
            logger.info(f"Employee {emp_id} is terminated")

    elif "restore" == choice:
        emp_id = None

        with con.cursor() as c:
            emp = update_employee.find_employees_by_terminated_return_random(c, terminated=True).first
            if not emp:
                logger.info("Cannot restore anyone because there are no terminated employees")
                return

            emp_id = emp[0]
            logger.info(f"Attempting to restore {emp_id}")

        with con.cursor() as c:
            update_employee.restore_employee(c, emp_id)
            logger.info(f"Employee {emp_id} is restored")


@scenario
def create_client(con):

    name = faker.name()
    phone = faker.phone_number()
    email = faker.ascii_company_email()
    job = faker.job()
    policy = f"<catalog><client><discount>{job}</discount></client></catalog>"

    with con.cursor() as c:
        create_client.add_client(c, name=name, phone=phone, email=email, job=job, policy=policy)
        logger.info(f"Added new client {name} with email <{email}> and phone {phone}")


@scenario
def update_client(con):

    phone = faker.phone_number()
    job = faker.job()
    policy = f"<catalog><client><discount>{job}</discount></client></catalog>"
    name = email = client_id = None

    with con.cursor() as c:
        client = update_client.get_clients_return_random(c).first
        if not client:
            logger.info("Cannot update client because there are no clients")
            return
        client_id, name, _, email, _, _ = client

    with con.cursor() as c:
        update_client.modify_client(c, name=name, phone=phone, email=email, job=job, policy=policy, client_id=client_id)
        logger.info(f"Client {name} <{email}> has new job '{job}'")


@scenario
def create_sale(con):

    subject = faker.sentence()
    amount = faker.random_int(min=2, max=9999)
    emp_id = emp_name = client_id = client_name = None

    with con.cursor() as c:
        emp = create_sale.find_employees_by_terminated_return_random(c, terminated=False).first
        if not emp:
            logger.info("Cannot create sale because there are no employees")
            return
        emp_id, emp_name, _, _, _ = emp

    with con.cursor() as c:
        client = create_sale.get_clients_return_random(c).first
        if not client:
            logger.info("Cannot create sales because there are no clients")
            return
        client_id, client_name, _, _, _, _ = client

    with con.cursor() as c:
        create_sale.add_sale(c, emp_id=emp_id, client_id=client_id, subjet=subject, amount=amount)
        logger.info(f"New sale is made: {emp_name} sold ${amount} of goods to {client_name}")


try:
    from dramatiq import set_broker, actor
    from dramatiq.brokers.rabbitmq import RabbitmqBroker
    from dbload import get_config

    config = get_config()
    broker = RabbitmqBroker(url=config.broker_url)
    set_broker(broker)

    logger.info("Decorating scenarios")
    actor(update_employee)
    actor(create_client)
    actor(update_client)
    actor(create_sale)

except ImportError:
    pass
