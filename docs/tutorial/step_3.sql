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