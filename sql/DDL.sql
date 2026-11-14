-- =====================================================================
-- COMP 3005 - Assignment 3: PostgreSQL CRUD Application
-- File: sql/DDL.sql
-- Purpose: Create the "students" table from the given schema.
--
-- Run this file first (pgAdmin Query Tool: open the file, press F5),
-- while connected to the database created for this assignment.
--
-- WARNING: DROP TABLE deletes the existing students table and all of its
-- tuples. This makes the script safe to re-run when resetting the
-- database to a clean state before the demo.
-- =====================================================================

-- DROP TABLE [IF EXISTS] table_name: remove a previous copy of the
-- table so the script can be re-run without an error.
DROP TABLE IF EXISTS students;

-- CREATE TABLE table_name (column datatype column_constraint, ...);
--   student_id      SERIAL: PostgreSQL's auto-incrementing INTEGER type
--                   (backed by a sequence). PRIMARY KEY = NOT NULL + UNIQUE,
--                   so every student is identified by exactly one value.
--   first_name      TEXT, NOT NULL: inserting NULL causes an error.
--   last_name       TEXT, NOT NULL.
--   email           TEXT, UNIQUE NOT NULL: required, and no two students
--                   may share the same email.
--   enrollment_date DATE with no constraint: a column accepts NULL by
--                   default, so the enrollment date is optional.
CREATE TABLE students (
    student_id      SERIAL PRIMARY KEY,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    email           TEXT UNIQUE NOT NULL,
    enrollment_date DATE
);
