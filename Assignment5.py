# Assignment 5
# Shubaan, Nia, Dillon

import sqlite3


# Shubaan - classes and helper functions

# CLASSES
# Updated from Assignment 3 to include login/logout and new scheduling methods

class User:

    def __init__(self):
        self.first_name = ""
        self.last_name = ""
        self.user_id = 0
        self.logged_in = False

    def set_first_name(self, first_name):
        self.first_name = first_name

    def set_last_name(self, last_name):
        self.last_name = last_name

    def set_id(self, user_id):
        self.user_id = user_id

    def login(self):
        self.logged_in = True
        print(f"{self.first_name} {self.last_name} logged in.")

    def logout(self):
        self.logged_in = False
        print(f"{self.first_name} {self.last_name} logged out.")

    def print_info(self):
        print(f"First Name: {self.first_name} | Last Name: {self.last_name} | ID: {self.user_id}")


class Student(User):

    def __init__(self):
        super().__init__()
        self.grad_year = 0
        self.major = ""
        self.email = ""

    def set_grad_year(self, year):
        self.grad_year = year

    def set_major(self, major):
        self.major = major

    def set_email(self, email):
        self.email = email

    def search_courses(self, cursor):
        # Query the COURSE table directly for Fall 2026 offerings, sorted for readability.
        cursor.execute(
            "SELECT * FROM COURSE WHERE SEMESTER = 'Fall' AND YEAR = 2026 ORDER BY DEPT, TIME"
        )
        rows = cursor.fetchall()
        print("\n--- All Courses (Fall 2026) ---")
        if not rows:
            print("  No courses found.")
            return
        for row in rows:
            row_to_course(row).print_info()

    def search_courses_by_parameter(self, cursor, parameter, value):
        # Whitelist valid column names so that no user-supplied string can be
        # interpolated into the query as raw SQL — prevents injection entirely.
        allowed_columns = {"CRN", "TITLE", "DEPT", "TIME", "DAYS",
                           "SEMESTER", "YEAR", "CREDITS"}
        col = parameter.strip().upper()
        if col not in allowed_columns:
            print(f"  Cannot search by '{parameter}'. "
                  f"Allowed columns: {', '.join(sorted(allowed_columns))}")
            return

        # TITLE uses LIKE so a partial keyword (e.g. 'Calc') matches all Calculus courses.
        # All other columns use exact equality.
        if col == "TITLE":
            cursor.execute("SELECT * FROM COURSE WHERE TITLE LIKE ?", (f"%{value}%",))
        else:
            cursor.execute(f"SELECT * FROM COURSE WHERE {col} = ?", (value,))

        rows = cursor.fetchall()
        print(f"\n--- Courses where {col} = '{value}' ---")
        if not rows:
            print("  No matching courses found.")
            return
        for row in rows:
            row_to_course(row).print_info()

    def add_course(self, cursor, crn):
        # Step 1: confirm the course exists and retrieve its title and seat limit.
        cursor.execute("SELECT TITLE, CAPACITY FROM COURSE WHERE CRN = ?", (crn,))
        row = cursor.fetchone()
        if not row:
            print(f"  No course found with CRN {crn}.")
            return
        title, capacity = row

        # Step 2: prevent double-enrollment by checking ENROLLMENT for this student+CRN pair.
        cursor.execute(
            "SELECT 1 FROM ENROLLMENT WHERE STUDENT_ID = ? AND CRN = ?",
            (self.user_id, crn)
        )
        if cursor.fetchone():
            print(f"  You are already enrolled in {title} (CRN {crn}).")
            return

        # Step 3: enforce the seat cap — count existing enrollments and compare to CAPACITY.
        cursor.execute("SELECT COUNT(*) FROM ENROLLMENT WHERE CRN = ?", (crn,))
        enrolled = cursor.fetchone()[0]
        if enrolled >= capacity:
            print(f"  {title} (CRN {crn}) is full ({enrolled}/{capacity} seats taken).")
            return

        # Step 4: all checks passed — insert the enrollment row and commit to the database.
        cursor.execute(
            "INSERT INTO ENROLLMENT (STUDENT_ID, CRN) VALUES (?, ?)",
            (self.user_id, crn)
        )
        cursor.connection.commit()
        print(f"  Enrolled in {title} (CRN {crn}). "
              f"Seats remaining: {capacity - enrolled - 1}")

    def drop_course(self, cursor, crn):
        # Verify this student is actually enrolled before attempting a delete.
        cursor.execute(
            "SELECT 1 FROM ENROLLMENT WHERE STUDENT_ID = ? AND CRN = ?",
            (self.user_id, crn)
        )
        if not cursor.fetchone():
            print(f"  You are not enrolled in CRN {crn}.")
            return

        # Fetch the course title so the confirmation message is human-readable.
        cursor.execute("SELECT TITLE FROM COURSE WHERE CRN = ?", (crn,))
        title_row = cursor.fetchone()
        title = title_row[0] if title_row else f"CRN {crn}"

        # Remove the enrollment row and persist the change.
        cursor.execute(
            "DELETE FROM ENROLLMENT WHERE STUDENT_ID = ? AND CRN = ?",
            (self.user_id, crn)
        )
        cursor.connection.commit()
        print(f"  Dropped {title} (CRN {crn}) from your schedule.")

    def check_conflicts(self, cursor):
        # Fetch every course this student is enrolled in, with the fields needed for comparison.
        cursor.execute("""
            SELECT C.CRN, C.TITLE, C.DAYS, C.TIME
            FROM ENROLLMENT E
            JOIN COURSE C ON E.CRN = C.CRN
            WHERE E.STUDENT_ID = ?
        """, (self.user_id,))
        courses = cursor.fetchall()

        if not courses:
            print("  Your schedule is empty — no conflicts possible.")
            return

        def days_to_set(days_str):
            # "TTH" is stored as a single token, not individual characters, so it must be
            # handled before the character-split path to avoid {"T","H"} vs {"TU","TH"} mismatch.
            if days_str.upper() == "TTH":
                return {"TU", "TH"}              # Tuesday and Thursday as two-char tokens
            return {c.upper() for c in days_str}  # "MWF" -> {"M", "W", "F"}

        # Compare every distinct pair of courses: a conflict is a shared meeting day
        # AND the same start time (the scheduling system uses 1-hour fixed slots).
        conflicts = []
        for i in range(len(courses)):
            for j in range(i + 1, len(courses)):
                crn_a, title_a, days_a, time_a = courses[i]
                crn_b, title_b, days_b, time_b = courses[j]
                shared_days = days_to_set(days_a) & days_to_set(days_b)
                if shared_days and time_a == time_b:
                    conflicts.append(
                        (title_a, crn_a, title_b, crn_b, time_a,
                         "/".join(sorted(shared_days)))
                    )

        if conflicts:
            print("\n*** SCHEDULE CONFLICTS DETECTED ***")
            for title_a, crn_a, title_b, crn_b, time, days in conflicts:
                print(f"  Conflict: {title_a} (CRN {crn_a}) and {title_b} (CRN {crn_b}) "
                      f"both meet at {time} on {days}")
        else:
            print("  No conflicts found in your schedule.")

    def print_schedule(self, cursor):
        print(f"\n--- Schedule for {self.first_name} {self.last_name} (ID: {self.user_id}) ---")
        # Join ENROLLMENT with COURSE to get full course details for every enrolled CRN.
        # ORDER BY DAYS then TIME so the output reads like a weekly calendar.
        cursor.execute("""
            SELECT C.CRN, C.TITLE, C.DEPT, C.TIME, C.DAYS,
                   C.SEMESTER, C.YEAR, C.CREDITS, C.CAPACITY
            FROM ENROLLMENT E
            JOIN COURSE C ON E.CRN = C.CRN
            WHERE E.STUDENT_ID = ?
            ORDER BY C.DAYS, C.TIME
        """, (self.user_id,))
        rows = cursor.fetchall()
        if not rows:
            print("  No courses enrolled.")
            return
        total_credits = 0
        for row in rows:
            c = row_to_course(row)
            c.print_info()
            total_credits += c.credits
        print(f"\n  Total Credits: {total_credits}")

    def print_info(self):
        print(f"[Student] ID: {self.user_id} | {self.first_name} {self.last_name} | Major: {self.major} | Grad: {self.grad_year} | Email: {self.email}")


