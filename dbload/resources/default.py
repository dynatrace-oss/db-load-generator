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
from dbload import scenario, query
import dramatiq


faker = Faker()


@dramatiq.actor
@scenario
def create_department(con):

    name = faker.word()
    create_department.insert_department(name=name)


@dramatiq.actor
@scenario
def create_employee(con):

    dep_id = create_employee.select_all_departments_return_random().get(0)[0]
    if dep_id is None:
        return

    name = faker.name()
    create_employee.insert_employee(name=name, dep_id=dep_id)


@dramatiq.actor
@scenario
def create_client(con):

    name = faker.name()
    phone = faker.phone_number()
    email = faker.ascii_company_email()
    job = faker.job()
    xml = f"<catalog><client><type>{job}</type></client></catalog>"

    create_client.insert_client(
        name=name, phone=phone, email=email, job=job, xml=xml
    )


@dramatiq.actor
@scenario
def create_sale(con):

    emp_id = create_sale.select_all_employees_return_random().get(0)[0]
    if emp_id is None:
        return

    client_id = create_sale.select_all_clients_return_random().get(0)[0]
    if client_id is None:
        return

    subject = faker.sentence()
    amount = faker.pyint()

    create_sale.insert_sale(
        emp_id=emp_id, client_id=client_id, subjet=subject, amount=amount
    )


@dramatiq.actor
@query
def count_sales(cur):
    stmt = "select count(*) from DBLOAD.DBL_SALES"
    sales = -1
    with cur:
        cur.execute(stmt)
        row = cur.fetchone()
        sales = row[0]
    return sales


@dramatiq.actor
@scenario
def sales_statistics(con):
    with con.cursor() as cur:
        sales = count_sales(cur)
        print(f"Current number of sales in the DB is {sales}.")
