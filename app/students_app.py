"""
COMP 3005 - Assignment 3: PostgreSQL CRUD Application
File: app/students_app.py

A command-line Python application that connects to a PostgreSQL database
and performs CRUD operations on the "students" table:

    Create -> addStudent()          (SQL INSERT)
    Read   -> getAllStudents()      (SQL SELECT)
    Update -> updateStudentEmail()  (SQL UPDATE)
    Delete -> deleteStudent()       (SQL DELETE)

Commands:
    python app/students_app.py list
    python app/students_app.py add <first_name> <last_name> <email> [enrollment_date]
    python app/students_app.py update-email <student_id> <new_email>
    python app/students_app.py delete <student_id>

Add --echo before the command to print every SQL statement as it runs:
    python app/students_app.py --echo list

The database connection is read from DATABASE_URL in a .env file
(see .env.example and README.md).
"""

import argparse
import os
import sys
from datetime import date

import psycopg
from psycopg import ClientCursor, errors
from dotenv import load_dotenv


# ---------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------

# Load DATABASE_URL from the .env file in the repository root (if it
# exists). Keeping the password in .env, which .gitignore excludes, means
# it is never committed to the public repository.
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DEFAULT_DATABASE_URL = "postgresql://postgres@localhost:5432/students_db"

# Set to True by the --echo option: every SQL statement is printed with
# its values before it is executed (useful for the demo video).
ECHO_SQL = False


def get_connection():
    """Open and return a new connection to the PostgreSQL database."""
    return psycopg.connect(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))


def execute(conn, cur, sql, params=None):
    """Execute one SQL statement, printing it first if --echo is on.

    The statement is always sent with its values as separate parameters
    (%s placeholders), never pasted into the SQL text, which prevents SQL
    injection. The echoed text only shows what the values will be.
    """
    if ECHO_SQL:
        shown = ClientCursor(conn).mogrify(sql, params)
        print("SQL> " + shown.replace("\n", "\n     "))
    cur.execute(sql, params)


# ---------------------------------------------------------------------
# Helper functions (input validation and output formatting)
# ---------------------------------------------------------------------

def parse_date(value):
    """Convert a 'YYYY-MM-DD' string to a date object.

    Returns None for None or an empty string, because enrollment_date
    accepts NULL. Raises ValueError for a bad format.
    """
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(
            f"Invalid date '{value}'. Use the format YYYY-MM-DD, e.g. 2024-01-15."
        ) from None


def require_text(field_name, value):
    """Make sure a required text field is not empty or only spaces.

    NOT NULL only rejects NULL, and NULL is not the same as an empty
    string, so the database alone would accept ''. This check rejects
    blank values. Returns the value with surrounding spaces removed.
    """
    if value is None or value.strip() == "":
        raise ValueError(f"{field_name} cannot be empty.")
    return value.strip()


def print_students(rows):
    """Print student tuples as an aligned table (similar to psql output)."""
    headers = ["student_id", "first_name", "last_name", "email", "enrollment_date"]

    # Convert every value to text; a NULL enrollment_date is shown as NULL.
    table = [
        [str(value) if value is not None else "NULL" for value in row]
        for row in rows
    ]

    # Each column is as wide as its longest header or value.
    widths = [
        max([len(headers[i])] + [len(row[i]) for row in table])
        for i in range(len(headers))
    ]

    print(" | ".join(h.ljust(w) for h, w in zip(headers, widths)).rstrip())
    print("-+-".join("-" * w for w in widths))
    for row in table:
        print(" | ".join(v.ljust(w) for v, w in zip(row, widths)).rstrip())
    print(f"({len(rows)} row{'s' if len(rows) != 1 else ''})")


# ---------------------------------------------------------------------
# CRUD functions required by the assignment
# (names use camelCase on purpose, to match the assignment specification)
# ---------------------------------------------------------------------

def getAllStudents():
    """READ: Retrieve and display all records from the students table.

    Returns the list of tuples:
    (student_id, first_name, last_name, email, enrollment_date)
    """
    # "with" closes the connection automatically when the block ends.
    with get_connection() as conn:
        with conn.cursor() as cur:
            # SELECT column_list FROM table ORDER BY column:
            # ORDER BY student_id shows the students in ID order.
            execute(conn, cur,
                    "SELECT student_id, first_name, last_name, email, enrollment_date\n"
                    "FROM students\n"
                    "ORDER BY student_id;")
            rows = cur.fetchall()

    print_students(rows)
    return rows


