from dbload import query, scenario, QueryResult
from faker import Faker

@query
def sort_employees(cursor):
    sql = "SELECT * FROM employees ORDER BY name"
    with cursor:
        cursor.execute(sql)
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
