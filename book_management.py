"""Tkinter book-management screen using the MySQL functions in database.py."""
import tkinter as tk
from tkinter import ttk, messagebox

from database import init_db, add_book, get_books, update_book, delete_book


class BookManagementFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, padding=12, **kwargs)
        init_db()
        self.selected_book_id = None
        self._build_ui()
        self.refresh_books()

    def _build_ui(self):
        ttk.Label(self, text="Book Management", font=("Segoe UI", 18, "bold")).pack(
            anchor="w", pady=(0, 12)
        )
        form = ttk.LabelFrame(self, text="Book Details", padding=10)
        form.pack(fill="x", pady=(0, 12))
        self.vars = {
            "title": tk.StringVar(), "author": tk.StringVar(),
            "publisher": tk.StringVar(), "category": tk.StringVar(),
            "quantity": tk.StringVar(value="1"),
        }
        fields = [
            ("Title *", "title"), ("Author *", "author"),
            ("Publisher", "publisher"), ("Category", "category"), ("Quantity", "quantity"),
        ]
        for index, (label, key) in enumerate(fields):
            row, col = divmod(index, 3)
            cell = ttk.Frame(form)
            cell.grid(row=row, column=col, sticky="ew", padx=6, pady=5)
            ttk.Label(cell, text=label).pack(anchor="w")
            ttk.Entry(cell, textvariable=self.vars[key], width=28).pack(fill="x")
            form.columnconfigure(col, weight=1)

        buttons = ttk.Frame(form)
        buttons.grid(row=2, column=0, columnspan=3, sticky="w", padx=6, pady=(8, 0))
        ttk.Button(buttons, text="Add Book", command=self.add_selected).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Update Selected", command=self.update_selected).pack(side="left", padx=6)
        ttk.Button(buttons, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=6)
        ttk.Button(buttons, text="Clear Form", command=self.clear_form).pack(side="left", padx=6)

        search_bar = ttk.Frame(self)
        search_bar.pack(fill="x", pady=(0, 8))
        ttk.Label(search_bar, text="Search title, author, or ID:").pack(side="left")
        self.search_var = tk.StringVar()
        ttk.Entry(search_bar, textvariable=self.search_var, width=32).pack(side="left", padx=8)
        self.search_var.trace_add("write", lambda *_: self.refresh_books())
        ttk.Button(search_bar, text="Refresh", command=self.refresh_books).pack(side="left")

        columns = ("book_id", "title", "author", "publisher", "category", "quantity", "available")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=13)
        headings = {
            "book_id": "Book ID", "title": "Title", "author": "Author",
            "publisher": "Publisher", "category": "Category",
            "quantity": "Quantity", "available": "Available",
        }
        widths = {"book_id": 70, "title": 190, "author": 150, "publisher": 130,
                  "category": 120, "quantity": 80, "available": 80}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _form_values(self):
        try:
            quantity = int(self.vars["quantity"].get())
            if quantity < 0:
                raise ValueError
        except ValueError:
            raise ValueError("Quantity must be a whole number greater than or equal to zero.")
        return (
            self.vars["title"].get(), self.vars["author"].get(),
            self.vars["publisher"].get(), self.vars["category"].get(), quantity
        )

    def add_selected(self):
        try:
            values = self._form_values()
            book_id = add_book(*values[:4], quantity=values[4])
            self.refresh_books()
            self.clear_form()
            messagebox.showinfo("Success", f"Book added successfully. Book ID: {book_id}", parent=self)
        except Exception as exc:
            messagebox.showerror("Unable to add book", str(exc), parent=self)

    def update_selected(self):
        if self.selected_book_id is None:
            messagebox.showwarning("Select a book", "Select a book from the table first.", parent=self)
            return
        try:
            values = self._form_values()
            update_book(self.selected_book_id, *values[:4], quantity=values[4])
            self.refresh_books()
            self.clear_form()
            messagebox.showinfo("Success", "Book updated successfully.", parent=self)
        except Exception as exc:
            messagebox.showerror("Unable to update book", str(exc), parent=self)

    def delete_selected(self):
        if self.selected_book_id is None:
            messagebox.showwarning("Select a book", "Select a book from the table first.", parent=self)
            return
        if not messagebox.askyesno("Confirm deletion", "Delete the selected book?", parent=self):
            return
        try:
            delete_book(self.selected_book_id)
            self.refresh_books()
            self.clear_form()
            messagebox.showinfo("Success", "Book deleted successfully.", parent=self)
        except Exception as exc:
            messagebox.showerror("Unable to delete book", str(exc), parent=self)

    def refresh_books(self):
        if not hasattr(self, "tree"):
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        for book in get_books(self.search_var.get() if hasattr(self, "search_var") else ""):
            self.tree.insert("", "end", values=(
                book["book_id"], book["title"], book["author"], book["publisher"],
                book["category"], book["quantity"], book["available"]
            ))

    def _on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        self.selected_book_id = int(values[0])
        book = get_book_safe(self.selected_book_id)
        if book:
            for key in self.vars:
                self.vars[key].set(str(book[key]) if key == "quantity" else (book[key] or ""))

    def clear_form(self):
        self.selected_book_id = None
        for key, var in self.vars.items():
            var.set("1" if key == "quantity" else "")
        if hasattr(self, "tree"):
            for item in self.tree.selection():
                self.tree.selection_remove(item)


def get_book_safe(book_id):
    from database import get_book
    return get_book(book_id)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Library Management System - Book Management")
    root.geometry("1050x650")
    try:
        BookManagementFrame(root).pack(fill="both", expand=True)
    except Exception as exc:
        messagebox.showerror("Database connection error", str(exc), parent=root)
        root.destroy()
    else:
        root.mainloop()