class Instructor(User):

    def __init__(self):
        super().__init__()
        self.title = ""
        self.hire_year = 0
        self.department = ""
        self.email = ""
        # No in-memory course/roster lists — all data lives in the database now.

    def set_title(self, title):
        self.title = title

    def set_hire_year(self, year):
        self.hire_year = year

    def set_department(self, dept):
        self.department = dept

    def set_email(self, email):
        self.email = email

    def search_courses(self, cursor):
        # Show every course in the system, sorted the same way as the Student view
        # so both roles see a consistent listing.
        cursor.execute(
            "SELECT * FROM COURSE WHERE SEMESTER = 'Fall' AND YEAR = 2026 ORDER BY DEPT, TIME"
        )
        rows = cursor.fetchall()
        print("\n--- All Courses (Fall 2026) ---")
        if not rows:
            print("  No courses found.")
            return
        for row in rows:
            row_to_course(row).print_info()

    def search_courses_by_parameter(self, cursor, parameter, value):
        # Same injection-safe whitelist pattern used in Student — only known column
        # names are ever interpolated into the query string.
        allowed_columns = {"CRN", "TITLE", "DEPT", "TIME", "DAYS",
                           "SEMESTER", "YEAR", "CREDITS"}
        col = parameter.strip().upper()
        if col not in allowed_columns:
            print(f"  Cannot search by '{parameter}'. "
                  f"Allowed columns: {', '.join(sorted(allowed_columns))}")
            return
        if col == "TITLE":
            cursor.execute("SELECT * FROM COURSE WHERE TITLE LIKE ?", (f"%{value}%",))
        else:
            cursor.execute(f"SELECT * FROM COURSE WHERE {col} = ?", (value,))
        rows = cursor.fetchall()
        print(f"\n--- Courses where {col} = '{value}' ---")
        if not rows:
            print("  No matching courses found.")
            return
        for row in rows:
            row_to_course(row).print_info()

    def print_schedule(self, cursor):
        print(f"\n--- Teaching Schedule for {self.first_name} {self.last_name} (ID: {self.user_id}) ---")
        # SELECT C.* pulls every column from COURSE — if new columns are added to
        # COURSE later, this query picks them up automatically without code changes.
        cursor.execute("""
            SELECT C.*
            FROM INSTRUCTOR_COURSE IC
            JOIN COURSE C ON IC.CRN = C.CRN
            WHERE IC.INSTRUCTOR_ID = ?
            ORDER BY C.DAYS, C.TIME
        """, (self.user_id,))
        rows = cursor.fetchall()
        if not rows:
            print("  No courses assigned to your account yet.")
            return
        for row in rows:
            row_to_course(row).print_info()

    def print_class_list(self, cursor, crn):
        # Look up the course title first so the header is human-readable.
        cursor.execute("SELECT TITLE FROM COURSE WHERE CRN = ?", (crn,))
        title_row = cursor.fetchone()
        title = title_row[0] if title_row else f"CRN {crn}"
        print(f"\n--- Class List: {title} (CRN {crn}) ---")
        # Join ENROLLMENT with STUDENT to get full student details for each enrolled seat.
        cursor.execute("""
            SELECT S.*
            FROM ENROLLMENT E
            JOIN STUDENT S ON E.STUDENT_ID = S.ID
            WHERE E.CRN = ?
            ORDER BY S.SURNAME, S.NAME
        """, (crn,))
        rows = cursor.fetchall()
        if not rows:
            print("  No students enrolled.")
            return
        for row in rows:
            row_to_student(row).print_info()

    def search_roster(self, cursor, crn, student_id):
        # A simple point-lookup: is this student_id present in ENROLLMENT for this CRN?
        cursor.execute(
            "SELECT 1 FROM ENROLLMENT WHERE CRN = ? AND STUDENT_ID = ?",
            (crn, student_id)
        )
        if cursor.fetchone():
            # Fetch the name to make the confirmation message more useful.
            cursor.execute("SELECT NAME, SURNAME FROM STUDENT WHERE ID = ?", (student_id,))
            name_row = cursor.fetchone()
            name = f"{name_row[0]} {name_row[1]}" if name_row else f"ID {student_id}"
            print(f"  {name} (ID {student_id}) IS enrolled in CRN {crn}.")
        else:
            print(f"  Student ID {student_id} is NOT enrolled in CRN {crn}.")

    def print_info(self):
        print(f"[Instructor] ID: {self.user_id} | {self.first_name} {self.last_name} | {self.title} | Dept: {self.department} | Hired: {self.hire_year} | Email: {self.email}")


