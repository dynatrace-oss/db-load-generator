-- name: create_departments_table, scenario: setup
CREATE TABLE departments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE
);

-- name: drop_departments_table, scenario: teardown
DROP TABLE IF EXISTS departments;