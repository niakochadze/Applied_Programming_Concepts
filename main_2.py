# Dillon Borowski

# holds all the info for a single course
class Course:
    def __init__(self, course_id, name, instructor_id, capacity):
        self.course_id = course_id
        self.name = name
        self.instructor_id = instructor_id
        self.capacity = capacity
        self.enrolled = []  # list of student IDs currently in the course

    # just checks if theres no room left
    def is_full(self):
        return len(self.enrolled) >= self.capacity

    # adds a student if theres space and they arent already in it
    def enroll(self, student_id):
        if not self.is_full() and student_id not in self.enrolled:
            self.enrolled.append(student_id)
            return True
        return False

    # removes a student from the course
    def drop(self, student_id):
        if student_id in self.enrolled:
            self.enrolled.remove(student_id)
            return True
        return False

    # makes it easier to print course info
    def __str__(self):
        return f"[{self.course_id}] {self.name} | Instructor: {self.instructor_id} | {len(self.enrolled)}/{self.capacity} enrolled"


# base class that Student, Instructor, and Admin all inherit from
class User:

    # Default constructor
    def __init__(self):
        self.first_name = ""
        self.last_name = ""
        self.user_id = 0

    # Setter functions
    def set_first_name(self, first_name):
        self.first_name = first_name

    def set_last_name(self, last_name):
        self.last_name = last_name

    def set_id(self, user_id):
        self.user_id = user_id

    # Prints user information
    def print_info(self):
        print(f"First Name: {self.first_name}")
        print(f"Last Name: {self.last_name}")
        print(f"ID: {self.user_id}")


# Student class derived from User
class Student(User):

    def __init__(self, courses):
        super().__init__()
        self.courses = courses  # reference to the shared course list
        self.schedule = []      # only the courses this student is enrolled in

    # Searches available courses - can pass a keyword or leave it blank to get everything
    def search_courses(self, keyword=""):
        results = [c for c in self.courses if keyword.lower() in c.name.lower() or keyword.lower() in c.course_id.lower()] if keyword else self.courses
        for c in results:
            print(f"  {c}")

    # Adds a course
    def add_course(self, course_id):
        for c in self.courses:
            if c.course_id == course_id:
                if c.enroll(self.user_id):
                    self.schedule.append(c)
                    print(f"  Enrolled in {c.name}")
                else:
                    print(f"  Could not enroll in {course_id}")
                return
        print(f"  Course {course_id} not found")

    # Drops a course
    def drop_course(self, course_id):
        for c in self.schedule:
            if c.course_id == course_id:
                c.drop(self.user_id)
                self.schedule.remove(c)
                print(f"  Dropped {course_id}")
                return
        print(f"  Not enrolled in {course_id}")

    # Prints student schedule
    def print_schedule(self):
        if not self.schedule:
            print("  No courses enrolled")
            return
        for c in self.schedule:
            print(f"  {c}")


# Instructor class derived from User
class Instructor(User):

    def __init__(self, courses):
        super().__init__()
        self.courses = courses

    # Prints instructor schedule
    def print_schedule(self):
        # filters down to only courses where the instructor id matches
        my_courses = [c for c in self.courses if c.instructor_id == self.user_id]
        for c in my_courses:
            print(f"  {c}")

    # Prints instructor class list
    def print_class_list(self):
        my_courses = [c for c in self.courses if c.instructor_id == self.user_id]
        for c in my_courses:
            print(f"  {c.course_id} - {c.name}: {c.enrolled if c.enrolled else 'No students'}")

    # Searches available courses
    def search_courses(self, keyword=""):
        results = [c for c in self.courses if keyword.lower() in c.name.lower()] if keyword else self.courses
        for c in results:
            print(f"  {c}")


# Admin class derived from User
class Admin(User):

    def __init__(self, courses):
        super().__init__()
        self.courses = courses  # same shared list, admin can modify it directly
        self.users = []

    # Adds a course
    def add_course(self, course):
        self.courses.append(course)
        print(f"  Added: {course}")

    # Removes a course
    def remove_course(self, course_id):
        for c in self.courses:
            if c.course_id == course_id:
                self.courses.remove(c)
                print(f"  Removed {course_id}")
                return
        print(f"  Course {course_id} not found")

    # Adds a user
    def add_user(self, user):
        self.users.append(user)
        print(f"  Added user: {user.first_name} {user.last_name}")

    # Removes a user
    def remove_user(self, user_id):
        for u in self.users:
            if u.user_id == user_id:
                self.users.remove(u)
                print(f"  Removed user {user_id}")
                return
        print(f"  User {user_id} not found")

    # Adds student to course - admin can force enroll someone
    def add_student_to_course(self, student, course_id):
        for c in self.courses:
            if c.course_id == course_id:
                if c.enroll(student.user_id):
                    student.schedule.append(c)
                    print(f"  Enrolled student {student.user_id} in {course_id}")
                return
        print(f"  Course {course_id} not found")

    # Removes student from course
    def remove_student_from_course(self, student, course_id):
        for c in self.courses:
            if c.course_id == course_id:
                c.drop(student.user_id)
                # also remove it from the students personal schedule
                student.schedule = [x for x in student.schedule if x.course_id != course_id]
                print(f"  Removed student {student.user_id} from {course_id}")
                return

    # Searches available courses
    def search_courses(self, keyword=""):
        results = [c for c in self.courses if keyword.lower() in c.name.lower()] if keyword else self.courses
        for c in results:
            print(f"  {c}")

    # Prints roster
    def print_roster(self):
        for c in self.courses:
            print(f"  {c.course_id} - {c.name}: {c.enrolled if c.enrolled else 'Empty'}")


# Main function for testing
def main():

    # set up some courses to work with
    courses = [
        Course("CS101", "Intro to Programming", 2001, 3),
        Course("CS201", "Data Structures", 2001, 2),
        Course("EE101", "Circuits and Systems", 2002, 5),
        Course("MATH101", "Calculus I", 2002, 4)
    ]

    # Student object
    student1 = Student(courses)
    student1.set_first_name("John")
    student1.set_last_name("Smith")
    student1.set_id(1001)

    print("----- Student Information -----")
    student1.print_info()
    student1.search_courses()
    student1.add_course("CS101")
    student1.add_course("CS201")
    student1.drop_course("CS201")  # testing drop
    student1.print_schedule()

    print()

    # Instructor object
    instructor1 = Instructor(courses)
    instructor1.set_first_name("Sarah")
    instructor1.set_last_name("Johnson")
    instructor1.set_id(2001)

    print("----- Instructor Information -----")
    instructor1.print_info()
    instructor1.search_courses()
    instructor1.print_schedule()
    instructor1.print_class_list()

    print()

    # Admin object
    admin1 = Admin(courses)
    admin1.set_first_name("Michael")
    admin1.set_last_name("Brown")
    admin1.set_id(3001)

    print("----- Admin Information -----")
    admin1.print_info()
    admin1.add_course(Course("CS301", "Algorithms", 2001, 30))
    admin1.remove_course("EE101")
    admin1.add_user(student1)
    admin1.add_user(instructor1)
    admin1.remove_user(1001)
    admin1.add_student_to_course(student1, "CS201")
    admin1.remove_student_from_course(student1, "CS201")
    admin1.search_courses()
    admin1.print_roster()


main()