class Admin(User):

    def __init__(self):
        super().__init__()
        self.title = ""
        self.office = ""
        self.email = ""
        # No in-memory lists — all course and user data lives in the database now.

    def set_title(self, title):
        self.title = title

    def set_office(self, office):
        self.office = office

    def set_email(self, email):
        self.email = email

    def add_course(self, cursor, course_data):
        # course_data must be a 9-tuple matching the COURSE column order:
        # (CRN, TITLE, DEPT, TIME, DAYS, SEMESTER, YEAR, CREDITS, CAPACITY)
        try:
            cursor.execute(
                "INSERT INTO COURSE VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", course_data
            )
            cursor.connection.commit()
            print(f"  Course '{course_data[1]}' (CRN {course_data[0]}) added to the system.")
        except sqlite3.IntegrityError:
            print(f"  CRN {course_data[0]} already exists — no changes made.")

    def remove_course(self, cursor, crn):
        # Confirm the course exists before deleting so we can print its name.
        cursor.execute("SELECT TITLE FROM COURSE WHERE CRN = ?", (crn,))
        row = cursor.fetchone()
        if not row:
            print(f"  No course found with CRN {crn}.")
            return
        cursor.execute("DELETE FROM COURSE WHERE CRN = ?", (crn,))
        cursor.connection.commit()
        print(f"  Course '{row[0]}' (CRN {crn}) removed from the system.")

    def add_user(self, cursor, role, user_data):
        # role is 'student', 'instructor', or 'admin' — it controls which table
        # receives the row and what column layout user_data must have:
        #   student    → (id, first, last, grad_year, major, email)
        #   instructor → (id, first, last, title, hire_year, dept, email)
        #   admin      → (id, first, last, title, office, email)
        role = role.lower()
        try:
            if role == "student":
                cursor.execute("INSERT INTO STUDENT VALUES (?, ?, ?, ?, ?, ?)", user_data)
            elif role == "instructor":
                cursor.execute("INSERT INTO INSTRUCTOR VALUES (?, ?, ?, ?, ?, ?, ?)", user_data)
            elif role == "admin":
                cursor.execute("INSERT INTO ADMIN VALUES (?, ?, ?, ?, ?, ?)", user_data)
            else:
                print(f"  Unknown role '{role}'. Must be student, instructor, or admin.")
                return

            # Derive the initial password from the email (everything before the '@'),
            # then insert a matching LOGIN row so the new person can actually sign in.
            user_id = user_data[0]
            email = user_data[-1]
            password = email.split("@")[0]
            cursor.execute(
                "INSERT INTO LOGIN VALUES (?, ?, ?)", (user_id, password, role)
            )
            cursor.connection.commit()
            print(f"  {role.capitalize()} ID {user_id} added. Login password: '{password}'.")
        except sqlite3.IntegrityError:
            print(f"  ID {user_data[0]} already exists — no changes made.")

    def remove_user(self, cursor, role, user_id):
        # Map role strings to table names so we can target the right table dynamically.
        role = role.lower()
        table_map = {"student": "STUDENT", "instructor": "INSTRUCTOR", "admin": "ADMIN"}
        if role not in table_map:
            print(f"  Unknown role '{role}'. Must be student, instructor, or admin.")
            return
        table = table_map[role]
        # Make sure the user actually exists before attempting the delete.
        cursor.execute(f"SELECT ID FROM {table} WHERE ID = ?", (user_id,))
        if not cursor.fetchone():
            print(f"  No {role} found with ID {user_id}.")
            return
        # Delete from the role table first, then clean up their LOGIN entry.
        cursor.execute(f"DELETE FROM {table} WHERE ID = ?", (user_id,))
        cursor.execute("DELETE FROM LOGIN WHERE USER_ID = ?", (user_id,))
        cursor.connection.commit()
        print(f"  {role.capitalize()} ID {user_id} and their login have been removed.")

    def add_student_to_course(self, cursor, student_id, crn):
        # Validate that both the student and course exist before doing anything.
        cursor.execute("SELECT 1 FROM STUDENT WHERE ID = ?", (student_id,))
        if not cursor.fetchone():
            print(f"  Student ID {student_id} not found.")
            return
        cursor.execute("SELECT TITLE, CAPACITY FROM COURSE WHERE CRN = ?", (crn,))
        row = cursor.fetchone()
        if not row:
            print(f"  No course found with CRN {crn}.")
            return
        title, capacity = row
        # Prevent double-enrollment.
        cursor.execute(
            "SELECT 1 FROM ENROLLMENT WHERE STUDENT_ID = ? AND CRN = ?", (student_id, crn)
        )
        if cursor.fetchone():
            print(f"  Student {student_id} is already enrolled in {title} (CRN {crn}).")
            return
        # Respect the course seat cap.
        cursor.execute("SELECT COUNT(*) FROM ENROLLMENT WHERE CRN = ?", (crn,))
        enrolled = cursor.fetchone()[0]
        if enrolled >= capacity:
            print(f"  {title} (CRN {crn}) is full ({enrolled}/{capacity} seats taken).")
            return
        cursor.execute(
            "INSERT INTO ENROLLMENT (STUDENT_ID, CRN) VALUES (?, ?)", (student_id, crn)
        )
        cursor.connection.commit()
        print(f"  Student {student_id} enrolled in {title} (CRN {crn}).")

    def remove_student_from_course(self, cursor, student_id, crn):
        # Confirm the enrollment row exists before deleting it.
        cursor.execute(
            "SELECT 1 FROM ENROLLMENT WHERE STUDENT_ID = ? AND CRN = ?", (student_id, crn)
        )
        if not cursor.fetchone():
            print(f"  Student {student_id} is not enrolled in CRN {crn}.")
            return
        cursor.execute(
            "DELETE FROM ENROLLMENT WHERE STUDENT_ID = ? AND CRN = ?", (student_id, crn)
        )
        cursor.connection.commit()
        print(f"  Student {student_id} removed from CRN {crn}.")

    def add_instructor_to_course(self, cursor, instructor_id, crn):
        # Validate that both the instructor and course exist first.
        cursor.execute("SELECT 1 FROM INSTRUCTOR WHERE ID = ?", (instructor_id,))
        if not cursor.fetchone():
            print(f"  Instructor ID {instructor_id} not found.")
            return
        cursor.execute("SELECT TITLE FROM COURSE WHERE CRN = ?", (crn,))
        row = cursor.fetchone()
        if not row:
            print(f"  No course found with CRN {crn}.")
            return
        course_title = row[0]
        # Prevent duplicate assignments.
        cursor.execute(
            "SELECT 1 FROM INSTRUCTOR_COURSE WHERE INSTRUCTOR_ID = ? AND CRN = ?",
            (instructor_id, crn)
        )
        if cursor.fetchone():
            print(f"  Instructor {instructor_id} is already assigned to {course_title} (CRN {crn}).")
            return
        cursor.execute(
            "INSERT INTO INSTRUCTOR_COURSE (INSTRUCTOR_ID, CRN) VALUES (?, ?)",
            (instructor_id, crn)
        )
        cursor.connection.commit()
        print(f"  Instructor {instructor_id} assigned to {course_title} (CRN {crn}).")

    def remove_instructor_from_course(self, cursor, instructor_id, crn):
        cursor.execute(
            "SELECT 1 FROM INSTRUCTOR_COURSE WHERE INSTRUCTOR_ID = ? AND CRN = ?",
            (instructor_id, crn)
        )
        if not cursor.fetchone():
            print(f"  Instructor {instructor_id} is not assigned to CRN {crn}.")
            return
        cursor.execute(
            "DELETE FROM INSTRUCTOR_COURSE WHERE INSTRUCTOR_ID = ? AND CRN = ?",
            (instructor_id, crn)
        )
        cursor.connection.commit()
        print(f"  Instructor {instructor_id} removed from CRN {crn}.")

    def search_courses(self, cursor):
        # Admin sees all courses regardless of semester, sorted for easy scanning.
        cursor.execute("SELECT * FROM COURSE ORDER BY DEPT, YEAR, SEMESTER, TIME")
        rows = cursor.fetchall()
        print("\n--- All Courses ---")
        if not rows:
            print("  No courses found.")
            return
        for row in rows:
            row_to_course(row).print_info()

    def print_roster(self, cursor, crn):
        # Same join pattern as Instructor.print_class_list — just a different entry point.
        cursor.execute("SELECT TITLE FROM COURSE WHERE CRN = ?", (crn,))
        title_row = cursor.fetchone()
        title = title_row[0] if title_row else f"CRN {crn}"
        print(f"\n--- Roster: {title} (CRN {crn}) ---")
        cursor.execute("""
            SELECT S.*
            FROM ENROLLMENT E
            JOIN STUDENT S ON E.STUDENT_ID = S.ID
            WHERE E.CRN = ?
            ORDER BY S.SURNAME, S.NAME
        """, (crn,))
        rows = cursor.fetchall()
        if not rows:
            print("  No students enrolled.")
            return
        for row in rows:
            row_to_student(row).print_info()

    def print_info(self):
        print(f"[Admin] ID: {self.user_id} | {self.first_name} {self.last_name} | {self.title} | Office: {self.office} | Email: {self.email}")


