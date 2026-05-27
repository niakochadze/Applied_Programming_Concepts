# Shubaan Meyyappan
# Process Model: Incremental Development
# Built in iterations - each phase adds on top of the last.
# Iteration 1: User class hierarchy (done in Assignment 1)
# Iteration 2: Course class and course list added
# Iteration 3: Real logic for add, drop, search added


# ITERATION 1: User class hierarchy

class User:

    def __init__(self):
        self.first_name = ""
        self.last_name = ""
        self.user_id = 0

    def set_first_name(self, first_name):
        self.first_name = first_name

    def set_last_name(self, last_name):
        self.last_name = last_name

    def set_id(self, user_id):
        self.user_id = user_id

    def print_info(self):
        print(f"First Name: {self.first_name}")
        print(f"Last Name: {self.last_name}")
        print(f"ID: {self.user_id}")


#ITERATION 2: Course class added

class Course:

    def __init__(self):
        self.crn = 0
        self.course_name = ""
        self.time = ""
        self.semester = ""
        self.capacity = 0
        self.instructor = None
        self.enrolled_students = []

    def set_crn(self, crn):
        self.crn = crn

    def set_course_name(self, name):
        self.course_name = name

    def set_time(self, time):
        self.time = time

    def set_semester(self, semester):
        self.semester = semester

    def set_capacity(self, capacity):
        self.capacity = capacity

    def set_instructor(self, instructor):
        self.instructor = instructor

    def print_info(self):
        print(f"CRN: {self.crn}")
        print(f"Course: {self.course_name}")
        print(f"Time: {self.time}")
        print(f"Semester: {self.semester}")
        print(f"Enrolled: {len(self.enrolled_students)}/{self.capacity}")


# Course list added in Iteration 2 - holds up to 100 students, 10 instructors
class Database:

    def __init__(self):
        self.students = []
        self.instructors = []
        self.courses = []

    def add_course(self, course):
        self.courses.append(course)

    def remove_course(self, crn):
        self.courses = [c for c in self.courses if c.crn != crn]

    def search_courses(self, keyword=""):
        if keyword:
            return [c for c in self.courses if keyword.lower() in c.course_name.lower()]
        return self.courses


# ITERATION 3: Real logic added to each class

class Student(User):

    def __init__(self):
        super().__init__()
        self.schedule = []

    def search_courses(self, database, keyword=""):
        print("Student course search function called.")
        for course in database.search_courses(keyword):
            print(f"  [{course.crn}] {course.course_name} - {course.time} ({course.semester})")

    def add_course(self, course):
        print("Student add course function called.")
        if len(course.enrolled_students) < course.capacity:
            self.schedule.append(course)
            course.enrolled_students.append(self)
            print(f"  Added: {course.course_name}")
        else:
            print(f"  Course full: {course.course_name}")

    def drop_course(self, course):
        print("Student drop course function called.")
        if course in self.schedule:
            self.schedule.remove(course)
            course.enrolled_students.remove(self)
            print(f"  Dropped: {course.course_name}")

    def print_schedule(self):
        print("Student schedule print function called.")
        if not self.schedule:
            print("  No courses enrolled.")
        for course in self.schedule:
            print(f"  [{course.crn}] {course.course_name} - {course.time} ({course.semester})")


class Instructor(User):

    def __init__(self):
        super().__init__()
        self.courses_teaching = []

    def print_schedule(self):
        print("Instructor schedule print function called.")
        for course in self.courses_teaching:
            print(f"  [{course.crn}] {course.course_name} - {course.time}")

    def print_class_list(self):
        print("Instructor class list function called.")
        for course in self.courses_teaching:
            print(f"  {course.course_name}:")
            for student in course.enrolled_students:
                print(f"    - {student.first_name} {student.last_name} (ID: {student.user_id})")

    def search_courses(self, database, keyword=""):
        print("Instructor course search function called.")
        for course in database.search_courses(keyword):
            print(f"  [{course.crn}] {course.course_name} - {course.time}")


class Admin(User):

    def add_course(self, database, course):
        print("Admin add course function called.")
        database.add_course(course)

    def remove_course(self, database, crn):
        print("Admin remove course function called.")
        database.remove_course(crn)

    def add_user(self, database, user):
        print("Admin add user function called.")
        if isinstance(user, Student):
            database.students.append(user)
        elif isinstance(user, Instructor):
            database.instructors.append(user)

    def remove_user(self, database, user):
        print("Admin remove user function called.")
        if isinstance(user, Student) and user in database.students:
            database.students.remove(user)
        elif isinstance(user, Instructor) and user in database.instructors:
            database.instructors.remove(user)

    def add_student_to_course(self, student, course):
        print("Admin add student to course function called.")
        course.enrolled_students.append(student)
        student.schedule.append(course)

    def remove_student_from_course(self, student, course):
        print("Admin remove student from course function called.")
        if student in course.enrolled_students:
            course.enrolled_students.remove(student)
            student.schedule.remove(course)

    def search_courses(self, database, keyword=""):
        print("Admin course search function called.")
        for course in database.search_courses(keyword):
            print(f"  [{course.crn}] {course.course_name} - {course.time}")

    def print_roster(self, course):
        print("Admin print roster function called.")
        print(f"  Roster for {course.course_name} ({course.crn}):")
        for student in course.enrolled_students:
            print(f"    - {student.first_name} {student.last_name} (ID: {student.user_id})")


# MAIN: Testing Iteration 3
def main():

    db = Database()

    # Instructor
    instructor1 = Instructor()
    instructor1.set_first_name("Sarah")
    instructor1.set_last_name("Johnson")
    instructor1.set_id(2001)
    db.instructors.append(instructor1)

    # Course
    course1 = Course()
    course1.set_crn(10101)
    course1.set_course_name("Applied Programming Concepts")
    course1.set_time("MWF 9:00-9:50AM")
    course1.set_semester("Fall 2026")
    course1.set_capacity(30)
    course1.set_instructor(instructor1)
    instructor1.courses_teaching.append(course1)
    db.add_course(course1)

    # Student
    student1 = Student()
    student1.set_first_name("John")
    student1.set_last_name("Smith")
    student1.set_id(1001)
    db.students.append(student1)

    print("----- Student Information -----")
    student1.print_info()
    student1.search_courses(db, "Programming")
    student1.add_course(course1)
    student1.print_schedule()
    student1.drop_course(course1)

    print()

    print("----- Instructor Information -----")
    instructor1.print_info()
    instructor1.search_courses(db)
    instructor1.print_schedule()
    instructor1.print_class_list()

    print()

    admin1 = Admin()
    admin1.set_first_name("Michael")
    admin1.set_last_name("Brown")
    admin1.set_id(3001)

    print("----- Admin Information -----")
    admin1.print_info()
    admin1.add_student_to_course(student1, course1)
    admin1.search_courses(db)
    admin1.print_roster(course1)
    admin1.remove_student_from_course(student1, course1)

    course2 = Course()
    course2.set_crn(20202)
    course2.set_course_name("Data Structures")
    course2.set_time("TTH 11:00-12:15PM")
    course2.set_semester("Fall 2026")
    course2.set_capacity(25)

    admin1.add_course(db, course2)
    admin1.remove_course(db, 20202)
    admin1.add_user(db, student1)
    admin1.remove_user(db, student1)


main()