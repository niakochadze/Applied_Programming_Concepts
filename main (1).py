# Dillon Borowski

# Base User class for the scheduling system
class User:

    # Default constructor
    def __init__(self):
        self.first_name = ""
        self.last_name = ""
        self.user_id = 0
        self.logged_in = False

    # Setter functions
    def set_first_name(self, first_name):
        self.first_name = first_name

    def set_last_name(self, last_name):
        self.last_name = last_name

    def set_id(self, user_id):
        self.user_id = user_id

    # Logs the user in
    def login(self):
        self.logged_in = True
        print(f"{self.first_name} {self.last_name} logged in.")

    # Logs the user out
    def logout(self):
        self.logged_in = False
        print(f"{self.first_name} {self.last_name} logged out.")

    # Prints user information
    def print_info(self):
        print(f"First Name: {self.first_name}")
        print(f"Last Name: {self.last_name}")
        print(f"ID: {self.user_id}")


# Student class derived from User
class Student(User):

    # Default constructor
    def __init__(self):
        super().__init__()
        self.schedule = []

    # Searches all available courses
    def search_courses(self):
        print("Student course search function called.")

    # Searches courses based on a parameter
    def search_courses_by_parameter(self, parameter):
        print(f"Student searching courses with parameter: {parameter}")

    # Adds a course by course ID
    def add_course(self, course_id):
        if course_id in self.schedule:
            print(f"Course {course_id} is already in your schedule.")
        else:
            self.schedule.append(course_id)
            print(f"Course {course_id} added to schedule.")

    # Drops a course by course ID
    def drop_course(self, course_id):
        if course_id in self.schedule:
            self.schedule.remove(course_id)
            print(f"Course {course_id} removed from schedule.")
        else:
            print(f"Course {course_id} not found in your schedule.")

    # Checks for conflicts in the course schedule
    def check_conflicts(self):
        if len(self.schedule) != len(set(self.schedule)):
            print("Conflict detected in schedule.")
        else:
            print("No conflicts found in schedule.")

    # Prints student schedule
    def print_schedule(self):
        print("Student Schedule:")
        if len(self.schedule) == 0:
            print("  No courses enrolled.")
        else:
            for course_id in self.schedule:
                print(f"  Course ID: {course_id}")


# Instructor class derived from User
class Instructor(User):

    # Default constructor
    def __init__(self):
        super().__init__()
        self.courses = []
        self.roster = []

    # Searches all available courses
    def search_courses(self):
        print("Instructor course search function called.")

    # Searches courses based on a parameter
    def search_courses_by_parameter(self, parameter):
        print(f"Instructor searching courses with parameter: {parameter}")

    # Prints instructor schedule
    def print_schedule(self):
        print("Instructor Teaching Schedule:")
        if len(self.courses) == 0:
            print("  No courses assigned.")
        else:
            for course_id in self.courses:
                print(f"  Course ID: {course_id}")

    # Prints instructor class list / roster
    def print_class_list(self):
        print("Instructor Class List:")
        if len(self.roster) == 0:
            print("  No students in roster.")
        else:
            for student_id in self.roster:
                print(f"  Student ID: {student_id}")

    # Searches the roster for a student by ID
    def search_roster(self, student_id):
        if student_id in self.roster:
            print(f"Student {student_id} found in roster.")
        else:
            print(f"Student {student_id} not found in roster.")


# Admin class derived from User
class Admin(User):

    # Default constructor
    def __init__(self):
        super().__init__()
        self.course_list = []
        self.user_list = []

    # Adds a course to the system
    def add_course(self, course_id):
        if course_id in self.course_list:
            print(f"Course {course_id} already exists in the system.")
        else:
            self.course_list.append(course_id)
            print(f"Course {course_id} added to the system.")

    # Removes a course from the system
    def remove_course(self, course_id):
        if course_id in self.course_list:
            self.course_list.remove(course_id)
            print(f"Course {course_id} removed from the system.")
        else:
            print(f"Course {course_id} not found in the system.")

    # Adds a user to the system
    def add_user(self, user_id):
        if user_id in self.user_list:
            print(f"User {user_id} already exists in the system.")
        else:
            self.user_list.append(user_id)
            print(f"User {user_id} added to the system.")

    # Removes a user from the system
    def remove_user(self, user_id):
        if user_id in self.user_list:
            self.user_list.remove(user_id)
            print(f"User {user_id} removed from the system.")
        else:
            print(f"User {user_id} not found in the system.")

    # Links a student to a course
    def add_student_to_course(self, student, course_id):
        student.add_course(course_id)
        print(f"Admin linked student {student.user_id} to course {course_id}.")

    # Unlinks a student from a course
    def remove_student_from_course(self, student, course_id):
        student.drop_course(course_id)
        print(f"Admin unlinked student {student.user_id} from course {course_id}.")

    # Links an instructor to a course
    def add_instructor_to_course(self, instructor, course_id):
        if course_id not in instructor.courses:
            instructor.courses.append(course_id)
            print(f"Admin linked instructor {instructor.user_id} to course {course_id}.")
        else:
            print(f"Instructor {instructor.user_id} is already linked to course {course_id}.")

    # Unlinks an instructor from a course
    def remove_instructor_from_course(self, instructor, course_id):
        if course_id in instructor.courses:
            instructor.courses.remove(course_id)
            print(f"Admin unlinked instructor {instructor.user_id} from course {course_id}.")
        else:
            print(f"Instructor {instructor.user_id} is not linked to course {course_id}.")

    # Searches all available courses
    def search_courses(self):
        print("Admin course search function called.")

    # Searches courses based on a parameter
    def search_courses_by_parameter(self, parameter):
        print(f"Admin searching courses with parameter: {parameter}")

    # Prints roster
    def print_roster(self):
        print("Admin print roster function called.")


# Main function for testing
def main():

    # Student object
    student1 = Student()

    student1.set_first_name("John")
    student1.set_last_name("Smith")
    student1.set_id(1001)

    print("----- Student Information -----")
    student1.print_info()
    student1.login()

    student1.search_courses()
    student1.search_courses_by_parameter("ELEC")
    student1.add_course(101)
    student1.add_course(102)
    student1.add_course(101)
    student1.check_conflicts()
    student1.drop_course(102)
    student1.print_schedule()
    student1.logout()

    print()

    # Instructor object
    instructor1 = Instructor()

    instructor1.set_first_name("Sarah")
    instructor1.set_last_name("Johnson")
    instructor1.set_id(2001)

    print("----- Instructor Information -----")
    instructor1.print_info()
    instructor1.login()

    instructor1.search_courses()
    instructor1.search_courses_by_parameter("ELEC")
    instructor1.print_schedule()
    instructor1.print_class_list()
    instructor1.roster.append(1001)
    instructor1.search_roster(1001)
    instructor1.search_roster(9999)
    instructor1.logout()

    print()

    # Admin object
    admin1 = Admin()

    admin1.set_first_name("Michael")
    admin1.set_last_name("Brown")
    admin1.set_id(3001)

    print("----- Admin Information -----")
    admin1.print_info()
    admin1.login()

    admin1.add_course(101)
    admin1.add_course(102)
    admin1.remove_course(102)

    admin1.add_user(1001)
    admin1.add_user(2001)
    admin1.remove_user(2001)

    admin1.add_student_to_course(student1, 103)
    admin1.remove_student_from_course(student1, 103)

    admin1.add_instructor_to_course(instructor1, 101)
    admin1.remove_instructor_from_course(instructor1, 101)

    admin1.search_courses()
    admin1.search_courses_by_parameter("ELEC")
    admin1.print_roster()
    admin1.logout()


main()