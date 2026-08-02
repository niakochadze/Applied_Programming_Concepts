# Assignment 8 - GUI (tkinter)
# Shubaan, Nia, Dillon
#
# A tkinter front end for the registration system built in Assignment5.py.
# None of the backend logic (classes, database setup, login, etc.) is
# rewritten here - every button in this file just calls a function or
# method that already exists in Assignment5.py and displays whatever it
# prints. This file only builds the window, the screens, and the plumbing
# that connects button clicks to those existing functions.
#
# ARCHITECTURE: one tkinter window (RegistrationApp) holds four frames -
# LoginPage, StudentPage, InstructorPage, AdminPage - stacked on top of
# each other in the same container. Switching "screens" just raises a
# different frame to the top (tkraise()); no new windows are ever opened.

import io
import sqlite3
import tkinter as tk
from contextlib import redirect_stdout
from tkinter import messagebox, simpledialog
from unittest.mock import patch

import Assignment5 as a5

DB_FILENAME = "assignment4.db"
FONT = ("TkDefaultFont", 12)
TITLE_FONT = ("TkDefaultFont", 18, "bold")
WELCOME_FONT = ("TkDefaultFont", 16, "bold")

# Columns Student/Instructor/Admin.search_courses_by_parameter() will
# accept - shown to the user so they know what to type in the dialog box.
SEARCH_COLUMNS_HINT = "CRN, TITLE, DEPT, TIME, DAYS, SEMESTER, YEAR, CREDITS"


def run_and_display(output_box, func, *args, **kwargs):
    """Call an existing Assignment5 function/method, capture everything it
    prints with print(), and show that captured text in output_box instead.
    This is the one place stdout gets redirected - every button on the
    Student/Instructor/Admin screens goes through this same helper, which
    is also what clears the box before showing new output."""
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        func(*args, **kwargs)

    output_box.config(state="normal")      # has to be editable to change it
    output_box.delete("1.0", tk.END)       # clear whatever was there before
    output_box.insert(tk.END, buffer.getvalue())
    output_box.config(state="disabled")    # back to read-only for the user


def build_output_area(parent):
    """Build a plain Text widget with a Scrollbar attached to it (the
    'scrollable text area' every role screen needs), and return the Text
    widget so buttons can pass it to run_and_display()."""
    output_frame = tk.Frame(parent)
    output_frame.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(output_frame)
    scrollbar.pack(side="right", fill="y")

    text_area = tk.Text(output_frame, font=FONT, wrap="word",
                         yscrollcommand=scrollbar.set, state="disabled")
    text_area.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=text_area.yview)

    return text_area


def build_button_column(parent, buttons):
    """buttons is a list of (label, command) pairs. Creates one left-
    aligned Button per pair, stacked in a column, and returns the column
    Frame so the caller can pack it on the left side of the screen."""
    column = tk.Frame(parent)
    for label, command in buttons:
        tk.Button(column, text=label, font=FONT, width=28, anchor="w",
                  command=command).pack(fill="x", pady=2)
    return column