class Course:

    def __init__(self):
        self.crn = 0
        self.title = ""
        self.department = ""
        self.time = ""
        self.days = ""
        self.semester = ""
        self.year = 0
        self.credits = 0
        self.capacity = 0
        self.enrolled = []

    def set_crn(self, crn):
        self.crn = crn

    def set_title(self, title):
        self.title = title

    def set_department(self, dept):
        self.department = dept

    def set_time(self, time):
        self.time = time

    def set_days(self, days):
        self.days = days

    def set_semester(self, semester):
        self.semester = semester

    def set_year(self, year):
        self.year = year

    def set_credits(self, credits):
        self.credits = credits

    def set_capacity(self, capacity):
        self.capacity = capacity

    def is_full(self):
        return len(self.enrolled) >= self.capacity

    def enroll(self, student_id):
        if not self.is_full() and student_id not in self.enrolled:
            self.enrolled.append(student_id)
            return True
        return False

    def drop(self, student_id):
        if student_id in self.enrolled:
            self.enrolled.remove(student_id)
            return True
        return False

    def print_info(self):
        print(f"[Course] CRN: {self.crn} | {self.title} | Dept: {self.department} | {self.days} {self.time} | {self.semester} {self.year} | {self.credits} credits | Capacity: {self.capacity}")


# HELPER FUNCTIONS
# Convert raw database rows (tuples) into class objects so we can use print_info()

def row_to_student(row):
    s = Student()
    s.set_id(row[0]); s.set_first_name(row[1]); s.set_last_name(row[2])
    s.set_grad_year(row[3]); s.set_major(row[4]); s.set_email(row[5])
    return s

def row_to_instructor(row):
    i = Instructor()
    i.set_id(row[0]); i.set_first_name(row[1]); i.set_last_name(row[2])
    i.set_title(row[3]); i.set_hire_year(row[4]); i.set_department(row[5]); i.set_email(row[6])
    return i

def row_to_admin(row):
    a = Admin()
    a.set_id(row[0]); a.set_first_name(row[1]); a.set_last_name(row[2])
    a.set_title(row[3]); a.set_office(row[4]); a.set_email(row[5])
    return a

def row_to_course(row):
    c = Course()
    c.set_crn(row[0]); c.set_title(row[1]); c.set_department(row[2])
    c.set_time(row[3]); c.set_days(row[4]); c.set_semester(row[5])
    c.set_year(row[6]); c.set_credits(row[7]); c.set_capacity(row[8])
    return c


# Nia - database setup and operations

# SETUP
# Runs automatically when the program starts
# Creates the COURSE table, adds students, removes Fourier, updates Vera Rubin

