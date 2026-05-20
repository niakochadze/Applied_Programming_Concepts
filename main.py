# Shubaan Meyyappan

# Base User class for the scheduling system
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

    # Searches available courses
    def search_courses(self):
        print("Student course search function called.")

    # Adds a course
    def add_course(self):
        print("Student add course function called.")

    # Drops a course
    def drop_course(self):
        print("Student drop course function called.")

    # Prints student schedule
    def print_schedule(self):
        print("Student schedule print function called.")


# Instructor class derived from User
class Instructor(User):

    # Prints instructor schedule
    def print_schedule(self):
        print("Instructor schedule print function called.")

    # Prints instructor class list
    def print_class_list(self):
        print("Instructor class list function called.")

    # Searches available courses
    def search_courses(self):
        print("Instructor course search function called.")


# Admin class derived from User
class Admin(User):

    # Adds a course
    def add_course(self):
        print("Admin add course function called.")

    # Removes a course
    def remove_course(self):
        print("Admin remove course function called.")

    # Adds a user
    def add_user(self):
        print("Admin add user function called.")

    # Removes a user
    def remove_user(self):
        print("Admin remove user function called.")

    # Adds student to course
    def add_student_to_course(self):
        print("Admin add student to course function called.")

    # Removes student from course
    def remove_student_from_course(self):
        print("Admin remove student from course function called.")

    # Searches available courses
    def search_courses(self):
        print("Admin course search function called.")

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

    student1.search_courses()
    student1.add_course()
    student1.drop_course()
    student1.print_schedule()

    print()

    # Instructor object
    instructor1 = Instructor()

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
    admin1 = Admin()

    admin1.set_first_name("Michael")
    admin1.set_last_name("Brown")
    admin1.set_id(3001)

    print("----- Admin Information -----")
    admin1.print_info()

    admin1.add_course()
    admin1.remove_course()

    admin1.add_user()
    admin1.remove_user()

    admin1.add_student_to_course()
    admin1.remove_student_from_course()


    admin1.search_courses()
    admin1.print_roster()


main()