class RegistrationApp(tk.Tk):
    """The one and only window. Owns the single shared database connection
    and cursor - the same objects get passed into every Assignment5
    function/method call, exactly like Assignment5.main() does - and holds
    all four screens stacked in one container frame."""

    def __init__(self):
        super().__init__()
        self.title("University Registration System")
        self.geometry("950x600")

        # One connection/cursor shared by the whole app for its lifetime.
        self.database = sqlite3.connect(DB_FILENAME)
        self.cursor = self.database.cursor()

        # Same startup sequence Assignment5.main() runs, so the GUI starts
        # from identical data. Their print() output isn't shown anywhere
        # (there's no screen up yet to show it on), so it's discarded.
        with redirect_stdout(io.StringIO()):
            a5.setup(self.cursor, self.database)
            a5.seed_users_and_courses(self.cursor, self.database)
            a5.seed_login_table(self.cursor, self.database)

        # Container that holds every screen, stacked on top of each other.
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for PageClass in (LoginPage, StudentPage, InstructorPage, AdminPage):
            frame = PageClass(container, self)
            self.frames[PageClass] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(LoginPage)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Apple's bundled Tcl/Tk (8.5, shipped with macOS's system Python)
        # has a long-standing rendering bug: Label and Entry widgets can
        # come up visually blank on first draw - only Buttons paint
        # correctly - and stay blank until the window is resized. Nudging
        # the window size by one pixel and back forces Tk to repaint
        # everything, working around it without needing a newer Tcl/Tk.
        self.after(50, self._force_redraw)

    def _force_redraw(self):
        width = self.winfo_width()
        height = self.winfo_height()
        self.geometry(f"{width + 1}x{height + 1}")
        self.geometry(f"{width}x{height}")

    def show_frame(self, page_class):
        """Raise one screen to the top of the stack - this is the entire
        'screen switching' mechanism, no new windows are created."""
        self.frames[page_class].tkraise()

    def on_login_success(self, role, user_id):
        """Called by LoginPage once a5.login() has returned a real role.
        Loads the matching record the same way Assignment5.main() does,
        hands the resulting object to that role's screen, and shows it."""
        if role == "student":
            self.cursor.execute("SELECT * FROM STUDENT WHERE ID = ?", (user_id,))
            user = a5.row_to_student(self.cursor.fetchone())
            self.frames[StudentPage].set_user(user)
            self.show_frame(StudentPage)

        elif role == "instructor":
            self.cursor.execute("SELECT * FROM INSTRUCTOR WHERE ID = ?", (user_id,))
            user = a5.row_to_instructor(self.cursor.fetchone())
            self.frames[InstructorPage].set_user(user)
            self.show_frame(InstructorPage)

        elif role == "admin":
            self.cursor.execute("SELECT * FROM ADMIN WHERE ID = ?", (user_id,))
            user = a5.row_to_admin(self.cursor.fetchone())
            self.frames[AdminPage].set_user(user)
            self.show_frame(AdminPage)

    def do_logout(self):
        """Shared by every role screen's Logout button. Calls the existing
        module-level logout() (its printed goodbye message is discarded,
        same as the startup print()s), resets the login form, and goes
        back to the login screen."""
        with redirect_stdout(io.StringIO()):
            a5.logout()
        self.frames[LoginPage].reset()
        self.show_frame(LoginPage)

    def on_close(self):
        self.database.close()
        self.destroy()


