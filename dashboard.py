"""Dashboard widgets and live summary queries for Person 3."""
import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection


class DashboardFrame(ttk.Frame):
    def __init__(self, master, on_open_books, on_open_students, on_open_reports):
        super().__init__(master, padding=18)
        self.on_open_books = on_open_books
        self.on_open_students = on_open_students
        self.on_open_reports = on_open_reports
        self._build()
        self.refresh()

    def _build(self):
        ttk.Label(self, text="Library Overview", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(self, text="Live summary of books, students, and lending activity.").pack(anchor="w", pady=(2, 14))
        cards = ttk.Frame(self)
        cards.pack(fill="x")
        self.metric_vars = {key: tk.StringVar(value="—") for key in ("titles", "copies", "available", "issued", "students", "overdue")}
        card_info = (("titles", "Book Titles"), ("copies", "Total Copies"), ("available", "Available Copies"),
                     ("issued", "Issued Copies"), ("students", "Registered Students"), ("overdue", "Overdue Loans"))
        for index, (key, label) in enumerate(card_info):
            card = ttk.LabelFrame(cards, text=label, padding=(14, 10))
            card.grid(row=index // 3, column=index % 3, sticky="nsew", padx=5, pady=5)
            ttk.Label(card, textvariable=self.metric_vars[key], font=("Segoe UI", 22, "bold")).pack(anchor="w")
            cards.columnconfigure(index % 3, weight=1)
        actions = ttk.LabelFrame(self, text="Quick Actions", padding=12)
        actions.pack(fill="x", pady=(12, 14))
        ttk.Button(actions, text="Manage Books (Person 1)", command=self.on_open_books).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Students & Issue/Return (Person 2)", command=self.on_open_students).pack(side="left", padx=8)
        ttk.Button(actions, text="Open Reports", command=self.on_open_reports).pack(side="left", padx=8)
        ttk.Button(actions, text="Refresh Dashboard", command=self.refresh).pack(side="right")

        recent_box = ttk.LabelFrame(self, text="Recent Transactions", padding=8)
        recent_box.pack(fill="both", expand=True)
        cols = ("id", "student", "book", "issue", "due", "status")
        self.recent_tree = ttk.Treeview(recent_box, columns=cols, show="headings", height=8)
        headings = ("Transaction ID", "Student", "Book", "Issue Date", "Due Date", "Status")
        widths = (105, 190, 300, 120, 120, 100)
        for col, heading, width in zip(cols, headings, widths):
            self.recent_tree.heading(col, text=heading)
            self.recent_tree.column(col, width=width, minwidth=70, anchor="w")
        self.recent_tree.pack(fill="both", expand=True)

    def refresh(self):
        try:
            with get_connection() as (_conn, cursor):
                cursor.execute("""SELECT COUNT(*) AS titles, COALESCE(SUM(quantity),0) AS copies,
                    COALESCE(SUM(available),0) AS available,
                    COALESCE(SUM(quantity-available),0) AS issued FROM books""")
                books = cursor.fetchone()
                cursor.execute("SELECT COUNT(*) AS students FROM students")
                students = cursor.fetchone()["students"]
                cursor.execute("SELECT COUNT(*) AS overdue FROM transactions WHERE status='Issued' AND due_date < CURDATE()")
                overdue = cursor.fetchone()["overdue"]
                cursor.execute("""SELECT t.transaction_id, s.name AS student_name, b.title AS book_title,
                    t.issue_date, t.due_date, t.status FROM transactions t
                    JOIN students s ON s.student_id=t.student_id
                    JOIN books b ON b.book_id=t.book_id ORDER BY t.transaction_id DESC LIMIT 10""")
                recent = cursor.fetchall()
            values = {"titles": books["titles"], "copies": books["copies"], "available": books["available"],
                      "issued": books["issued"], "students": students, "overdue": overdue}
            for key, value in values.items():
                self.metric_vars[key].set(str(value))
            self.recent_tree.delete(*self.recent_tree.get_children())
            for row in recent:
                self.recent_tree.insert("", "end", values=(row["transaction_id"], row["student_name"], row["book_title"], row["issue_date"], row["due_date"], row["status"]))
        except Exception as exc:
            messagebox.showerror("Dashboard error", f"Could not load dashboard data.\n\nCheck that MySQL is running and database.py uses the correct credentials.\n\n{exc}", parent=self.winfo_toplevel())
