# Assignment 6 - Automated Tests
# Shubaan, Nia, Dillon
#
# Automated tests using unittest - no typed inputs.
# Uses an in-memory database so assignment4.db is never touched.
# login() input is faked with unittest.mock.patch.
# Printed output is captured so tests can check it.

import io
import sqlite3
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import Assignment5 as a5


# Run a function, capture and return whatever it prints
def quiet(func, *args, **kwargs):
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        func(*args, **kwargs)
    return buffer.getvalue()


# Base class - fresh database before every test
class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.database = sqlite3.connect(":memory:")
        self.cursor = self.database.cursor()
        # Reuse our own setup and seed functions
        quiet(a5.setup, self.cursor, self.database)
        quiet(a5.seed_users_and_courses, self.cursor, self.database)
        quiet(a5.seed_login_table, self.cursor, self.database)

        # Shared test student
        self.cursor.execute("SELECT * FROM STUDENT WHERE ID = 11001")
        self.student = a5.row_to_student(self.cursor.fetchone())

    def tearDown(self):
        self.database.close()

    # Check if a (student, course) pair is in ENROLLMENT
    def enrollment_exists(self, student_id, crn):
        self.cursor.execute(
            "SELECT 1 FROM ENROLLMENT WHERE STUDENT_ID = ? AND CRN = ?",
            (student_id, crn)
        )
        return self.cursor.fetchone() is not None


# ADD/REMOVE COURSE FROM SEMESTER SCHEDULE (STUDENT)

class TestStudentAddDrop(BaseTestCase):

    # Typical: add a valid course
    def test_add_course_typical(self):
        quiet(self.student.add_course, self.cursor, 41001)
        self.assertTrue(self.enrollment_exists(11001, 41001))

    # Unlikely: CRN doesn't exist
    def test_add_course_nonexistent_crn(self):
        output = quiet(self.student.add_course, self.cursor, 99999)
        self.assertIn("No course found", output)
        self.assertFalse(self.enrollment_exists(11001, 99999))

    # Unlikely: enrolling in the same course twice
    def test_add_course_duplicate(self):
        quiet(self.student.add_course, self.cursor, 41001)
        output = quiet(self.student.add_course, self.cursor, 41001)
        self.assertIn("already enrolled", output)
        # Still only one enrollment row
        self.cursor.execute(
            "SELECT COUNT(*) FROM ENROLLMENT WHERE STUDENT_ID = 11001 AND CRN = 41001"
        )
        self.assertEqual(self.cursor.fetchone()[0], 1)

    # Unlikely: course is full
    def test_add_course_full(self):
        # Capacity 1 course with the seat already taken
        self.cursor.execute(
            "INSERT INTO COURSE VALUES (48000, 'Tiny Seminar', 'BSCO', '8:00AM', 'F', 'Fall', 2026, 1, 1)"
        )
        self.cursor.execute("INSERT INTO ENROLLMENT VALUES (11002, 48000)")
        self.database.commit()

        output = quiet(self.student.add_course, self.cursor, 48000)
        self.assertIn("full", output)
        self.assertFalse(self.enrollment_exists(11001, 48000))

    # Typical: drop an enrolled course
    def test_drop_course_typical(self):
        quiet(self.student.add_course, self.cursor, 41002)
        quiet(self.student.drop_course, self.cursor, 41002)
        self.assertFalse(self.enrollment_exists(11001, 41002))

    # Unlikely: drop a course never added
    def test_drop_course_not_enrolled(self):
        output = quiet(self.student.drop_course, self.cursor, 41003)
        self.assertIn("not enrolled", output)


# ASSEMBLE AND PRINT COURSE ROSTER / CLASS LIST (INSTRUCTOR)

