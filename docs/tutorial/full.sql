-- name: create_departments_table, scenario: setup
CREATE TABLE departments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE
);

-- name: drop_departments_table, scenario: teardown
DROP TABLE IF EXISTS departments

-- name: add_department
INSERT INTO departments (name) VALUES (?);

-- name: get_departments, option: return_random
SELECT * FROM departments;

-- name: create_employees_table, scenario: setup
CREATE TABLE employees (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  title TEXT,
  dep_id INTEGER,
  FOREIGN KEY(dep_id) REFERENCES departments(id)
)

-- name: add_employee
INSERT INTO employees (name, title, dep_id) VALUES (?, ?, ?);

-- name: sort_employees
SELECT * FROM employees ORDER BY name;