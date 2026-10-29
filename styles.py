"""Shared Tkinter theme helpers."""
from tkinter import ttk


def apply_theme(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("TButton", padding=(10, 6), font=("Segoe UI", 9))
    style.configure("TLabel", font=("Segoe UI", 10))
    style.configure("Treeview", rowheight=27, font=("Segoe UI", 9))
    style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
    style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
