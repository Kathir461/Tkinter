"""Reports and CSV export for the Library Management System (Person 3)."""
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
from database import get_connection


class ReportsWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Library Reports")
        self.geometry("1100x650")
        self.minsize(850, 500)
        self.transient(master)
        self._build()
        self.refresh()

    def _build(self):
        top = ttk.Frame(self, padding=12)
        top.pack(fill="x")
        ttk.Label(top, text="LIBRARY REPORTS", font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="right", padx=(6, 0))
        ttk.Button(top, text="Export Current Report to CSV", command=self.export_csv).pack(side="right")

        filters = ttk.Frame(self, padding=(12, 0, 12, 8))
        filters.pack(fill="x")
        ttk.Label(filters, text="Report:").pack(side="left")
        self.report_kind = tk.StringVar(value="All Transactions")
        combo = ttk.Combobox(filters, textvariable=self.report_kind, state="readonly", width=25,
                             values=("All Transactions", "Currently Issued", "Overdue Books", "Returned Books"))
        combo.pack(side="left", padx=8)
        combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        self.summary = ttk.Label(filters, text="")
        self.summary.pack(side="right")

        holder = ttk.Frame(self, padding=(12, 0, 12, 12))
        holder.pack(fill="both", expand=True)
        cols = ("transaction_id", "student_id", "student_name", "book_id", "book_title", "issue_date", "due_date", "return_date", "status")
        self.tree = ttk.Treeview(holder, columns=cols, show="headings")
        labels = ("Txn ID", "Student ID", "Student", "Book ID", "Book", "Issue Date", "Due Date", "Return Date", "Status")
        widths = (75, 85, 165, 75, 220, 100, 100, 100, 90)
        for col, label, width in zip(cols, labels, widths):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, minwidth=65, anchor="w")
        ybar = ttk.Scrollbar(holder, orient="vertical", command=self.tree.yview)
        xbar = ttk.Scrollbar(holder, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)

    def _query(self):
        kind = self.report_kind.get()
        sql = """SELECT t.transaction_id, t.student_id, s.name AS student_name,
                         t.book_id, b.title AS book_title, t.issue_date, t.due_date,
                         t.return_date, t.status
                  FROM transactions t
                  JOIN students s ON s.student_id = t.student_id
                  JOIN books b ON b.book_id = t.book_id"""
        params = ()
        if kind == "Currently Issued":
            sql += " WHERE t.status = 'Issued'"
        elif kind == "Overdue Books":
            sql += " WHERE t.status = 'Issued' AND t.due_date < %s"
            params = (date.today().isoformat(),)
        elif kind == "Returned Books":
            sql += " WHERE t.status = 'Returned'"
        sql += " ORDER BY t.transaction_id DESC"
        with get_connection() as (_conn, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall()

    def refresh(self):
        try:
            rows = self._query()
            self.rows = rows
            self.tree.delete(*self.tree.get_children())
            for row in rows:
                values = [row.get(k) for k in ("transaction_id", "student_id", "student_name", "book_id", "book_title", "issue_date", "due_date", "return_date", "status")]
                values = ["" if v is None else str(v) for v in values]
                self.tree.insert("", "end", values=values)
            self.summary.config(text=f"{len(rows)} record(s) | Today: {date.today().isoformat()}")
        except Exception as exc:
            messagebox.showerror("Report error", f"Could not load report. Check the database connection.\n\n{exc}", parent=self)

    def export_csv(self):
        if not getattr(self, "rows", None):
            messagebox.showinfo("No data", "There are no records to export in this report.", parent=self)
            return
        filename = filedialog.asksaveasfilename(parent=self, title="Save report", defaultextension=".csv",
                                                initialfile="library_report.csv", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
        if not filename:
            return
        fields = ("transaction_id", "student_id", "student_name", "book_id", "book_title", "issue_date", "due_date", "return_date", "status")
        try:
            with open(filename, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                for row in self.rows:
                    writer.writerow({key: row.get(key) for key in fields})
            messagebox.showinfo("Export complete", f"Report saved to:\n{filename}", parent=self)
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc), parent=self)