class LoginPage(tk.Frame):
    """The first screen shown. Collects an email/password and hands them
    to the real a5.login() using the input()/getpass() monkeypatch
    described above, instead of re-implementing the credential check."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="University Registration System",
                 font=TITLE_FONT).pack(pady=(40, 20))

        form = tk.Frame(self)
        form.pack(pady=10)

        tk.Label(form, text="Email:", font=FONT).grid(
            row=0, column=0, sticky="e", padx=5, pady=5)
        self.email_entry = tk.Entry(form, font=FONT, width=30)
        self.email_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form, text="Password:", font=FONT).grid(
            row=1, column=0, sticky="e", padx=5, pady=5)
        # show="*" masks each typed character with an asterisk.
        self.password_entry = tk.Entry(form, font=FONT, width=30, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Button(self, text="Login", font=FONT, width=15,
                  command=self.attempt_login).pack(pady=10)

        self.error_label = tk.Label(self, text="", fg="red", font=FONT)
        self.error_label.pack()

        button_row = tk.Frame(self)
        button_row.pack(pady=30)
        tk.Button(button_row, text="Forgot Password", font=FONT,
                  command=self.show_forgot_password).pack(side="left", padx=5)
        tk.Button(button_row, text="Help", font=FONT,
                  command=self.show_help).pack(side="left", padx=5)
        tk.Button(button_row, text="About", font=FONT,
                  command=self.show_about).pack(side="left", padx=5)

    def attempt_login(self):
        self.error_label.config(text="")  # clear any leftover error first

        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        # a5.login() normally reads the email/password from the terminal
        # via input() and getpass(). Rather than rewrite it, we swap those
        # two calls out for stand-ins that just hand back what's already
        # typed into the boxes above - the same technique the Assignment6
        # test suite uses to drive login() without a real terminal. The
        # patch only lasts for this one call and is undone automatically
        # when the "with" block ends.
        with patch("builtins.input", return_value=email), \
             patch("Assignment5.getpass", return_value=password), \
             redirect_stdout(io.StringIO()):
            role, user_id = a5.login(self.controller.cursor)

        if role is None:
            self.error_label.config(text="Invalid email or password")
            self.password_entry.delete(0, tk.END)
        else:
            self.email_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.controller.on_login_success(role, user_id)

    def reset(self):
        """Clear the form - called when a Logout button brings us back here."""
        self.email_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.error_label.config(text="")

    def show_forgot_password(self):
        messagebox.showinfo("Forgot Password",
                             "Contact your administrator to reset your password.")

    def show_help(self):
        messagebox.showinfo(
            "Help",
            "1. Enter your university email and password, then click Login.\n\n"
            "2. Students, instructors, and admins each see a different set "
            "of buttons after logging in.\n\n"
            "3. Click a button on the left to perform an action - if it "
            "needs more information (like a CRN), a small box will pop up "
            "asking for it.\n\n"
            "4. Results appear in the text area on the right.\n\n"
            "5. Click Logout at any time to return to this screen."
        )

    def show_about(self):
        messagebox.showinfo(
            "About",
            "University Registration System\n\n"
            "Shubaan Meyyappan\n"
            "Nia Kochadze\n"
            "Dillion Borowski\n\n"
            "ELEC3225 Applied Programming Concepts"
        )


class StudentPage(tk.Frame):
    """Shown after a student logs in. self.student is set by set_user()
    right after login and is the same Student object main() would have
    built - every button below just calls a method on it."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.student = None

        self.welcome_label = tk.Label(self, text="Welcome, Student", font=WELCOME_FONT)
        self.welcome_label.pack(pady=10, anchor="w", padx=10)

        body = tk.Frame(self)
        body.pack(fill="both", expand=True, padx=10, pady=10)

        buttons = [
            ("Search All Courses", self.search_all_courses),
            ("Search Courses by Parameter", self.search_by_parameter),
            ("Add Course", self.add_course),
            ("Drop Course", self.drop_course),
            ("Check Schedule Conflicts", self.check_conflicts),
            ("Print My Schedule", self.print_schedule),
            ("Logout", self.logout),
        ]
        build_button_column(body, buttons).pack(side="left", fill="y", padx=(0, 10))
        self.output = build_output_area(body)

    def set_user(self, student):
        self.student = student
        self.welcome_label.config(text=f"Welcome, {student.first_name} — Student")

    def search_all_courses(self):
        run_and_display(self.output, self.student.search_courses, self.controller.cursor)

    def search_by_parameter(self):
        param = simpledialog.askstring(
            "Search by Parameter", f"Search by ({SEARCH_COLUMNS_HINT}):", parent=self)
        if param is None:
            return
        value = simpledialog.askstring("Search by Parameter", "Value to search for:", parent=self)
        if value is None:
            return
        run_and_display(self.output, self.student.search_courses_by_parameter,
                         self.controller.cursor, param, value)

    def add_course(self):
        crn = simpledialog.askinteger("Add Course", "Enter the CRN to add:", parent=self)
        if crn is None:
            return
        run_and_display(self.output, self.student.add_course, self.controller.cursor, crn)

    def drop_course(self):
        crn = simpledialog.askinteger("Drop Course", "Enter the CRN to drop:", parent=self)
        if crn is None:
            return
        run_and_display(self.output, self.student.drop_course, self.controller.cursor, crn)

    def check_conflicts(self):
        run_and_display(self.output, self.student.check_conflicts, self.controller.cursor)

    def print_schedule(self):
        run_and_display(self.output, self.student.print_schedule, self.controller.cursor)

    def logout(self):
        self.controller.do_logout()


