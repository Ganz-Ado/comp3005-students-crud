# COMP 3005 Assignment 3: PostgreSQL CRUD Application

A Python command-line application that connects to a PostgreSQL database and performs CRUD (Create, Read, Update, Delete) operations on a `students` table.

**Author:** Adonay Ganzasabwa

**Video demonstration:** _ADD YOUR VIDEO LINK HERE_

## Repository Structure

```
comp3005-students-crud/
├── sql/
│   ├── DDL.sql            # CREATE TABLE statement with constraints
│   └── DML.sql            # Initial data (3 students)
├── app/
│   └── students_app.py    # Database connection, CRUD functions, command-line interface
├── .env.example           # Template for the database connection settings
├── requirements.txt       # Python dependencies
└── README.md
```

## Prerequisites

- PostgreSQL and pgAdmin 4
- Python 3.10 or newer

## Step 1: Set Up the Database (pgAdmin)

1. In pgAdmin, right-click **Databases** → **Create** → **Database...**, name it `students_db`, and click **Save**.
2. Right-click `students_db` → **Query Tool**.
3. Open `sql/DDL.sql` (folder icon in the Query Tool) and press **F5**. This creates the `students` table.
4. Open `sql/DML.sql` and press **F5**. This inserts the initial data and shows the 3 tuples.

Schema created by `sql/DDL.sql`:

| Field | Type | Constraints |
|---|---|---|
| `student_id` | `SERIAL` (auto-incrementing integer) | `PRIMARY KEY` |
| `first_name` | `TEXT` | `NOT NULL` |
| `last_name` | `TEXT` | `NOT NULL` |
| `email` | `TEXT` | `UNIQUE NOT NULL` |
| `enrollment_date` | `DATE` | none (NULL allowed) |

## Step 2: Install the Application

Python is interpreted, so there is nothing to compile. Run these commands from the repository's root folder.

**Windows (PowerShell):**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again.

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Step 3: Configure the Database Connection

Copy `.env.example` to `.env`, then replace `YOUR_PASSWORD` with your PostgreSQL password:

```powershell
copy .env.example .env      # Windows (use cp on macOS / Linux)
```

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/students_db
```

If your database has a different name, user or port, change it in the same line. The `.env` file is listed in `.gitignore`, so your password is never committed to the repository.

## Step 4: Run the Application

On Windows, use `py` instead of `python3`.

```bash
python3 app/students_app.py list
python3 app/students_app.py add Alice Wong alice.wong@example.com 2024-01-15
python3 app/students_app.py update-email 2 jane.s@example.com
python3 app/students_app.py delete 3
```

Add `--echo` before the command to print each SQL statement, with its values, before it runs:

```
$ python3 app/students_app.py --echo update-email 2 jane.s@example.com
SQL> UPDATE students
     SET email = 'jane.s@example.com'
     WHERE student_id = 2;
Updated student 2: email is now jane.s@example.com
```

To see the effect of each operation in pgAdmin, right-click the `students` table → **View/Edit Data** → **All Rows**, and press **F5** in the data view to refresh after each change.

## Functions

### 1. `getAllStudents()`: Retrieve and display all students

**Command:** `python3 app/students_app.py list`

**SQL Statement:**

```sql
SELECT student_id, first_name, last_name, email, enrollment_date
FROM students
ORDER BY student_id;
```

**How the Query is Constructed:**

- `SELECT` lists the five columns of the table.
- `FROM` names the source table, `students`.
- `ORDER BY student_id` returns the tuples in ID order, so the output is predictable.

**Expected Result** (initial data):

```
student_id | first_name | last_name | email                  | enrollment_date
-----------+------------+-----------+------------------------+----------------
1          | John       | Doe       | john.doe@example.com   | 2023-09-01
2          | Jane       | Smith     | jane.smith@example.com | 2023-09-01
3          | Jim        | Beam      | jim.beam@example.com   | 2023-09-02
(3 rows)
```

### 2. `addStudent(first_name, last_name, email, enrollment_date)`: Insert a new student

**Command:** `python3 app/students_app.py add Alice Wong alice.wong@example.com 2024-01-15`

**SQL Statement:**

```sql
INSERT INTO students(first_name, last_name, email, enrollment_date)
VALUES (%s, %s, %s, %s)
RETURNING student_id;
```

**How the Query is Constructed:**

- `INSERT INTO students(...)` names the columns being filled. `student_id` is left out because `SERIAL` generates it.
- `VALUES (%s, %s, %s, %s)` holds placeholders; psycopg sends the actual values separately, which prevents SQL injection.
- `RETURNING student_id` gives back the ID PostgreSQL generated, so the program can report it.
- `enrollment_date` is optional: leave it out of the command and NULL is stored.

**Expected Result:** `Added student 4: Alice Wong <alice.wong@example.com>`, and a new tuple with `student_id` 4 appears in pgAdmin.

### 3. `updateStudentEmail(student_id, new_email)`: Update a student's email

**Command:** `python3 app/students_app.py update-email 2 jane.s@example.com`

**SQL Statement:**

```sql
UPDATE students
SET email = %s
WHERE student_id = %s;
```

**How the Query is Constructed:**

- `UPDATE students` names the table to modify.
- `SET email = %s` assigns the new email.
- `WHERE student_id = %s` limits the change to one student. Without the `WHERE` condition, every tuple in the table would get the new email.
- The number of changed tuples (`rowcount`) tells the program whether the student existed.

**Expected Result:** `Updated student 2: email is now jane.s@example.com`, and Jane Smith's email changes in pgAdmin.

### 4. `deleteStudent(student_id)`: Delete a student

**Command:** `python3 app/students_app.py delete 3`

**SQL Statement:**

```sql
DELETE FROM students
WHERE student_id = %s
RETURNING first_name, last_name;
```

**How the Query is Constructed:**

- `DELETE FROM students` names the table.
- `WHERE student_id = %s` deletes only that student. Without the `WHERE` condition, all tuples would be deleted.
- `RETURNING first_name, last_name` reports who was removed; no returned tuple means the ID did not exist.

**Expected Result:** `Deleted student 3: Jim Beam`, and Jim Beam's tuple disappears from pgAdmin.

## Error Handling

| Situation | Result |
|---|---|
| Duplicate email (violates `UNIQUE`) | Clear error message; nothing is changed |
| Unknown `student_id` for update or delete | "No student found"; nothing is changed |
| Invalid date (not `YYYY-MM-DD`) or blank required field | Rejected before any SQL runs |
| Wrong password, server not running, wrong database name | Connection error with the server's message |
| `students` table missing | Tells you to run `sql/DDL.sql` and `sql/DML.sql` |

Each operation runs in its own transaction: it is committed on success and rolled back on error.

## Resetting the Database

Run `sql/DDL.sql` and then `sql/DML.sql` again. `DDL.sql` drops and recreates the table, so all changes are removed and `student_id` numbering restarts at 1.

## AI Assistance Disclosure

The application code, SQL scripts and this README were written with assistance from Claude (Anthropic), an AI assistant, as permitted by the course's AI policy.
