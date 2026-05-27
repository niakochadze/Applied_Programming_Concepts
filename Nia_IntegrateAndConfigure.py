# Nia Kochadze
# Process Model: Integrate and Configure
# Components used:
#   - sqlite3: persistent database for users and courses
#   - hashlib: password hashing for user authentication

import sqlite3
import hashlib


# ─── CONFIGURE: SQLite database setup ───
def init_database(db_path="scheduler.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            role TEXT,
            password_hash TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            crn INTEGER PRIMARY KEY,
            course_name TEXT,
            time TEXT,
            instructor_id INTEGER,
            FOREIGN KEY (instructor_id) REFERENCES users(user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            student_id INTEGER,
            crn INTEGER,
            PRIMARY KEY (student_id, crn)
        )
    """)

    conn.commit()
    return conn


# ─── INTEGRATE: Base User class wired to SQLite ───
class User:

    def __init__(self, conn):
        self.conn = conn
        self.first_name = ""
        self.last_name = ""
        self.user_id = 0
        self.role = ""

    def set_first_name(self, first_name):
        self.first_name = first_name

    def set_last_name(self, last_name):
        self.last_name = last_name

    def set_id(self, user_id):
        self.user_id = user_id

    def save(self, password="password123"):
        cursor = self.conn.cursor()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, first_name, last_name, role, password_hash)
            VALUES (?, ?, ?, ?, ?)
        """, (self.user_id, self.first_name, self.last_name, self.role, password_hash))
        self.conn.commit()

    def print_info(self):
        print(f"Name: {self.first_name} {self.last_name} | ID: {self.user_id} | Role: {self.role}")


# ─── INTEGRATE: Student ───
class Student(User):

    def __init__(self, conn):
        super().__init__(conn)
        self.role = "student"

    def add_course(self, crn):
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO enrollments (student_id, crn) VALUES (?, ?)", (self.user_id, crn))
            self.conn.commit()
            print(f"  Enrolled in CRN {crn}")
        except sqlite3.IntegrityError:
            print(f"  Already enrolled in CRN {crn}")

    def print_schedule(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.crn, c.course_name, c.time FROM courses c
            JOIN enrollments e ON c.crn = e.crn
            WHERE e.student_id = ?
        """, (self.user_id,))
        rows = cursor.fetchall()
        print(f"  Schedule for {self.first_name} {self.last_name}:")
        if not rows:
            print("  No courses enrolled.")
        for row in rows:
            print(f"    [{row[0]}] {row[1]} - {row[2]}")


# ─── INTEGRATE: Instructor ───
class Instructor(User):

    def __init__(self, conn):
        super().__init__(conn)
        self.role = "instructor"

    def print_class_list(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT crn, course_name FROM courses WHERE instructor_id = ?", (self.user_id,))
        courses = cursor.fetchall()
        for course in courses:
            print(f"  {course[1]} (CRN: {course[0]}):")
            cursor.execute("""
                SELECT u.first_name, u.last_name FROM users u
                JOIN enrollments e ON u.user_id = e.student_id
                WHERE e.crn = ?
            """, (course[0],))
            for student in cursor.fetchall():
                print(f"    - {student[0]} {student[1]}")


# ─── INTEGRATE: Admin ───
class Admin(User):

    def __init__(self, conn):
        super().__init__(conn)
        self.role = "admin"

    def add_course(self, crn, name, time, instructor):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO courses (crn, course_name, time, instructor_id)
            VALUES (?, ?, ?, ?)
        """, (crn, name, time, instructor.user_id))
        self.conn.commit()
        print(f"  Course added: {name} (CRN: {crn})")

    def add_user(self, user):
        user.save()
        print(f"  User added: {user.first_name} {user.last_name}")


# ─── MAIN: Integration Test ───
def main():

    conn = init_database(":memory:")

    # Setup
    instructor1 = Instructor(conn)
    instructor1.set_first_name("Sarah")
    instructor1.set_last_name("Johnson")
    instructor1.set_id(2001)
    instructor1.save()

    student1 = Student(conn)
    student1.set_first_name("John")
    student1.set_last_name("Smith")
    student1.set_id(1001)
    student1.save()

    admin1 = Admin(conn)
    admin1.set_first_name("Michael")
    admin1.set_last_name("Brown")
    admin1.set_id(3001)
    admin1.save()

    # Demonstrate integrate and configure
    print("----- Admin: Adding Course -----")
    admin1.add_course(10101, "Applied Programming Concepts", "MWF 9:00-9:50AM", instructor1)
    admin1.add_user(student1)

    print("\n----- Student: Enroll and View Schedule -----")
    student1.print_info()
    student1.add_course(10101)
    student1.print_schedule()

    print("\n----- Instructor: View Class List -----")
    instructor1.print_info()
    instructor1.print_class_list()

    conn.close()


main()