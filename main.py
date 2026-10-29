"""Main application entry point — Person 3 dashboard and integration."""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from database import init_db
from dashboard import DashboardFrame
from reports import ReportsWindow
from styles import apply_theme


class LibraryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Library Management System")
        self.geometry("1200x790")
        self.minsize(980, 650)
        apply_theme(self)
        self._build()

    def _build(self):
        header = ttk.Frame(self, padding=(18, 14))
        header.pack(fill="x")
        ttk.Label(header, text="LIBRARY MANAGEMENT SYSTEM", font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Label(header, text="Person 3 · Dashboard & Reports", font=("Segoe UI", 10)).pack(side="right")
        ttk.Separator(self).pack(fill="x")
        self.dashboard = DashboardFrame(self, self.open_books, self.open_students, self.open_reports)
        self.dashboard.pack(fill="both", expand=True)
        footer = ttk.Frame(self, padding=(18, 5, 18, 12))
        footer.pack(fill="x")
        ttk.Label(footer, text="Connected modules use the shared MySQL database: library_management").pack(side="left")
        ttk.Button(footer, text="Exit", command=self.destroy).pack(side="right")

    def _launch_module(self, filename, label):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if not os.path.isfile(path):
            messagebox.showerror("Module not found", f"Cannot find {filename}.\nKeep the module file beside main.py.", parent=self)
            return
        try:
            subprocess.Popen([sys.executable, path], cwd=os.path.dirname(path))
        except OSError as exc:
            messagebox.showerror("Could not open module", f"Unable to start {label}.\n\n{exc}", parent=self)

    def open_books(self):
        self._launch_module("book_management.py", "Book Management")

    def open_students(self):
        self._launch_module("student_issue_return.py", "Student Management / Issue-Return")

    def open_reports(self):
        ReportsWindow(self)


def main():
    try:
        init_db()
    except Exception as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Database connection failed", "Could not connect to MySQL.\n\n"
            "1. Start MySQL Server.\n2. Check the LIBRARY_DB_* environment variables.\n"
            "3. Ensure the configured MySQL account can access the library_management database.\n\n"
            f"Details: {exc}")
        root.destroy()
        return
    LibraryApp().mainloop()


if __name__ == "__main__":
    main()