def setup(cursor, database):

    # Create all tables if they don't already exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS STUDENT (
        ID INT PRIMARY KEY NOT NULL,
        NAME TEXT NOT NULL,
        SURNAME TEXT NOT NULL,
        GRADYEAR INT NOT NULL,
        MAJOR CHAR(4) NOT NULL,
        EMAIL TEXT NOT NULL
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS INSTRUCTOR (
        ID INT PRIMARY KEY NOT NULL,
        NAME TEXT NOT NULL,
        SURNAME TEXT NOT NULL,
        TITLE TEXT NOT NULL,
        HIREYEAR INT NOT NULL,
        DEPT CHAR(4) NOT NULL,
        EMAIL TEXT NOT NULL
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS ADMIN (
        ID INT PRIMARY KEY NOT NULL,
        NAME TEXT NOT NULL,
        SURNAME TEXT NOT NULL,
        TITLE TEXT NOT NULL,
        OFFICE TEXT NOT NULL,
        EMAIL TEXT NOT NULL
    )""")

    # Create COURSE table if it doesn't already exist
    sql_command = """CREATE TABLE IF NOT EXISTS COURSE (
        CRN INTEGER PRIMARY KEY NOT NULL,
        TITLE TEXT NOT NULL,
        DEPT TEXT NOT NULL,
        TIME TEXT NOT NULL,
        DAYS TEXT NOT NULL,
        SEMESTER TEXT NOT NULL,
        YEAR INTEGER NOT NULL,
        CREDITS INTEGER NOT NULL,
        CAPACITY INTEGER
    )"""
    cursor.execute(sql_command)

    # "CREATE TABLE IF NOT EXISTS" only uses the column list above the very
    # first time COURSE is ever created. If COURSE already existed in the
    # database file from before we added CAPACITY, the line above does
    # nothing - SQLite sees the table is already there and skips it. So we
    # double check here: does COURSE already have a CAPACITY column? PRAGMA
    # table_info gives us back the list of every column currently in the
    # table, and we look for "CAPACITY" in that list.
    cursor.execute("PRAGMA table_info(COURSE)")
    existing_columns = [column[1] for column in cursor.fetchall()]
    if "CAPACITY" not in existing_columns:
        cursor.execute("ALTER TABLE COURSE ADD COLUMN CAPACITY INTEGER")

    # Create LOGIN table if it doesn't already exist.
    # USER_ID matches the ID column in STUDENT, INSTRUCTOR, or ADMIN -
    # whichever table that person belongs to.
    # The CHECK constraint tells SQLite to refuse any row where ROLE isn't
    # exactly "student", "instructor", or "admin" - it's a safety net that
    # catches typos before bad data ever gets saved.
    cursor.execute("""CREATE TABLE IF NOT EXISTS LOGIN (
        USER_ID INTEGER PRIMARY KEY NOT NULL,
        PASSWORD TEXT NOT NULL,
        ROLE TEXT NOT NULL CHECK (ROLE IN ('student', 'instructor', 'admin'))
    )""")

    # ENROLLMENT tracks which student is registered in which course (many-to-many).
    # IF NOT EXISTS means this is safe to call on every startup, and also safe if
    # another team member already created the table in a previous run.
    cursor.execute("""CREATE TABLE IF NOT EXISTS ENROLLMENT (
        STUDENT_ID INTEGER NOT NULL,
        CRN        INTEGER NOT NULL,
        PRIMARY KEY (STUDENT_ID, CRN),
        FOREIGN KEY (STUDENT_ID) REFERENCES STUDENT(ID),
        FOREIGN KEY (CRN)        REFERENCES COURSE(CRN)
    )""")

    # INSTRUCTOR_COURSE tracks which instructor is assigned to teach which course
    # (also many-to-many — one course can have multiple instructors, one instructor
    # can teach multiple courses). IF NOT EXISTS keeps this idempotent on every run.
    cursor.execute("""CREATE TABLE IF NOT EXISTS INSTRUCTOR_COURSE (
        INSTRUCTOR_ID INTEGER NOT NULL,
        CRN           INTEGER NOT NULL,
        PRIMARY KEY (INSTRUCTOR_ID, CRN),
        FOREIGN KEY (INSTRUCTOR_ID) REFERENCES INSTRUCTOR(ID),
        FOREIGN KEY (CRN)           REFERENCES COURSE(CRN)
    )""")

    # Add 2 students - wrapped in try/except in case they already exist
    try:
        sql_command = "INSERT INTO STUDENT VALUES (10011, 'Shubaan', 'Meyyappan', 2026, 'BSCO', 'meyyappans')"
        cursor.execute(sql_command)
        sql_command = "INSERT INTO STUDENT VALUES (10012, 'Nia', 'Kochadze', 2027, 'BSCO', 'kochadzen')"
        cursor.execute(sql_command)
    except sqlite3.IntegrityError:
        pass

    # Remove Fourier - target by ID so we don't accidentally delete anyone else
    try:
        sql_command = "DELETE FROM INSTRUCTOR WHERE ID = 20001"
        cursor.execute(sql_command)
    except:
        pass

    # Update Vera Rubin's title to Vice-President
    sql_command = "UPDATE ADMIN SET TITLE = 'Vice-President' WHERE SURNAME = 'Rubin'"
    cursor.execute(sql_command)

    # Insert 5 courses - wrapped in try/except in case they already exist
    try:
        cursor.execute("INSERT INTO COURSE VALUES (40001, 'Applied Programming Concepts', 'BSCO', '9:00AM', 'MWF', 'Fall', 2026, 3, 30)")
        cursor.execute("INSERT INTO COURSE VALUES (40002, 'Circuits I', 'BSEE', '11:00AM', 'TTH', 'Fall', 2026, 4, 28)")
        cursor.execute("INSERT INTO COURSE VALUES (40003, 'Statics', 'BSME', '1:00PM', 'MWF', 'Fall', 2026, 3, 30)")
        cursor.execute("INSERT INTO COURSE VALUES (40004, 'Calculus III', 'BSAS', '10:00AM', 'TTH', 'Fall', 2026, 4, 35)")
        cursor.execute("INSERT INTO COURSE VALUES (40005, 'Data Structures', 'BCOS', '2:00PM', 'MWF', 'Fall', 2026, 3, 30)")
    except sqlite3.IntegrityError:
        pass

    # Save all setup changes to the database file
    database.commit()
    print("Database ready.\n")


# Assignment 5 additions - realistic sample data and login system

# SEED USERS AND COURSES
# Loads a realistic set of students, instructors, courses, and admins into
# the database. Several students share the same MAJOR and several courses
# share the same DEPT on purpose, so functions like match_courses() (and any
# future roster/conflict-checking code) have real overlapping data to use.
# This is safe to call every time the program starts: each insert is wrapped
# in try/except, so if a row with that ID/CRN is already there from a
# previous run, we just skip it instead of crashing.

def seed_users_and_courses(cursor, database):

    students = [
        (11001, "Olivia", "Martinez", 2026, "BSCO", "omartinez@university.edu"),
        (11002, "Liam", "Chen", 2027, "BSEE", "lchen@university.edu"),
        (11003, "Emma", "Johnson", 2026, "BSCO", "ejohnson@university.edu"),
        (11004, "Noah", "Williams", 2028, "BSME", "nwilliams@university.edu"),
        (11005, "Ava", "Thompson", 2027, "BSAS", "athompson@university.edu"),
        (11006, "Ethan", "Davis", 2026, "BSCO", "edavis@university.edu"),
        (11007, "Sophia", "Patel", 2029, "BSCE", "spatel@university.edu"),
        (11008, "Mason", "Rodriguez", 2027, "BSEE", "mrodriguez@university.edu"),
        (11009, "Isabella", "Kim", 2026, "BSCO", "ikim@university.edu"),
        (11010, "Lucas", "Nguyen", 2028, "BSME", "lnguyen@university.edu"),
        (11011, "Mia", "Anderson", 2027, "BSAS", "manderson@university.edu"),
        (11012, "Benjamin", "Carter", 2026, "BSCO", "bcarter@university.edu"),
        (11013, "Charlotte", "Wright", 2029, "BSCE", "cwright@university.edu"),
        (11014, "Henry", "Lopez", 2027, "BSEE", "hlopez@university.edu"),
        (11015, "Amelia", "Scott", 2026, "BSCO", "ascott@university.edu"),
        (11016, "Jacob", "Murphy", 2028, "BSME", "jmurphy@university.edu"),
        (11017, "Harper", "Collins", 2027, "BSAS", "hcollins@university.edu"),
        (11018, "Daniel", "Mitchell", 2026, "BSCO", "dmitchell@university.edu"),
        (11019, "Grace", "Bennett", 2029, "BSCE", "gbennett@university.edu"),
        (11020, "Samuel", "Reed", 2027, "BSEE", "sreed@university.edu"),
    ]

    instructors = [
        (21001, "Robert", "Hayes", "Professor", 2005, "BSCO", "rhayes@university.edu"),
        (21002, "Linda", "Foster", "Associate Professor", 2010, "BSEE", "lfoster@university.edu"),
        (21003, "James", "Coleman", "Professor", 1998, "BSME", "jcoleman@university.edu"),
        (21004, "Susan", "Brooks", "Assistant Professor", 2015, "BSAS", "sbrooks@university.edu"),
        (21005, "Michael", "Turner", "Professor", 2008, "BSCO", "mturner@university.edu"),
        (21006, "Karen", "Hughes", "Associate Professor", 2012, "BSCE", "khughes@university.edu"),
        (21007, "David", "Powell", "Professor", 2001, "BSEE", "dpowell@university.edu"),
        (21008, "Nancy", "Ortiz", "Assistant Professor", 2018, "BSCO", "nortiz@university.edu"),
        (21009, "William", "Bishop", "Professor", 2003, "BSME", "wbishop@university.edu"),
        (21010, "Patricia", "Long", "Associate Professor", 2011, "BSAS", "plong@university.edu"),
        (21011, "Christopher", "Reyes", "Professor", 2006, "BSCE", "creyes@university.edu"),
        (21012, "Barbara", "Simmons", "Assistant Professor", 2019, "BSEE", "bsimmons@university.edu"),
        (21013, "Joseph", "Fisher", "Professor", 2000, "BSCO", "jfisher@university.edu"),
        (21014, "Margaret", "Wells", "Associate Professor", 2014, "BSME", "mwells@university.edu"),
        (21015, "Thomas", "Hart", "Professor", 2009, "BSAS", "thart@university.edu"),
    ]

    courses = [
        (41001, "Intro to Programming", "BSCO", "9:00AM", "MWF", "Fall", 2026, 3, 35),
        (41002, "Data Structures II", "BSCO", "11:00AM", "MWF", "Fall", 2026, 3, 30),
        (41003, "Database Systems", "BSCO", "1:00PM", "TTH", "Fall", 2026, 3, 28),
        (41004, "Operating Systems", "BSCO", "10:00AM", "TTH", "Spring", 2027, 4, 25),
        (41005, "Circuits II", "BSEE", "9:00AM", "TTH", "Fall", 2026, 4, 30),
        (41006, "Digital Logic Design", "BSEE", "2:00PM", "MWF", "Fall", 2026, 3, 32),
        (41007, "Signals and Systems", "BSEE", "11:00AM", "TTH", "Spring", 2027, 4, 27),
        (41008, "Thermodynamics", "BSME", "1:00PM", "MWF", "Fall", 2026, 3, 30),
        (41009, "Fluid Mechanics", "BSME", "9:00AM", "TTH", "Fall", 2026, 4, 28),
        (41010, "Machine Design", "BSME", "3:00PM", "MWF", "Spring", 2027, 3, 25),
        (41011, "Calculus III", "BSAS", "10:00AM", "TTH", "Fall", 2026, 4, 40),
        (41012, "Linear Algebra", "BSAS", "9:00AM", "MWF", "Fall", 2026, 3, 35),
        (41013, "Differential Equations", "BSAS", "1:00PM", "TTH", "Spring", 2027, 4, 30),
        (41014, "Structural Analysis", "BSCE", "11:00AM", "MWF", "Fall", 2026, 3, 28),
        (41015, "Soil Mechanics", "BSCE", "2:00PM", "TTH", "Fall", 2026, 3, 26),
        (41016, "Surveying", "BSCE", "10:00AM", "MWF", "Spring", 2027, 3, 24),
        (41017, "Algorithms", "BSCO", "3:00PM", "TTH", "Spring", 2027, 3, 30),
        (41018, "Computer Networks", "BSCO", "12:00PM", "MWF", "Fall", 2026, 3, 32),
        (41019, "Power Systems", "BSEE", "1:00PM", "TTH", "Fall", 2026, 4, 28),
        (41020, "Environmental Engineering", "BSCE", "9:00AM", "MWF", "Spring", 2027, 3, 26),
    ]

    admins = [
        (31001, "Patricia", "Nolan", "Registrar", "Admin Building 101", "pnolan@university.edu"),
        (31002, "George", "Whitfield", "Dean of Students", "Admin Building 205", "gwhitfield@university.edu"),
        (31003, "Rachel", "Dunn", "IT Director", "Tech Building 12", "rdunn@university.edu"),
    ]

    # Go through every row and try to insert it. The "?" placeholders are
    # filled in safely by sqlite3 - this is the same pattern the insert()
    # function below uses, so typed-in values (or in this case, our own
    # data) can never be misread as SQL commands.
    for s in students:
        try:
            cursor.execute("INSERT INTO STUDENT VALUES (?, ?, ?, ?, ?, ?)", s)
        except sqlite3.IntegrityError:
            pass  # this student ID is already in the table

    for i in instructors:
        try:
            cursor.execute("INSERT INTO INSTRUCTOR VALUES (?, ?, ?, ?, ?, ?, ?)", i)
        except sqlite3.IntegrityError:
            pass

    for c in courses:
        try:
            cursor.execute("INSERT INTO COURSE VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", c)
        except sqlite3.IntegrityError:
            pass

    for a in admins:
        try:
            cursor.execute("INSERT INTO ADMIN VALUES (?, ?, ?, ?, ?, ?)", a)
        except sqlite3.IntegrityError:
            pass

    database.commit()
    print("Realistic sample data loaded (or already present).\n")


# SEED LOGIN TABLE
# Builds one LOGIN row for every person already sitting in STUDENT,
# INSTRUCTOR, or ADMIN. The password is just whatever comes before the "@"
# in that person's email - so "omartinez@university.edu" gets the password
# "omartinez". We read the email back out of the database (instead of
# retyping it here) so the LOGIN table can never drift out of sync with
# the real email addresses stored elsewhere.

def seed_login_table(cursor, database):

    role_tables = [
        ("STUDENT", "student"),
        ("INSTRUCTOR", "instructor"),
        ("ADMIN", "admin"),
    ]

    for table_name, role in role_tables:
        cursor.execute(f"SELECT ID, EMAIL FROM {table_name}")
        for user_id, email in cursor.fetchall():
            password = email.split("@")[0]
            try:
                cursor.execute("INSERT INTO LOGIN VALUES (?, ?, ?)", (user_id, password, role))
            except sqlite3.IntegrityError:
                pass  # this person already has a LOGIN row

    database.commit()
    print("Login accounts ready.\n")


# LOGIN / LOGOUT
# login() only ever asks for an email and a password - never a role. We
# figure out the role ourselves by checking which table (STUDENT,
# INSTRUCTOR, or ADMIN) the email actually belongs to, then confirming the
# password against the LOGIN table.

def login(cursor):
    max_attempts = 3

    for attempt in range(max_attempts):
        email = input("Email: ").strip()
        password = input("Password: ").strip()

        user_id = None
        role = None

        # Check STUDENT, then INSTRUCTOR, then ADMIN for a matching email,
        # and stop as soon as we find one - an email should only ever
        # belong to one person in one of these three tables.
        for table_name in ("STUDENT", "INSTRUCTOR", "ADMIN"):
            cursor.execute(f"SELECT ID FROM {table_name} WHERE EMAIL = ?", (email,))
            row = cursor.fetchone()
            if row:
                user_id = row[0]
                break

        # Now that we (maybe) know who this is, check the LOGIN table for
        # that exact USER_ID + PASSWORD combination. ROLE is read straight
        # from that matching row, since LOGIN is the single source of
        # truth for "who is allowed to log in, and as what."
        if user_id is not None:
            cursor.execute("SELECT ROLE FROM LOGIN WHERE USER_ID = ? AND PASSWORD = ?", (user_id, password))
            login_row = cursor.fetchone()
            if login_row:
                role = login_row[0]

        if role is not None:
            print(f"Welcome! You are logged in as {role}.")
            return role, user_id

        attempts_left = max_attempts - (attempt + 1)
        if attempts_left > 0:
            print(f"Invalid email or password. {attempts_left} attempt(s) left.")
        else:
            print("Too many failed login attempts. Exiting program.")

    # We used up every attempt without a match, so we return "nobody" -
    # (None, None) - and let main() decide to stop the program.
    return None, None


def logout():
    print("You have been logged out. Goodbye!")


# Dillon - menu and query functions

# PRINT ALL
# Prints every record in all four tables using class objects

def print_all(cursor):
    print("\nAll Students:")
    cursor.execute("SELECT * FROM STUDENT")
    for row in cursor.fetchall():
        row_to_student(row).print_info()

    print("\nAll Instructors:")
    cursor.execute("SELECT * FROM INSTRUCTOR")
    for row in cursor.fetchall():
        row_to_instructor(row).print_info()

    print("\nAll Admins:")
    cursor.execute("SELECT * FROM ADMIN")
    for row in cursor.fetchall():
        row_to_admin(row).print_info()

    print("\nAll Courses:")
    cursor.execute("SELECT * FROM COURSE")
    for row in cursor.fetchall():
        row_to_course(row).print_info()


# SEARCH
# Search by student last name, instructor department, or course department

def search(cursor):
    print("\nSearch by:")
    print("1. Student last name")
    print("2. Instructor department")
    print("3. Course department")
    choice = input("Choice: ").strip()

    if choice == "1":
        name = input("Last name: ").strip()
        cursor.execute("SELECT * FROM STUDENT WHERE SURNAME LIKE ?", (f"%{name}%",))
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                row_to_student(row).print_info()
        else:
            print("No students found.")

    elif choice == "2":
        dept = input("Department: ").strip().upper()
        cursor.execute("SELECT * FROM INSTRUCTOR WHERE DEPT = ?", (dept,))
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                row_to_instructor(row).print_info()
        else:
            print("No instructors found in that department.")

    elif choice == "3":
        dept = input("Department: ").strip().upper()
        cursor.execute("SELECT * FROM COURSE WHERE DEPT = ?", (dept,))
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                row_to_course(row).print_info()
        else:
            print("No courses found in that department.")


# INSERT
# Insert a new student or course into the database

def insert(cursor, database):
    print("\nInsert:")
    print("1. Student")
    print("2. Course")
    choice = input("Choice: ").strip()

    if choice == "1":
        uid = input("ID: ").strip()
        fname = input("First name: ").strip()
        lname = input("Last name: ").strip()
        grad = input("Grad year: ").strip()
        major = input("Major: ").strip()
        email = input("Email: ").strip()
        try:
            cursor.execute("INSERT INTO STUDENT VALUES (?, ?, ?, ?, ?, ?)", (uid, fname, lname, grad, major, email))
            database.commit()
            print("Student added.")
        except sqlite3.IntegrityError:
            print("ID already exists.")

    elif choice == "2":
        crn = input("CRN: ").strip()
        title = input("Title: ").strip()
        dept = input("Department: ").strip().upper()
        time = input("Time: ").strip()
        days = input("Days (e.g. MWF): ").strip()
        sem = input("Semester: ").strip()
        year = input("Year: ").strip()
        credits = input("Credits: ").strip()
        capacity = input("Capacity: ").strip()
        try:
            cursor.execute("INSERT INTO COURSE VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (crn, title, dept, time, days, sem, year, credits, capacity))
            database.commit()
            print("Course added.")
        except sqlite3.IntegrityError:
            print("CRN already exists.")


# UPDATE
# Update a student email, instructor title, or admin title

def update(cursor, database):
    print("\nUpdate:")
    print("1. Student email")
    print("2. Instructor title")
    print("3. Admin title")
    choice = input("Choice: ").strip()

    if choice == "1":
        uid = input("Student ID: ").strip()
        email = input("New email: ").strip()
        cursor.execute("UPDATE STUDENT SET EMAIL = ? WHERE ID = ?", (email, uid))
        database.commit()
        print("Student updated.")

    elif choice == "2":
        uid = input("Instructor ID: ").strip()
        title = input("New title: ").strip()
        cursor.execute("UPDATE INSTRUCTOR SET TITLE = ? WHERE ID = ?", (title, uid))
        database.commit()
        print("Instructor updated.")

    elif choice == "3":
        uid = input("Admin ID: ").strip()
        title = input("New title: ").strip()
        cursor.execute("UPDATE ADMIN SET TITLE = ? WHERE ID = ?", (title, uid))
        database.commit()
        print("Admin updated.")


# REMOVE
# Remove a student, instructor, or course from the database

def remove(cursor, database):
    print("\nRemove:")
    print("1. Student by ID")
    print("2. Instructor by ID")
    print("3. Course by CRN")
    choice = input("Choice: ").strip()

    if choice == "1":
        uid = input("Student ID: ").strip()
        cursor.execute("DELETE FROM STUDENT WHERE ID = ?", (uid,))
        database.commit()
        print("Student removed.")

    elif choice == "2":
        uid = input("Instructor ID: ").strip()
        cursor.execute("DELETE FROM INSTRUCTOR WHERE ID = ?", (uid,))
        database.commit()
        print("Instructor removed.")

    elif choice == "3":
        crn = input("Course CRN: ").strip()
        cursor.execute("DELETE FROM COURSE WHERE CRN = ?", (crn,))
        database.commit()
        print("Course removed.")


# MATCH COURSES TO INSTRUCTORS
# For each course, find an instructor in the same department
# If no match found, flag it

def match_courses(cursor):
    print("\nCourse to Instructor Matching:")
    cursor.execute("SELECT * FROM COURSE")
    courses = cursor.fetchall()

    for course_row in courses:
        course = row_to_course(course_row)
        print(f"\nCourse: {course.title} (Dept: {course.department})")

        # Second cursor so we don't interfere with the courses loop
        cursor2 = cursor.connection.cursor()
        cursor2.execute("SELECT * FROM INSTRUCTOR WHERE DEPT = ?", (course.department,))
        instructors = cursor2.fetchall()

        if instructors:
            for inst_row in instructors:
                inst = row_to_instructor(inst_row)
                print(f"  -> Can be taught by: {inst.first_name} {inst.last_name} ({inst.title})")
        else:
            print(f"  -> No matching instructor found for department: {course.department}")


# ROLE-SPECIFIC MENUS
# Each function below handles the interactive menu loop for one role.
# They receive the already-constructed user object (Student, Instructor, or Admin)
# and the database cursor, then loop until the user chooses to log out.

def student_menu(student, cursor):
    while True:
        print(f"\n=== Student Menu — {student.first_name} {student.last_name} ===")
        print("1. Browse all courses (Fall 2026)")
        print("2. Search courses by parameter")
        print("3. View my schedule")
        print("4. Add a course to my schedule")
        print("5. Drop a course from my schedule")
        print("6. Check my schedule for conflicts")
        print("0. Logout / Exit")

        choice = input("\nChoice: ").strip()

        if choice == "1":
            student.search_courses(cursor)
        elif choice == "2":
            param = input("Search by (e.g. DEPT, TITLE, CREDITS): ").strip()
            value = input("Value: ").strip()
            student.search_courses_by_parameter(cursor, param, value)
        elif choice == "3":
            student.print_schedule(cursor)
        elif choice == "4":
            crn = input("CRN to add: ").strip()
            student.add_course(cursor, int(crn))
        elif choice == "5":
            crn = input("CRN to drop: ").strip()
            student.drop_course(cursor, int(crn))
        elif choice == "6":
            student.check_conflicts(cursor)
        elif choice == "0":
            logout()
            break
        else:
            print("Invalid choice.")


def instructor_menu(instructor, cursor):
    while True:
        print(f"\n=== Instructor Menu — {instructor.title} {instructor.first_name} {instructor.last_name} ===")
        print("1. Browse all courses (Fall 2026)")
        print("2. Search courses by parameter")
        print("3. View my teaching schedule")
        print("4. View class list for a course")
        print("5. Search roster for a specific student")
        print("0. Logout / Exit")

        choice = input("\nChoice: ").strip()

        if choice == "1":
            instructor.search_courses(cursor)
        elif choice == "2":
            param = input("Search by (e.g. DEPT, TITLE, CREDITS): ").strip()
            value = input("Value: ").strip()
            instructor.search_courses_by_parameter(cursor, param, value)
        elif choice == "3":
            instructor.print_schedule(cursor)
        elif choice == "4":
            crn = input("CRN: ").strip()
            instructor.print_class_list(cursor, int(crn))
        elif choice == "5":
            crn = input("CRN: ").strip()
            sid = input("Student ID: ").strip()
            instructor.search_roster(cursor, int(crn), int(sid))
        elif choice == "0":
            logout()
            break
        else:
            print("Invalid choice.")


def admin_menu(admin, cursor, database):
    while True:
        print(f"\n=== Admin Menu — {admin.title} {admin.first_name} {admin.last_name} ===")
        print("--- Courses ---")
        print(" 1. Browse all courses")
        print(" 2. Add a course")
        print(" 3. Remove a course")
        print(" 4. Assign instructor to a course")
        print(" 5. Remove instructor from a course")
        print(" 6. Enroll student in a course")
        print(" 7. Remove student from a course")
        print(" 8. View roster for a course")
        print("--- Users ---")
        print(" 9. Add a user")
        print("10. Remove a user")
        print("--- System ---")
        print("11. Print all records")
        print("12. Search records")
        print("13. Update a record")
        print("14. Match courses to instructors")
        print(" 0. Logout / Exit")

        choice = input("\nChoice: ").strip()

        if choice == "1":
            admin.search_courses(cursor)
        elif choice == "2":
            # Collect each course field individually so input is explicit and easy to follow.
            crn     = input("CRN: ").strip()
            title   = input("Title: ").strip()
            dept    = input("Department (e.g. BSCO): ").strip().upper()
            time    = input("Time (e.g. 9:00AM): ").strip()
            days    = input("Days (e.g. MWF): ").strip().upper()
            sem     = input("Semester (Fall/Spring): ").strip()
            year    = input("Year: ").strip()
            credits = input("Credits: ").strip()
            cap     = input("Capacity: ").strip()
            admin.add_course(cursor, (int(crn), title, dept, time, days, sem, int(year), int(credits), int(cap)))
        elif choice == "3":
            crn = input("CRN to remove: ").strip()
            admin.remove_course(cursor, int(crn))
        elif choice == "4":
            inst_id = input("Instructor ID: ").strip()
            crn     = input("CRN: ").strip()
            admin.add_instructor_to_course(cursor, int(inst_id), int(crn))
        elif choice == "5":
            inst_id = input("Instructor ID: ").strip()
            crn     = input("CRN: ").strip()
            admin.remove_instructor_from_course(cursor, int(inst_id), int(crn))
        elif choice == "6":
            sid = input("Student ID: ").strip()
            crn = input("CRN: ").strip()
            admin.add_student_to_course(cursor, int(sid), int(crn))
        elif choice == "7":
            sid = input("Student ID: ").strip()
            crn = input("CRN: ").strip()
            admin.remove_student_from_course(cursor, int(sid), int(crn))
        elif choice == "8":
            crn = input("CRN: ").strip()
            admin.print_roster(cursor, int(crn))
        elif choice == "9":
            # Ask for the role first so we know which fields to collect.
            role = input("Role (student/instructor/admin): ").strip().lower()
            uid  = int(input("ID: ").strip())
            fn   = input("First name: ").strip()
            ln   = input("Last name: ").strip()
            if role == "student":
                grad  = int(input("Grad year: ").strip())
                major = input("Major (e.g. BSCO): ").strip().upper()
                email = input("Email: ").strip()
                admin.add_user(cursor, role, (uid, fn, ln, grad, major, email))
            elif role == "instructor":
                title_    = input("Title (e.g. Professor): ").strip()
                hire_year = int(input("Hire year: ").strip())
                dept      = input("Department (e.g. BSCO): ").strip().upper()
                email     = input("Email: ").strip()
                admin.add_user(cursor, role, (uid, fn, ln, title_, hire_year, dept, email))
            elif role == "admin":
                title_  = input("Title (e.g. Registrar): ").strip()
                office  = input("Office: ").strip()
                email   = input("Email: ").strip()
                admin.add_user(cursor, role, (uid, fn, ln, title_, office, email))
            else:
                print("  Unknown role.")
        elif choice == "10":
            role = input("Role (student/instructor/admin): ").strip().lower()
            uid  = int(input("ID to remove: ").strip())
            admin.remove_user(cursor, role, uid)
        elif choice == "11":
            print_all(cursor)
        elif choice == "12":
            search(cursor)
        elif choice == "13":
            update(cursor, database)
        elif choice == "14":
            match_courses(cursor)
        elif choice == "0":
            logout()
            break
        else:
            print("Invalid choice.")


# MAIN MENU
# Runs setup first, requires a successful login, then delegates to the
# appropriate role-specific menu so each user only sees their own options.

def main():
    database = sqlite3.connect("assignment4.db")
    cursor = database.cursor()

    setup(cursor, database)
    seed_users_and_courses(cursor, database)
    seed_login_table(cursor, database)

    # Require a successful login before showing any menu. If login() exhausts
    # all attempts it returns (None, None) — we close the connection and stop.
    role, user_id = login(cursor)
    if role is None:
        database.close()
        return

    # Load the matching record from the database so we can populate the user
    # object with their real name, email, etc. rather than leaving them blank.
    if role == "student":
        cursor.execute("SELECT * FROM STUDENT WHERE ID = ?", (user_id,))
        row = cursor.fetchone()
        user = row_to_student(row)
        student_menu(user, cursor)

    elif role == "instructor":
        cursor.execute("SELECT * FROM INSTRUCTOR WHERE ID = ?", (user_id,))
        row = cursor.fetchone()
        user = row_to_instructor(row)
        instructor_menu(user, cursor)

    elif role == "admin":
        cursor.execute("SELECT * FROM ADMIN WHERE ID = ?", (user_id,))
        row = cursor.fetchone()
        user = row_to_admin(row)
        admin_menu(user, cursor, database)

    database.close()


if __name__ == "__main__":
    main()
