"""MySQL database layer for the Library Management System.

Install dependencies: pip install -r requirements.txt
Configure credentials with environment variables or edit the defaults below.
The database itself is created automatically if the MySQL account has permission.
"""
import os
from contextlib import contextmanager
import mysql.connector
from mysql.connector import Error

DB_HOST = os.getenv("LIBRARY_DB_HOST", "localhost")
DB_PORT = int(os.getenv("LIBRARY_DB_PORT", "3306"))
DB_USER = os.getenv("LIBRARY_DB_USER", "root")
DB_PASSWORD = os.getenv("LIBRARY_DB_PASSWORD", "")
DB_NAME = os.getenv("LIBRARY_DB_NAME", "library_management")


def _connect_server():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def init_db():
    """Create database and shared tables if they do not already exist."""
    conn = _connect_server()
    cursor = conn.cursor()
    try:
        # Database identifiers cannot be parameterized; validate our configured name.
        if not DB_NAME.replace("_", "").isalnum():
            raise ValueError("Database name may contain only letters, numbers, and underscores.")
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    finally:
        cursor.close()
        conn.close()

    conn = mysql.connector.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, database=DB_NAME
    )
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                book_id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                author VARCHAR(255) NOT NULL,
                publisher VARCHAR(255) NOT NULL DEFAULT '',
                category VARCHAR(120) NOT NULL DEFAULT '',
                quantity INT NOT NULL DEFAULT 1,
                available INT NOT NULL DEFAULT 1,
                CONSTRAINT chk_books_quantity CHECK (quantity >= 0),
                CONSTRAINT chk_books_available CHECK (available >= 0 AND available <= quantity)
            ) ENGINE=InnoDB
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                department VARCHAR(150) NOT NULL DEFAULT '',
                phone VARCHAR(40) NOT NULL DEFAULT '',
                email VARCHAR(255) NOT NULL DEFAULT ''
            ) ENGINE=InnoDB
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                book_id INT NOT NULL,
                student_id INT NOT NULL,
                issue_date DATE NOT NULL,
                due_date DATE NOT NULL,
                return_date DATE NULL,
                status ENUM('Issued', 'Returned') NOT NULL DEFAULT 'Issued',
                CONSTRAINT fk_transactions_book FOREIGN KEY (book_id)
                    REFERENCES books(book_id),
                CONSTRAINT fk_transactions_student FOREIGN KEY (student_id)
                    REFERENCES students(student_id)
            ) ENGINE=InnoDB
        """)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


@contextmanager
def get_connection():
    """Yield a connected cursor and commit on success, rollback on failure."""
    conn = mysql.connector.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, database=DB_NAME
    )
    cursor = conn.cursor(dictionary=True)
    try:
        yield conn, cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def _validate_book(title, author, quantity):
    title = str(title).strip()
    author = str(author).strip()
    if not title:
        raise ValueError("Book title is required.")
    if not author:
        raise ValueError("Author name is required.")
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        raise ValueError("Quantity must be a whole number.") from None
    if quantity < 0:
        raise ValueError("Quantity cannot be negative.")
    return title, author, quantity


def add_book(title, author, publisher="", category="", quantity=1):
    title, author, quantity = _validate_book(title, author, quantity)
    with get_connection() as (conn, cursor):
        cursor.execute(
            """INSERT INTO books
               (title, author, publisher, category, quantity, available)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (title, author, str(publisher).strip(), str(category).strip(),
             quantity, quantity),
        )
        return cursor.lastrowid


def get_books(search=""):
    search = str(search).strip()
    with get_connection() as (_conn, cursor):
        if search:
            like = f"%{search}%"
            cursor.execute(
                """SELECT * FROM books
                   WHERE title LIKE %s OR author LIKE %s OR CAST(book_id AS CHAR) LIKE %s
                   ORDER BY book_id DESC""",
                (like, like, like),
            )
        else:
            cursor.execute("SELECT * FROM books ORDER BY book_id DESC")
        return cursor.fetchall()


def get_book(book_id):
    with get_connection() as (_conn, cursor):
        cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
        return cursor.fetchone()


def update_book(book_id, title, author, publisher="", category="", quantity=1):
    title, author, quantity = _validate_book(title, author, quantity)
    with get_connection() as (conn, cursor):
        cursor.execute(
            "SELECT quantity, available FROM books WHERE book_id = %s FOR UPDATE",
            (book_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError("Book not found.")
        issued_count = row["quantity"] - row["available"]
        if quantity < issued_count:
            raise ValueError(
                f"Quantity cannot be less than {issued_count} copies currently issued."
            )
        available = quantity - issued_count
        cursor.execute(
            """UPDATE books
               SET title=%s, author=%s, publisher=%s, category=%s, quantity=%s, available=%s
               WHERE book_id=%s""",
            (title, author, str(publisher).strip(), str(category).strip(),
             quantity, available, book_id),
        )


def delete_book(book_id):
    with get_connection() as (conn, cursor):
        cursor.execute("SELECT book_id FROM books WHERE book_id=%s", (book_id,))
        if cursor.fetchone() is None:
            raise ValueError("Book not found.")
        cursor.execute(
            "SELECT 1 AS found FROM transactions WHERE book_id=%s LIMIT 1", (book_id,)
        )
        if cursor.fetchone():
            raise ValueError("This book has transaction history and cannot be deleted.")
        cursor.execute("DELETE FROM books WHERE book_id=%s", (book_id,))


def get_book_summary():
    with get_connection() as (_conn, cursor):
        cursor.execute("""
            SELECT
                COALESCE(SUM(quantity), 0) AS total_copies,
                COALESCE(SUM(available), 0) AS available_copies,
                COALESCE(SUM(quantity - available), 0) AS issued_copies,
                COUNT(*) AS title_count
            FROM books
        """)
        return cursor.fetchone()


def get_categories():
    with get_connection() as (_conn, cursor):
        cursor.execute(
            "SELECT DISTINCT category FROM books WHERE category <> '' ORDER BY category"
        )
        return [row["category"] for row in cursor.fetchall()]


if __name__ == "__main__":
    try:
        init_db()
        print(f"MySQL database '{DB_NAME}' and shared tables are ready.")
    except Error as exc:
        print("Could not initialize MySQL.")
        print("Check that MySQL Server is running and your credentials are correct.")
        print(f"MySQL error: {exc}")