class InstructorPage(tk.Frame):
    """Shown after an instructor logs in. self.instructor is set by
    set_user() and is the same Instructor object main() would have built."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.instructor = None

        self.welcome_label = tk.Label(self, text="Welcome, Instructor", font=WELCOME_FONT)
        self.welcome_label.pack(pady=10, anchor="w", padx=10)

        body = tk.Frame(self)
        body.pack(fill="both", expand=True, padx=10, pady=10)

        buttons = [
            ("Search All Courses", self.search_all_courses),
            ("Search Courses by Parameter", self.search_by_parameter),
            ("Print My Teaching Schedule", self.print_schedule),
            ("Print Class List", self.print_class_list),
            ("Search Roster for Student", self.search_roster),
            ("Logout", self.logout),
        ]
        build_button_column(body, buttons).pack(side="left", fill="y", padx=(0, 10))
        self.output = build_output_area(body)

    def set_user(self, instructor):
        self.instructor = instructor
        self.welcome_label.config(text=f"Welcome, {instructor.first_name} — Instructor")

    def search_all_courses(self):
        run_and_display(self.output, self.instructor.search_courses, self.controller.cursor)

    def search_by_parameter(self):
        param = simpledialog.askstring(
            "Search by Parameter", f"Search by ({SEARCH_COLUMNS_HINT}):", parent=self)
        if param is None:
            return
        value = simpledialog.askstring("Search by Parameter", "Value to search for:", parent=self)
        if value is None:
            return
        run_and_display(self.output, self.instructor.search_courses_by_parameter,
                         self.controller.cursor, param, value)

    def print_schedule(self):
        run_and_display(self.output, self.instructor.print_schedule, self.controller.cursor)

    def print_class_list(self):
        crn = simpledialog.askinteger("Print Class List", "Enter the CRN:", parent=self)
        if crn is None:
            return
        run_and_display(self.output, self.instructor.print_class_list, self.controller.cursor, crn)

    def search_roster(self):
        crn = simpledialog.askinteger("Search Roster", "Enter the CRN:", parent=self)
        if crn is None:
            return
        student_id = simpledialog.askinteger("Search Roster", "Enter the Student ID:", parent=self)
        if student_id is None:
            return
        run_and_display(self.output, self.instructor.search_roster,
                         self.controller.cursor, crn, student_id)

    def logout(self):
        self.controller.do_logout()


class AdminPage(tk.Frame):
    """Shown after an admin logs in. self.admin is set by set_user() and
    is the same Admin object main() would have built."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.admin = None

        self.welcome_label = tk.Label(self, text="Welcome, Admin", font=WELCOME_FONT)
        self.welcome_label.pack(pady=10, anchor="w", padx=10)

        body = tk.Frame(self)
        body.pack(fill="both", expand=True, padx=10, pady=10)

        buttons = [
            ("Search All Courses", self.search_all_courses),
            ("Search Courses by Parameter", self.search_by_parameter),
            ("Add Course", self.add_course),
            ("Remove Course", self.remove_course),
            ("Add User", self.add_user),
            ("Remove User", self.remove_user),
            ("Add Student to Course", self.add_student_to_course),
            ("Remove Student from Course", self.remove_student_from_course),
            ("Link Instructor to Course", self.link_instructor_to_course),
            ("Unlink Instructor from Course", self.unlink_instructor_from_course),
            ("Print Roster", self.print_roster),
            ("Logout", self.logout),
        ]
        build_button_column(body, buttons).pack(side="left", fill="y", padx=(0, 10))
        self.output = build_output_area(body)

    def set_user(self, admin):
        self.admin = admin
        self.welcome_label.config(text=f"Welcome, {admin.first_name} — Admin")

    def search_all_courses(self):
        run_and_display(self.output, self.admin.search_courses, self.controller.cursor)

    def search_by_parameter(self):
        param = simpledialog.askstring(
            "Search by Parameter", f"Search by ({SEARCH_COLUMNS_HINT}):", parent=self)
        if param is None:
            return
        value = simpledialog.askstring("Search by Parameter", "Value to search for:", parent=self)
        if value is None:
            return
        run_and_display(self.output, self.admin.search_courses_by_parameter,
                         self.controller.cursor, param, value)

    def add_course(self):
        # Same 9 fields the terminal admin menu asks for, one dialog box at
        # a time, in the exact order Admin.add_course() expects them.
        crn = simpledialog.askinteger("Add Course", "CRN:", parent=self)
        if crn is None:
            return
        title = simpledialog.askstring("Add Course", "Title:", parent=self)
        if title is None:
            return
        dept = simpledialog.askstring("Add Course", "Department (e.g. BSCO):", parent=self)
        if dept is None:
            return
        time_ = simpledialog.askstring("Add Course", "Time (e.g. 9:00AM):", parent=self)
        if time_ is None:
            return
        days = simpledialog.askstring("Add Course", "Days (e.g. MWF):", parent=self)
        if days is None:
            return
        semester = simpledialog.askstring("Add Course", "Semester (Fall/Spring):", parent=self)
        if semester is None:
            return
        year = simpledialog.askinteger("Add Course", "Year:", parent=self)
        if year is None:
            return
        credits_ = simpledialog.askinteger("Add Course", "Credits:", parent=self)
        if credits_ is None:
            return
        capacity = simpledialog.askinteger("Add Course", "Capacity:", parent=self)
        if capacity is None:
            return

        course_data = (crn, title, dept.strip().upper(), time_, days.strip().upper(),
                        semester, year, credits_, capacity)
        run_and_display(self.output, self.admin.add_course, self.controller.cursor, course_data)

    def remove_course(self):
        crn = simpledialog.askinteger("Remove Course", "Enter the CRN to remove:", parent=self)
        if crn is None:
            return
        run_and_display(self.output, self.admin.remove_course, self.controller.cursor, crn)

    def add_user(self):
        # Ask which role first, since that decides which fields come next -
        # the same branching Admin.add_user() itself expects.
        role = simpledialog.askstring(
            "Add User", "Role (student, instructor, or admin):", parent=self)
        if role is None:
            return
        role = role.strip().lower()
        if role not in ("student", "instructor", "admin"):
            messagebox.showerror(
                "Add User", f"Unknown role '{role}'. Must be student, instructor, or admin.")
            return

        uid = simpledialog.askinteger("Add User", "ID:", parent=self)
        if uid is None:
            return
        first = simpledialog.askstring("Add User", "First name:", parent=self)
        if first is None:
            return
        last = simpledialog.askstring("Add User", "Last name:", parent=self)
        if last is None:
            return

        if role == "student":
            grad = simpledialog.askinteger("Add User", "Grad year:", parent=self)
            if grad is None:
                return
            major = simpledialog.askstring("Add User", "Major (e.g. BSCO):", parent=self)
            if major is None:
                return
            email = simpledialog.askstring("Add User", "Email:", parent=self)
            if email is None:
                return
            user_data = (uid, first, last, grad, major.strip().upper(), email)

        elif role == "instructor":
            title_ = simpledialog.askstring("Add User", "Title (e.g. Professor):", parent=self)
            if title_ is None:
                return
            hire_year = simpledialog.askinteger("Add User", "Hire year:", parent=self)
            if hire_year is None:
                return
            dept = simpledialog.askstring("Add User", "Department (e.g. BSCO):", parent=self)
            if dept is None:
                return
            email = simpledialog.askstring("Add User", "Email:", parent=self)
            if email is None:
                return
            user_data = (uid, first, last, title_, hire_year, dept.strip().upper(), email)

        else:  # admin
            title_ = simpledialog.askstring("Add User", "Title (e.g. Registrar):", parent=self)
            if title_ is None:
                return
            office = simpledialog.askstring("Add User", "Office:", parent=self)
            if office is None:
                return
            email = simpledialog.askstring("Add User", "Email:", parent=self)
            if email is None:
                return
            user_data = (uid, first, last, title_, office, email)

        run_and_display(self.output, self.admin.add_user, self.controller.cursor, role, user_data)

    def remove_user(self):
        uid = simpledialog.askinteger("Remove User", "ID to remove:", parent=self)
        if uid is None:
            return
        role = simpledialog.askstring(
            "Remove User", "Role (student, instructor, or admin):", parent=self)
        if role is None:
            return
        run_and_display(self.output, self.admin.remove_user, self.controller.cursor, role, uid)

    def add_student_to_course(self):
        student_id = simpledialog.askinteger("Add Student to Course", "Student ID:", parent=self)
        if student_id is None:
            return
        crn = simpledialog.askinteger("Add Student to Course", "CRN:", parent=self)
        if crn is None:
            return
        run_and_display(self.output, self.admin.add_student_to_course,
                         self.controller.cursor, student_id, crn)

    def remove_student_from_course(self):
        student_id = simpledialog.askinteger("Remove Student from Course", "Student ID:", parent=self)
        if student_id is None:
            return
        crn = simpledialog.askinteger("Remove Student from Course", "CRN:", parent=self)
        if crn is None:
            return
        run_and_display(self.output, self.admin.remove_student_from_course,
                         self.controller.cursor, student_id, crn)

    def link_instructor_to_course(self):
        instructor_id = simpledialog.askinteger(
            "Link Instructor to Course", "Instructor ID:", parent=self)
        if instructor_id is None:
            return
        crn = simpledialog.askinteger("Link Instructor to Course", "CRN:", parent=self)
        if crn is None:
            return
        run_and_display(self.output, self.admin.add_instructor_to_course,
                         self.controller.cursor, instructor_id, crn)

    def unlink_instructor_from_course(self):
        instructor_id = simpledialog.askinteger(
            "Unlink Instructor from Course", "Instructor ID:", parent=self)
        if instructor_id is None:
            return
        crn = simpledialog.askinteger("Unlink Instructor from Course", "CRN:", parent=self)
        if crn is None:
            return
        run_and_display(self.output, self.admin.remove_instructor_from_course,
                         self.controller.cursor, instructor_id, crn)

    def print_roster(self):
        crn = simpledialog.askinteger("Print Roster", "Enter the CRN:", parent=self)
        if crn is None:
            return
        run_and_display(self.output, self.admin.print_roster, self.controller.cursor, crn)

    def logout(self):
        self.controller.do_logout()


if __name__ == "__main__":
    app = RegistrationApp()
    app.mainloop()
