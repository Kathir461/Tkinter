"""Person 2 module: Student Management + Book Issue/Return.

Place this file beside Person 1's database.py. The shared database.py creates
and connects to the same library_management MySQL database.
Run: python student_issue_return.py
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from database import init_db, get_connection


class LibraryPerson2App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Library Management System - Students & Issue/Return")
        self.geometry("1180x720")
        self.minsize(950, 600)
        self.configure(padx=12, pady=12)

        ttk.Label(self, text="LIBRARY MANAGEMENT SYSTEM", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(self, text="Person 2 module: Student Management | Book Issue | Book Return", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 12))

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)
        self.student_tab = ttk.Frame(self.tabs, padding=10)
        self.issue_tab = ttk.Frame(self.tabs, padding=10)
        self.history_tab = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(self.student_tab, text="Student Management")
        self.tabs.add(self.issue_tab, text="Issue / Return Books")
        self.tabs.add(self.history_tab, text="Transaction History")

        self._build_students_tab()
        self._build_issue_tab()
        self._build_history_tab()
        self.refresh_all()

    def _tree(self, parent, columns, headings, widths=None, height=13):
        wrapper = ttk.Frame(parent)
        wrapper.pack(fill="both", expand=True, pady=(8, 0))
        tree = ttk.Treeview(wrapper, columns=columns, show="headings", height=height, selectmode="browse")
        vs = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
        hs = ttk.Scrollbar(wrapper, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        wrapper.rowconfigure(0, weight=1)
        wrapper.columnconfigure(0, weight=1)
        for i, col in enumerate(columns):
            tree.heading(col, text=headings[i])
            tree.column(col, width=(widths[i] if widths else 120), minwidth=70, anchor="w")
        return tree

    def _build_students_tab(self):
        form = ttk.LabelFrame(self.student_tab, text="Student Details", padding=10)
        form.pack(fill="x")
        self.student_vars = {k: tk.StringVar() for k in ("name", "department", "phone", "email")}
        labels = [("name", "Full name"), ("department", "Department"), ("phone", "Phone"), ("email", "Email")]
        for i, (key, label) in enumerate(labels):
            ttk.Label(form, text=label).grid(row=0, column=i, sticky="w", padx=5, pady=(0, 4))
            ttk.Entry(form, textvariable=self.student_vars[key], width=25).grid(row=1, column=i, sticky="ew", padx=5)
            form.columnconfigure(i, weight=1)
        buttons = ttk.Frame(form)
        buttons.grid(row=2, column=0, columnspan=4, sticky="w", pady=(10, 0))
        ttk.Button(buttons, text="Add Student", command=self.add_student).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Update Selected", command=self.update_student).pack(side="left", padx=6)
        ttk.Button(buttons, text="Delete Selected", command=self.delete_student).pack(side="left", padx=6)
        ttk.Button(buttons, text="Clear Form", command=self.clear_student_form).pack(side="left", padx=6)

        searchbar = ttk.Frame(self.student_tab)
        searchbar.pack(fill="x", pady=(12, 0))
        ttk.Label(searchbar, text="Search students:").pack(side="left")
        self.student_search = tk.StringVar()
        entry = ttk.Entry(searchbar, textvariable=self.student_search, width=35)
        entry.pack(side="left", padx=8)
        entry.bind("<Return>", lambda _e: self.load_students())
        ttk.Button(searchbar, text="Search", command=self.load_students).pack(side="left")
        ttk.Button(searchbar, text="Show All", command=lambda: (self.student_search.set(""), self.load_students())).pack(side="left", padx=6)

        self.student_tree = self._tree(self.student_tab,
            ("id", "name", "department", "phone", "email"),
            ("Student ID", "Full Name", "Department", "Phone", "Email"),
            (90, 230, 180, 140, 250))
        self.student_tree.bind("<<TreeviewSelect>>", self.on_student_select)

    def _build_issue_tab(self):
        form = ttk.LabelFrame(self.issue_tab, text="Issue a Book", padding=10)
        form.pack(fill="x")
        self.issue_student = tk.StringVar()
        self.issue_book = tk.StringVar()
        self.issue_date = tk.StringVar(value=date.today().isoformat())
        self.due_date = tk.StringVar(value=date.today().isoformat())
        ttk.Label(form, text="Student").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.student_combo = ttk.Combobox(form, textvariable=self.issue_student, state="readonly", width=36)
        self.student_combo.grid(row=1, column=0, sticky="ew", padx=5)
        ttk.Label(form, text="Book (available copies only)").grid(row=0, column=1, sticky="w", padx=5, pady=4)
        self.book_combo = ttk.Combobox(form, textvariable=self.issue_book, state="readonly", width=44)
        self.book_combo.grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Label(form, text="Issue date (YYYY-MM-DD)").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        ttk.Entry(form, textvariable=self.issue_date, width=18).grid(row=1, column=2, sticky="ew", padx=5)
        ttk.Label(form, text="Due date (YYYY-MM-DD)").grid(row=0, column=3, sticky="w", padx=5, pady=4)
        ttk.Entry(form, textvariable=self.due_date, width=18).grid(row=1, column=3, sticky="ew", padx=5)
        for i in range(4):
            form.columnconfigure(i, weight=1)
        ttk.Button(form, text="Issue Selected Book", command=self.issue_book_to_student).grid(row=2, column=0, sticky="w", padx=5, pady=(10, 0))
        ttk.Label(form, text="Select an active issue below and click Return Selected Book.").grid(row=3, column=0, columnspan=4, sticky="w", padx=5, pady=(12, 0))

        self.active_tree = self._tree(self.issue_tab,
            ("transaction_id", "student", "book", "issue_date", "due_date", "status"),
            ("Transaction ID", "Student", "Book", "Issue Date", "Due Date", "Status"),
            (110, 210, 280, 120, 120, 100), height=12)
        ttk.Button(self.issue_tab, text="Return Selected Book", command=self.return_selected_book).pack(anchor="w", pady=10)

    def _build_history_tab(self):
        bar = ttk.Frame(self.history_tab)
        bar.pack(fill="x")
        ttk.Label(bar, text="Filter:").pack(side="left")
        self.history_filter = tk.StringVar(value="All")
        combo = ttk.Combobox(bar, textvariable=self.history_filter, values=("All", "Issued", "Returned"), state="readonly", width=15)
        combo.pack(side="left", padx=8)
        combo.bind("<<ComboboxSelected>>", lambda _e: self.load_history())
        ttk.Button(bar, text="Refresh", command=self.load_history).pack(side="left")
        self.history_tree = self._tree(self.history_tab,
            ("transaction_id", "student_id", "student", "book_id", "book", "issue_date", "due_date", "return_date", "status"),
            ("Transaction ID", "Student ID", "Student Name", "Book ID", "Book Title", "Issue Date", "Due Date", "Return Date", "Status"),
            (105, 85, 180, 75, 220, 105, 105, 105, 90), height=18)

    @staticmethod
    def _selected_id(tree):
        selected = tree.selection()
        if not selected:
            return None
        values = tree.item(selected[0], "values")
        return int(values[0]) if values else None

    def _clear_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)

    def _show_error(self, title, exc):
        messagebox.showerror(title, str(exc), parent=self)

    def refresh_all(self):
        self.load_students()
        self.load_choices()
        self.load_active_transactions()
        self.load_history()

    def load_students(self):
        try:
            search = self.student_search.get().strip()
            with get_connection() as (_conn, cur):
                if search:
                    like = f"%{search}%"
                    cur.execute("""SELECT * FROM students WHERE name LIKE %s OR department LIKE %s
                                   OR phone LIKE %s OR email LIKE %s OR CAST(student_id AS CHAR) LIKE %s
                                   ORDER BY student_id DESC""", (like, like, like, like, like))
                else:
                    cur.execute("SELECT * FROM students ORDER BY student_id DESC")
                rows = cur.fetchall()
            self._clear_tree(self.student_tree)
            for row in rows:
                self.student_tree.insert("", "end", values=(row["student_id"], row["name"], row["department"], row["phone"], row["email"]))
        except Exception as exc:
            self._show_error("Could not load students", exc)

    def on_student_select(self, _event=None):
        selected = self.student_tree.selection()
        if not selected:
            return
        vals = self.student_tree.item(selected[0], "values")
        for key, value in zip(("name", "department", "phone", "email"), vals[1:]):
            self.student_vars[key].set(value or "")

    def clear_student_form(self):
        for var in self.student_vars.values():
            var.set("")
        self.student_tree.selection_remove(self.student_tree.selection())

    def _student_form_values(self):
        data = {key: var.get().strip() for key, var in self.student_vars.items()}
        if not data["name"]:
            raise ValueError("Student name is required.")
        return data

    def add_student(self):
        try:
            d = self._student_form_values()
            with get_connection() as (_conn, cur):
                cur.execute("INSERT INTO students (name, department, phone, email) VALUES (%s, %s, %s, %s)",
                            (d["name"], d["department"], d["phone"], d["email"]))
            messagebox.showinfo("Success", "Student added successfully.", parent=self)
            self.clear_student_form(); self.refresh_all()
        except Exception as exc:
            self._show_error("Could not add student", exc)

    def update_student(self):
        student_id = self._selected_id(self.student_tree)
        if student_id is None:
            messagebox.showwarning("Select student", "Select a student from the table first.", parent=self); return
        try:
            d = self._student_form_values()
            with get_connection() as (_conn, cur):
                cur.execute("UPDATE students SET name=%s, department=%s, phone=%s, email=%s WHERE student_id=%s",
                            (d["name"], d["department"], d["phone"], d["email"], student_id))
            messagebox.showinfo("Success", "Student details updated.", parent=self)
            self.refresh_all()
        except Exception as exc:
            self._show_error("Could not update student", exc)

    def delete_student(self):
        student_id = self._selected_id(self.student_tree)
        if student_id is None:
            messagebox.showwarning("Select student", "Select a student from the table first.", parent=self); return
        if not messagebox.askyesno("Confirm delete", "Delete this student? Students with transaction history cannot be deleted.", parent=self):
            return
        try:
            with get_connection() as (_conn, cur):
                cur.execute("SELECT COUNT(*) AS n FROM transactions WHERE student_id=%s", (student_id,))
                if cur.fetchone()["n"]:
                    raise ValueError("This student has transaction history and cannot be deleted.")
                cur.execute("DELETE FROM students WHERE student_id=%s", (student_id,))
            self.clear_student_form(); self.refresh_all()
        except Exception as exc:
            self._show_error("Could not delete student", exc)

    def load_choices(self):
        try:
            with get_connection() as (_conn, cur):
                cur.execute("SELECT student_id, name, department FROM students ORDER BY name")
                students = cur.fetchall()
                cur.execute("SELECT book_id, title, author, available FROM books WHERE available > 0 ORDER BY title")
                books = cur.fetchall()
            self.student_map = {f'{s["student_id"]} - {s["name"]} ({s["department"]})': s["student_id"] for s in students}
            self.book_map = {f'{b["book_id"]} - {b["title"]} by {b["author"]} [Available: {b["available"]}]': b["book_id"] for b in books}
            self.student_combo["values"] = list(self.student_map.keys())
            self.book_combo["values"] = list(self.book_map.keys())
            if self.issue_student.get() not in self.student_map:
                self.issue_student.set("")
            if self.issue_book.get() not in self.book_map:
                self.issue_book.set("")
        except Exception as exc:
            self._show_error("Could not load choices", exc)

    def issue_book_to_student(self):
        student_id = self.student_map.get(self.issue_student.get())
        book_id = self.book_map.get(self.issue_book.get())
        if not student_id or not book_id:
            messagebox.showwarning("Missing selection", "Choose a student and an available book.", parent=self); return
        try:
            issue = date.fromisoformat(self.issue_date.get().strip())
            due = date.fromisoformat(self.due_date.get().strip())
            if due < issue:
                raise ValueError("Due date cannot be earlier than the issue date.")
            with get_connection() as (_conn, cur):
                # Lock the selected book row to avoid issuing the same final copy twice.
                cur.execute("SELECT available FROM books WHERE book_id=%s FOR UPDATE", (book_id,))
                book = cur.fetchone()
                if not book or book["available"] < 1:
                    raise ValueError("This book is no longer available. Refresh and choose another book.")
                cur.execute("UPDATE books SET available=available-1 WHERE book_id=%s", (book_id,))
                cur.execute("INSERT INTO transactions (book_id, student_id, issue_date, due_date, status) VALUES (%s, %s, %s, %s, 'Issued')",
                            (book_id, student_id, issue.isoformat(), due.isoformat()))
            messagebox.showinfo("Success", "Book issued successfully.", parent=self)
            self.issue_book.set(""); self.refresh_all()
        except Exception as exc:
            self._show_error("Could not issue book", exc)

    def load_active_transactions(self):
        try:
            with get_connection() as (_conn, cur):
                cur.execute("""SELECT t.transaction_id, s.name AS student, b.title AS book,
                              t.issue_date, t.due_date, t.status
                              FROM transactions t JOIN students s ON s.student_id=t.student_id
                              JOIN books b ON b.book_id=t.book_id WHERE t.status='Issued'
                              ORDER BY t.due_date, t.transaction_id""")
                rows = cur.fetchall()
            self._clear_tree(self.active_tree)
            for r in rows:
                self.active_tree.insert("", "end", values=(r["transaction_id"], r["student"], r["book"], r["issue_date"], r["due_date"], r["status"]))
        except Exception as exc:
            self._show_error("Could not load issued books", exc)

    def return_selected_book(self):
        transaction_id = self._selected_id(self.active_tree)
        if transaction_id is None:
            messagebox.showwarning("Select transaction", "Select an issued book from the table first.", parent=self); return
        if not messagebox.askyesno("Confirm return", "Mark this book as returned?", parent=self):
            return
        try:
            with get_connection() as (_conn, cur):
                cur.execute("SELECT book_id, status FROM transactions WHERE transaction_id=%s FOR UPDATE", (transaction_id,))
                tx = cur.fetchone()
                if not tx or tx["status"] != "Issued":
                    raise ValueError("This transaction is not currently issued.")
                cur.execute("UPDATE transactions SET status='Returned', return_date=%s WHERE transaction_id=%s",
                            (date.today().isoformat(), transaction_id))
                cur.execute("UPDATE books SET available=available+1 WHERE book_id=%s", (tx["book_id"],))
            messagebox.showinfo("Success", "Book returned successfully.", parent=self)
            self.refresh_all()
        except Exception as exc:
            self._show_error("Could not return book", exc)

    def load_history(self):
        try:
            status = self.history_filter.get() if hasattr(self, "history_filter") else "All"
            sql = """SELECT t.transaction_id, s.student_id, s.name AS student, b.book_id,
                     b.title AS book, t.issue_date, t.due_date, t.return_date, t.status
                     FROM transactions t JOIN students s ON s.student_id=t.student_id
                     JOIN books b ON b.book_id=t.book_id"""
            params = ()
            if status in ("Issued", "Returned"):
                sql += " WHERE t.status=%s"; params = (status,)
            sql += " ORDER BY t.transaction_id DESC"
            with get_connection() as (_conn, cur):
                cur.execute(sql, params); rows = cur.fetchall()
            self._clear_tree(self.history_tree)
            for r in rows:
                self.history_tree.insert("", "end", values=(r["transaction_id"], r["student_id"], r["student"], r["book_id"], r["book"], r["issue_date"], r["due_date"], r["return_date"] or "—", r["status"]))
        except Exception as exc:
            self._show_error("Could not load transaction history", exc)


def main():
    try:
        init_db()
    except Exception as exc:
        root = tk.Tk(); root.withdraw()
        messagebox.showerror("Database connection failed", f"Could not connect to MySQL. Check that MySQL is running and database.py credentials are correct.\n\nDetails: {exc}")
        root.destroy()
        return
    app = LibraryPerson2App()
    app.mainloop()


if __name__ == "__main__":
    main()
