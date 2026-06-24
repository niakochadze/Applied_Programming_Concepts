# Assignment 4
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
        self.schedule = []

    def set_grad_year(self, year):
        self.grad_year = year

    def set_major(self, major):
        self.major = major

    def set_email(self, email):
        self.email = email

    def search_courses(self):
        print("Student course search function called.")

    def search_courses_by_parameter(self, parameter):
        print(f"Student searching courses with parameter: {parameter}")

    def add_course(self, course):
        if course.crn in self.schedule:
            print(f"Course {course.crn} is already in your schedule.")
        elif course.enroll(self.user_id):
            self.schedule.append(course.crn)
            print(f"Course {course.crn} added to schedule.")
        else:
            print(f"Course {course.crn} is full.")

    def drop_course(self, course_id):
        if course_id in self.schedule:
            self.schedule.remove(course_id)
            print(f"Course {course_id} removed from schedule.")
        else:
            print(f"Course {course_id} not found in your schedule.")

    def check_conflicts(self):
        if len(self.schedule) != len(set(self.schedule)):
            print("Conflict detected in schedule.")
        else:
            print("No conflicts found in schedule.")

    def print_schedule(self):
        print("Student Schedule:")
        if len(self.schedule) == 0:
            print("  No courses enrolled.")
        else:
            for course_id in self.schedule:
                print(f"  Course ID: {course_id}")

    def print_info(self):
        print(f"[Student] ID: {self.user_id} | {self.first_name} {self.last_name} | Major: {self.major} | Grad: {self.grad_year} | Email: {self.email}")


class Instructor(User):

    def __init__(self):
        super().__init__()
        self.title = ""
        self.hire_year = 0
        self.department = ""
        self.email = ""
        self.courses = []
        self.roster = []

    def set_title(self, title):
        self.title = title

    def set_hire_year(self, year):
        self.hire_year = year

    def set_department(self, dept):
        self.department = dept

    def set_email(self, email):
        self.email = email

    def search_courses(self):
        print("Instructor course search function called.")

    def search_courses_by_parameter(self, parameter):
        print(f"Instructor searching courses with parameter: {parameter}")

    def print_schedule(self):
        print("Instructor Teaching Schedule:")
        if len(self.courses) == 0:
            print("  No courses assigned.")
        else:
            for course_id in self.courses:
                print(f"  Course ID: {course_id}")

    def print_class_list(self):
        print("Instructor Class List:")
        if len(self.roster) == 0:
            print("  No students in roster.")
        else:
            for student_id in self.roster:
                print(f"  Student ID: {student_id}")

    def search_roster(self, student_id):
        if student_id in self.roster:
            print(f"Student {student_id} found in roster.")
        else:
            print(f"Student {student_id} not found in roster.")

    def print_info(self):
        print(f"[Instructor] ID: {self.user_id} | {self.first_name} {self.last_name} | {self.title} | Dept: {self.department} | Hired: {self.hire_year} | Email: {self.email}")


class Admin(User):

    def __init__(self):
        super().__init__()
        self.title = ""
        self.office = ""
        self.email = ""
        self.course_list = []
        self.user_list = []

    def set_title(self, title):
        self.title = title

    def set_office(self, office):
        self.office = office

    def set_email(self, email):
        self.email = email

    def add_course(self, course_id):
        if course_id in self.course_list:
            print(f"Course {course_id} already exists in the system.")
        else:
            self.course_list.append(course_id)
            print(f"Course {course_id} added to the system.")

    def remove_course(self, course_id):
        if course_id in self.course_list:
            self.course_list.remove(course_id)
            print(f"Course {course_id} removed from the system.")
        else:
            print(f"Course {course_id} not found in the system.")

    def add_user(self, user_id):
        if user_id in self.user_list:
            print(f"User {user_id} already exists in the system.")
        else:
            self.user_list.append(user_id)
            print(f"User {user_id} added to the system.")

    def remove_user(self, user_id):
        if user_id in self.user_list:
            self.user_list.remove(user_id)
            print(f"User {user_id} removed from the system.")
        else:
            print(f"User {user_id} not found in the system.")

    def add_student_to_course(self, student, course):
        student.add_course(course)
        print(f"Admin linked student {student.user_id} to course {course.crn}.")

    def remove_student_from_course(self, student, course_id):
        student.drop_course(course_id)
        print(f"Admin unlinked student {student.user_id} from course {course_id}.")

    def add_instructor_to_course(self, instructor, course_id):
        if course_id not in instructor.courses:
            instructor.courses.append(course_id)
            print(f"Admin linked instructor {instructor.user_id} to course {course_id}.")
        else:
            print(f"Instructor {instructor.user_id} is already linked to course {course_id}.")

    def remove_instructor_from_course(self, instructor, course_id):
        if course_id in instructor.courses:
            instructor.courses.remove(course_id)
            print(f"Admin unlinked instructor {instructor.user_id} from course {course_id}.")
        else:
            print(f"Instructor {instructor.user_id} is not linked to course {course_id}.")

    def search_courses(self):
        print("Admin course search function called.")

    def search_courses_by_parameter(self, parameter):
        print(f"Admin searching courses with parameter: {parameter}")

    def print_roster(self):
        print("Admin print roster function called.")

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
        print(f"[Course] CRN: {self.crn} | {self.title} | Dept: {self.department} | {self.days} {self.time} | {self.semester} {self.year} | {self.credits} credits")


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
    c.set_year(row[6]); c.set_credits(row[7])
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
        CREDITS INTEGER NOT NULL
    )"""
    cursor.execute(sql_command)

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
        cursor.execute("INSERT INTO COURSE VALUES (40001, 'Applied Programming Concepts', 'BSCO', '9:00AM', 'MWF', 'Fall', 2026, 3)")
        cursor.execute("INSERT INTO COURSE VALUES (40002, 'Circuits I', 'BSEE', '11:00AM', 'TTH', 'Fall', 2026, 4)")
        cursor.execute("INSERT INTO COURSE VALUES (40003, 'Statics', 'BSME', '1:00PM', 'MWF', 'Fall', 2026, 3)")
        cursor.execute("INSERT INTO COURSE VALUES (40004, 'Calculus III', 'BSAS', '10:00AM', 'TTH', 'Fall', 2026, 4)")
        cursor.execute("INSERT INTO COURSE VALUES (40005, 'Data Structures', 'BCOS', '2:00PM', 'MWF', 'Fall', 2026, 3)")
    except sqlite3.IntegrityError:
        pass

    # Save all setup changes to the database file
    database.commit()
    print("Database ready.\n")


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
        try:
            cursor.execute("INSERT INTO COURSE VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (crn, title, dept, time, days, sem, year, credits))
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


# MAIN MENU
# Runs setup first then loops the menu until the user exits

def main():
    database = sqlite3.connect("assignment4.db")
    cursor = database.cursor()

    setup(cursor, database)

    while True:
        print("University Scheduling System")
        print("1. Print all")
        print("2. Search")
        print("3. Insert")
        print("4. Update")
        print("5. Remove")
        print("6. Match courses to instructors")
        print("0. Exit")

        choice = input("\nChoice: ").strip()

        if choice == "1":
            print_all(cursor)
        elif choice == "2":
            search(cursor)
        elif choice == "3":
            insert(cursor, database)
        elif choice == "4":
            update(cursor, database)
        elif choice == "5":
            remove(cursor, database)
        elif choice == "6":
            match_courses(cursor)
        elif choice == "0":
            print("Exiting.")
            break
        else:
            print("Invalid choice.")

    database.close()


main()