def addStudent(first_name, last_name, email, enrollment_date):
    """CREATE: Insert a new student record into the students table.

    enrollment_date may be a 'YYYY-MM-DD' string, a date object, or None.
    Returns the new student_id, or None if the insert failed.
    """
    # Validate input in Python first so the user gets a clear message.
    try:
        first_name = require_text("first_name", first_name)
        last_name = require_text("last_name", last_name)
        email = require_text("email", email)
        enrollment_date = parse_date(enrollment_date)
    except ValueError as e:
        print(f"Error: {e}")
        return None

    try:
        # Leaving the "with" block normally commits the transaction;
        # an exception inside it rolls the transaction back.
        with get_connection() as conn:
            with conn.cursor() as cur:
                # INSERT INTO table(column1, ...) VALUES (value1, ...):
                # student_id is omitted because SERIAL generates it, and
                # RETURNING gives back the generated value.
                execute(conn, cur,
                        "INSERT INTO students(first_name, last_name, email, enrollment_date)\n"
                        "VALUES (%s, %s, %s, %s)\n"
                        "RETURNING student_id;",
                        (first_name, last_name, email, enrollment_date))
                new_id = cur.fetchone()[0]
    except errors.UniqueViolation:
        # The UNIQUE constraint on email rejected a duplicate value.
        print(f"Error: a student with email '{email}' already exists.")
        return None

    print(f"Added student {new_id}: {first_name} {last_name} <{email}>")
    return new_id


def updateStudentEmail(student_id, new_email):
    """UPDATE: Change the email address of the student with student_id.

    Returns True if a tuple was updated, False otherwise.
    """
    try:
        new_email = require_text("new_email", new_email)
    except ValueError as e:
        print(f"Error: {e}")
        return False

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # UPDATE table SET column = value WHERE condition:
                # the WHERE condition limits the change to one student.
                # Without it, every tuple in the table would be updated.
                execute(conn, cur,
                        "UPDATE students\n"
                        "SET email = %s\n"
                        "WHERE student_id = %s;",
                        (new_email, student_id))
                # rowcount is the number of tuples the UPDATE changed.
                updated = cur.rowcount
    except errors.UniqueViolation:
        print(f"Error: email '{new_email}' is already used by another student.")
        return False

    if updated == 0:
        print(f"No student found with student_id {student_id}. Nothing updated.")
        return False

    print(f"Updated student {student_id}: email is now {new_email}")
    return True


def deleteStudent(student_id):
    """DELETE: Remove the record of the student with student_id.

    Returns True if a tuple was deleted, False otherwise.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            # DELETE FROM table WHERE condition: the WHERE condition
            # deletes only this student. Without it, ALL tuples would be
            # deleted. RETURNING shows which student was removed.
            execute(conn, cur,
                    "DELETE FROM students\n"
                    "WHERE student_id = %s\n"
                    "RETURNING first_name, last_name;",
                    (student_id,))
            deleted = cur.fetchone()

    if deleted is None:
        print(f"No student found with student_id {student_id}. Nothing deleted.")
        return False

    print(f"Deleted student {student_id}: {deleted[0]} {deleted[1]}")
    return True


# ---------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------

def build_parser():
    """Define the command-line commands and their arguments."""
    parser = argparse.ArgumentParser(
        description="CRUD operations on the PostgreSQL students table."
    )
    parser.add_argument(
        "--echo", action="store_true",
        help="print each SQL statement before it is executed",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list -> getAllStudents()
    sub.add_parser("list", help="Display all students")

    # add -> addStudent(first_name, last_name, email, enrollment_date)
    p_add = sub.add_parser("add", help="Add a new student")
    p_add.add_argument("first_name")
    p_add.add_argument("last_name")
    p_add.add_argument("email")
    p_add.add_argument(
        "enrollment_date",
        nargs="?",
        default=None,
        help="YYYY-MM-DD (optional; omit to store NULL)",
    )

    # update-email -> updateStudentEmail(student_id, new_email)
    p_upd = sub.add_parser("update-email", help="Update a student's email")
    p_upd.add_argument("student_id", type=int)
    p_upd.add_argument("new_email")

    # delete -> deleteStudent(student_id)
    p_del = sub.add_parser("delete", help="Delete a student")
    p_del.add_argument("student_id", type=int)

    return parser


def main():
    """Parse the command, call the matching CRUD function, and report
    database connection problems clearly. Returns the exit code."""
    global ECHO_SQL
    args = build_parser().parse_args()
    ECHO_SQL = args.echo

    try:
        if args.command == "list":
            getAllStudents()
            ok = True
        elif args.command == "add":
            ok = addStudent(
                args.first_name, args.last_name, args.email, args.enrollment_date
            ) is not None
        elif args.command == "update-email":
            ok = updateStudentEmail(args.student_id, args.new_email)
        else:  # "delete"
            ok = deleteStudent(args.student_id)
    except psycopg.OperationalError as e:
        # Server not running, wrong password, wrong database name, etc.
        print("Error: could not connect to the database. "
              "Check DATABASE_URL in your .env file (see README.md).")
        print(f"Details: {str(e).strip()}")
        return 1
    except errors.UndefinedTable:
        print("Error: the students table does not exist. "
              "Run sql/DDL.sql and sql/DML.sql first.")
        return 1
    except psycopg.Error as e:
        # Any other database error.
        print(f"Database error: {str(e).strip()}")
        return 1

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
