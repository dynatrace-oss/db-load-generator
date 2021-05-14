-- name: create_dbload_schema, scenario: setup
CREATE SCHEMA DBLOAD;

-- comment line without name tag

-- name: drop_dbload_schema, scenario: teardown[900]
DROP SCHEMA DBLOAD;

-- name: drop_departments_table, scenario: teardown[100]
DROP TABLE DBLOAD.DBL_DEPARTMENTS;

-- name: create_departments_table, scenario: setup
CREATE TABLE DBLOAD.DBL_DEPARTMENTS (
	ID INTEGER IDENTITY(1, 1),
	NAME VARCHAR(50) NOT NULL,
	PRIMARY KEY (ID),
	UNIQUE (NAME)
);

-- name: insert_department
INSERT INTO DBLOAD.DBL_DEPARTMENTS (NAME) VALUES (?);

-- name: select_all_departments, option: return_random, option: run_once
SELECT * FROM DBLOAD.DBL_DEPARTMENTS;

-- name: drop_employees_table, scenario: teardown[80]
DROP TABLE DBLOAD.DBL_EMPLOYEES;

-- name: create_employees_table, scenario: setup
CREATE TABLE DBLOAD.DBL_EMPLOYEES (
	ID	BIGINT IDENTITY(1, 1),
	NAME VARCHAR(50) NOT NULL,
	DEPARTMENT_ID INTEGER NOT NULL,
	PRIMARY KEY (ID),
	FOREIGN KEY (DEPARTMENT_ID)
		REFERENCES DBLOAD.DBL_DEPARTMENTS (ID)
);

-- name: drop_employees_index, scenario: teardown[70]
DROP INDEX DBL_EMPLOYEES_NAME_IDX ON DBLOAD.DBL_EMPLOYEES;

-- name: create_employees_index, scenario: setup
CREATE UNIQUE INDEX DBL_EMPLOYEES_NAME_IDX ON DBLOAD.DBL_EMPLOYEES (NAME);

-- name: insert_employee
INSERT INTO DBLOAD.DBL_EMPLOYEES (NAME, DEPARTMENT_ID) VALUES (?, ?);

-- name: select_all_employees, option: return_random
SELECT * FROM DBLOAD.DBL_EMPLOYEES;

-- name: drop_clients_table, scenario: teardown[50]
DROP TABLE DBLOAD.DBL_CLIENTS;

-- name: create_clients_table, scenario: setup
CREATE TABLE DBLOAD.DBL_CLIENTS (
	ID BIGINT IDENTITY(1, 1) PRIMARY KEY,
	NAME VARCHAR(255) NOT NULL,
	PHONE VARCHAR(100) NOT NULL,
	EMAIL VARCHAR(255) NOT NULL,
	JOB_TITLE VARCHAR(255) NOT NULL,
	POLICY XML,
);

-- name: insert_client
INSERT INTO DBLOAD.DBL_CLIENTS (NAME, PHONE, EMAIL, JOB_TITLE, POLICY)
VALUES (?, ?, ?, ?, ?);

-- name: select_all_clients, option: return_random
SELECT * FROM DBLOAD.DBL_CLIENTS;

-- name: drop_sales_table, scenario: teardown[30]
DROP TABLE DBLOAD.DBL_SALES;

-- name: create_sales_table, scenario: setup
CREATE TABLE DBLOAD.DBL_SALES (
	ID BIGINT IDENTITY(1, 1),
	SALES_EMP_ID BIGINT NOT NULL,
	CLIENT_ID BIGINT NOT NULL,
	SUBJECT VARCHAR(500) NOT NULL,
	AMOUNT INTEGER NOT NULL,
	PRIMARY KEY (ID),
	FOREIGN KEY (SALES_EMP_ID)
		REFERENCES DBLOAD.DBL_EMPLOYEES (ID),
	FOREIGN KEY (CLIENT_ID)
		REFERENCES DBLOAD.DBL_CLIENTS (ID)
);

-- name: insert_sale
INSERT INTO DBLOAD.DBL_SALES (SALES_EMP_ID, CLIENT_ID, SUBJECT, AMOUNT)
VALUES (?, ?, ?, ?);

-- name: select_all_sales, option: return_random
SELECT * FROM DBLOAD.DBL_SALES;
