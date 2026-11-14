-- =====================================================================
-- COMP 3005 - Assignment 3: PostgreSQL CRUD Application
-- File: sql/DML.sql
-- Purpose: Populate the students table with the initial data.
--
-- Run this file after sql/DDL.sql.
-- =====================================================================

-- INSERT INTO table_name(column1, column2, ...) VALUES (...), (...);
-- Inserts multiple tuples in one statement. student_id is not listed
-- because SERIAL generates it automatically (1, 2, 3).
INSERT INTO students (first_name, last_name, email, enrollment_date) VALUES
('John', 'Doe', 'john.doe@example.com', '2023-09-01'),
('Jane', 'Smith', 'jane.smith@example.com', '2023-09-01'),
('Jim', 'Beam', 'jim.beam@example.com', '2023-09-02');

-- Verify the insert: should return 3 tuples with student_id 1, 2 and 3.
SELECT *
FROM students
ORDER BY student_id;