class TestInstructorRoster(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.cursor.execute("SELECT * FROM INSTRUCTOR WHERE ID = 21001")
        self.instructor = a5.row_to_instructor(self.cursor.fetchone())

    # Typical: roster with enrolled students
    def test_class_list_typical(self):
        self.cursor.execute("INSERT INTO ENROLLMENT VALUES (11001, 41001)")
        self.cursor.execute("INSERT INTO ENROLLMENT VALUES (11003, 41001)")
        self.database.commit()

        output = quiet(self.instructor.print_class_list, self.cursor, 41001)
        self.assertIn("Martinez", output)
        self.assertIn("Johnson", output)

    # Unlikely: valid course, no enrollments
    def test_class_list_empty(self):
        output = quiet(self.instructor.print_class_list, self.cursor, 41001)
        self.assertIn("No students enrolled", output)

    # Unlikely: CRN doesn't exist
    def test_class_list_nonexistent_crn(self):
        output = quiet(self.instructor.print_class_list, self.cursor, 99999)
        self.assertIn("No students enrolled", output)

    # Typical: student on roster / Unlikely: student not on roster
    def test_search_roster_found_and_not_found(self):
        self.cursor.execute("INSERT INTO ENROLLMENT VALUES (11001, 41001)")
        self.database.commit()

        found = quiet(self.instructor.search_roster, self.cursor, 41001, 11001)
        self.assertIn("IS enrolled", found)

        not_found = quiet(self.instructor.search_roster, self.cursor, 41001, 11002)
        self.assertIn("NOT enrolled", not_found)


# ADD/REMOVE COURSES FROM THE SYSTEM (ADMIN)

class TestAdminCourses(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.cursor.execute("SELECT * FROM ADMIN WHERE ID = 31001")
        self.admin = a5.row_to_admin(self.cursor.fetchone())

    # Typical: add a new course
    def test_add_course_typical(self):
        new_course = (45001, "Embedded Systems", "BSCO", "9:00AM", "TTH", "Fall", 2026, 4, 30)
        quiet(self.admin.add_course, self.cursor, new_course)

        self.cursor.execute("SELECT TITLE FROM COURSE WHERE CRN = 45001")
        self.assertEqual(self.cursor.fetchone()[0], "Embedded Systems")

    # Unlikely: duplicate CRN
    def test_add_course_duplicate_crn(self):
        dupe = (41001, "Fake Copy", "BSCO", "9:00AM", "MWF", "Fall", 2026, 3, 30)
        output = quiet(self.admin.add_course, self.cursor, dupe)
        self.assertIn("already exists", output)

        # Original course untouched
        self.cursor.execute("SELECT TITLE FROM COURSE WHERE CRN = 41001")
        self.assertEqual(self.cursor.fetchone()[0], "Intro to Programming")

    # Typical: remove an existing course
    def test_remove_course_typical(self):
        quiet(self.admin.remove_course, self.cursor, 41001)
        self.cursor.execute("SELECT 1 FROM COURSE WHERE CRN = 41001")
        self.assertIsNone(self.cursor.fetchone())

    # Unlikely: remove a course that doesn't exist
    def test_remove_course_nonexistent(self):
        output = quiet(self.admin.remove_course, self.cursor, 99999)
        self.assertIn("No course found", output)


# LOG-IN, LOG-OUT (ALL USERS)

class TestLoginLogout(BaseTestCase):

    # Typical: valid student login
    def test_login_typical_student(self):
        # Password is now masked via getpass(), which reads the raw stdin
        # stream instead of going through builtins.input() - so it needs
        # its own patch separate from the email input() patch.
        with patch("builtins.input", side_effect=["omartinez@university.edu"]), \
             patch("Assignment5.getpass", return_value="omartinez"):
            with redirect_stdout(io.StringIO()):
                role, user_id = a5.login(self.cursor)
        self.assertEqual(role, "student")
        self.assertEqual(user_id, 11001)

    # Typical: valid admin login
    def test_login_typical_admin(self):
        with patch("builtins.input", side_effect=["pnolan@university.edu"]), \
             patch("Assignment5.getpass", return_value="pnolan"):
            with redirect_stdout(io.StringIO()):
                role, user_id = a5.login(self.cursor)
        self.assertEqual(role, "admin")
        self.assertEqual(user_id, 31001)

    # Typical: valid instructor login
    def test_login_typical_instructor(self):
        with patch("builtins.input", side_effect=["rhayes@university.edu"]), \
             patch("Assignment5.getpass", return_value="rhayes"):
            with redirect_stdout(io.StringIO()):
                role, user_id = a5.login(self.cursor)
        self.assertEqual(role, "instructor")
        self.assertEqual(user_id, 21001)

    # Unlikely: wrong password 3 times
    def test_login_wrong_password_three_times(self):
        fake_emails = ["omartinez@university.edu"] * 3
        fake_passwords = ["wrong1", "wrong2", "wrong3"]
        with patch("builtins.input", side_effect=fake_emails), \
             patch("Assignment5.getpass", side_effect=fake_passwords):
            with redirect_stdout(io.StringIO()):
                role, user_id = a5.login(self.cursor)
        self.assertIsNone(role)
        self.assertIsNone(user_id)

    # Unlikely: email that belongs to nobody
    def test_login_unknown_email(self):
        fake_emails = ["ghost@university.edu"] * 3
        fake_passwords = ["ghost"] * 3
        with patch("builtins.input", side_effect=fake_emails), \
             patch("Assignment5.getpass", side_effect=fake_passwords):
            with redirect_stdout(io.StringIO()):
                role, user_id = a5.login(self.cursor)
        self.assertIsNone(role)

    # Logout flips the flag and prints the message
    def test_logout_flags_and_message(self):
        self.student.logged_in = True
        quiet(self.student.logout)
        self.assertFalse(self.student.logged_in)

        output = quiet(a5.logout)
        self.assertIn("logged out", output)


# SEARCH ALL COURSES (DEFAULT SEARCH) (ALL USERS)

class TestSearchAllCourses(BaseTestCase):

    # Typical: lists Fall 2026 courses only
    def test_search_all_typical(self):
        output = quiet(self.student.search_courses, self.cursor)
        self.assertIn("Intro to Programming", output)
        self.assertNotIn("Operating Systems", output)  # Spring 2027

    # Unlikely: empty COURSE table
    def test_search_all_empty_table(self):
        self.cursor.execute("DELETE FROM COURSE")
        self.database.commit()
        output = quiet(self.student.search_courses, self.cursor)
        self.assertIn("No courses found", output)


# SEARCH COURSES BASED ON PARAMETERS (ALL USERS)

class TestSearchByParameter(BaseTestCase):

    # Typical: exact match on department
    def test_search_by_dept_typical(self):
        output = quiet(self.student.search_courses_by_parameter,
                       self.cursor, "DEPT", "BSEE")
        self.assertIn("Circuits II", output)
        self.assertNotIn("Thermodynamics", output)  # BSME

    # Typical: partial title match (LIKE)
    def test_search_by_title_partial(self):
        output = quiet(self.student.search_courses_by_parameter,
                       self.cursor, "TITLE", "Calc")
        self.assertIn("Calculus III", output)

    # Unlikely: lowercase parameter still works
    def test_search_lowercase_parameter(self):
        output = quiet(self.student.search_courses_by_parameter,
                       self.cursor, "dept", "BSCO")
        self.assertIn("Data Structures II", output)

    # Unlikely: invalid column name
    def test_search_invalid_column(self):
        output = quiet(self.student.search_courses_by_parameter,
                       self.cursor, "PROFESSOR", "Hayes")
        self.assertIn("Cannot search by", output)

    # Unlikely: SQL injection attempt
    def test_search_injection_attempt(self):
        output = quiet(self.student.search_courses_by_parameter,
                       self.cursor, "CRN; DROP TABLE COURSE", "1")
        self.assertIn("Cannot search by", output)
        # COURSE table still intact
        self.cursor.execute("SELECT COUNT(*) FROM COURSE")
        self.assertGreater(self.cursor.fetchone()[0], 0)

    # Unlikely: valid column, no matches
    def test_search_no_matches(self):
        output = quiet(self.student.search_courses_by_parameter,
                       self.cursor, "DEPT", "ZZZZ")
        self.assertIn("No matching courses found", output)


if __name__ == "__main__":
    unittest.main()