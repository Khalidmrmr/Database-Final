#!/usr/bin/env python3
"""
Terminal-based Library Management CLI
Demonstrates application-level interaction with the PostgreSQL schema
defined for a two-member group project (5 tables, search feature included).
"""

import psycopg2
from psycopg2 import sql
from datetime import date, timedelta

# --- Configuration: adjust to your environment ---
DB_PARAMS = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "library_db",
    "user":     "your_username",
    "password": "your_password"
}

# --- Database Connection Utility ---

def get_connection():
    return psycopg2.connect(**DB_PARAMS)

# --- Feature Implementations ---

def add_book():
    """Add a new book title and one or more copies."""
    title = input("Book title: ").strip()
    isbn = input("ISBN (13 chars): ").strip()
    year = input("Publication year (YYYY): ").strip()
    genre = input("Genre: ").strip()
    author_name = input("Author name: ").strip()

    # Number of physical copies to create
    try:
        num_copies = int(input("Number of copies to add: ").strip())
        if num_copies < 1:
            raise ValueError
    except ValueError:
        print("Error: please enter a positive integer for copies.")
        return

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Ensure the author exists (or create)
        cur.execute("""
            SELECT author_id FROM author WHERE author_name = %s
        """, (author_name,))
        row = cur.fetchone()
        if row:
            author_id = row[0]
        else:
            cur.execute("""
                INSERT INTO author (author_name)
                VALUES (%s) RETURNING author_id
            """, (author_name,))
            author_id = cur.fetchone()[0]

        # Insert into book
        cur.execute("""
            INSERT INTO book (title, isbn, publication_year, genre, author_id)
            VALUES (%s, %s, %s, %s, %s) RETURNING book_id
        """, (title, isbn, year or None, genre or None, author_id))
        book_id = cur.fetchone()[0]

        # Insert copies
        for _ in range(num_copies):
            cur.execute("""
                INSERT INTO bookcopy (book_id, status)
                VALUES (%s, 'Available')
            """, (book_id,))

        conn.commit()
        print(f"Success: '{title}' added with {num_copies} copies.")
    except Exception as e:
        conn.rollback()
        print("Error adding book:", e)
    finally:
        cur.close()
        conn.close()


def add_member():
    """Register a new library member."""
    name = input("Member name: ").strip()
    address = input("Address: ").strip()
    phone = input("Phone number: ").strip()

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO member (member_name, address, phone_number)
            VALUES (%s, %s, %s) RETURNING member_id
        """, (name, address or None, phone or None))
        member_id = cur.fetchone()[0]
        conn.commit()
        print(f"Success: Member '{name}' registered (ID {member_id}).")
    except Exception as e:
        conn.rollback()
        print("Error registering member:", e)
    finally:
        cur.close()
        conn.close()


def search_books():
    """Search books by title or author and show inventory summary."""
    term = input("Search term (title or author): ").strip()
    conn = get_connection()
    cur = conn.cursor()
    try:
        query = """
        SELECT
            b.book_id,
            b.title,
            a.author_name,
            COUNT(bc.*)           AS total_copies,
            SUM((bc.status = 'Available')::int) AS available_copies
        FROM book b
        LEFT JOIN author a USING (author_id)
        LEFT JOIN bookcopy bc USING (book_id)
        WHERE LOWER(b.title) LIKE LOWER(%s)
           OR LOWER(a.author_name) LIKE LOWER(%s)
        GROUP BY b.book_id, b.title, a.author_name
        ORDER BY b.title
        """
        like_term = f"%{term}%"
        cur.execute(query, (like_term, like_term))
        rows = cur.fetchall()
        if not rows:
            print("No matches found.")
        else:
            print(f"\n{'ID':<4} {'Title':<30} {'Author':<20} {'Owned':>5} {'Avail':>5}")
            print("-" * 70)
            for book_id, title, author, total, avail in rows:
                print(f"{book_id:<4} {title:<30} {author:<20} {total:>5} {avail:>5}")
            print()
    except Exception as e:
        print("Error during search:", e)
    finally:
        cur.close()
        conn.close()


def checkout_book():
    """Check out an available copy for a member."""
    try:
        member_id = int(input("Member ID: ").strip())
    except ValueError:
        print("Error: invalid member ID.")
        return

    title = input("Book title to check out: ").strip()
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Find an available copy for that title
        cur.execute("""
            SELECT bc.copy_id
            FROM bookcopy bc
            JOIN book b ON bc.book_id = b.book_id
            WHERE b.title = %s
              AND bc.status = 'Available'
            LIMIT 1
        """, (title,))
        row = cur.fetchone()
        if not row:
            print("Error: no available copy found for that title.")
            return

        copy_id = row[0]
        today = date.today()
        due = today + timedelta(days=21)

        # Insert loan record
        cur.execute("""
            INSERT INTO loan (copy_id, member_id, date_borrowed, due_date)
            VALUES (%s, %s, %s, %s)
        """, (copy_id, member_id, today, due))

        # Update copy status
        cur.execute("""
            UPDATE bookcopy
            SET status = 'On Loan'
            WHERE copy_id = %s
        """, (copy_id,))

        conn.commit()
        print(f"Checkout successful: copy {copy_id} due on {due}.")
    except Exception as e:
        conn.rollback()
        print("Error during checkout:", e)
    finally:
        cur.close()
        conn.close()


def return_book():
    """Return a borrowed copy."""
    try:
        copy_id = int(input("Copy ID to return: ").strip())
    except ValueError:
        print("Error: invalid copy ID.")
        return

    conn = get_connection()
    cur = conn.cursor()
    try:
        today = date.today()
        # Update loan record
        cur.execute("""
            UPDATE loan
            SET date_returned = %s
            WHERE copy_id = %s
              AND date_returned IS NULL
        """, (today, copy_id))

        if cur.rowcount == 0:
            print("Error: no active loan found for that copy.")
            conn.rollback()
            return

        # Update copy status
        cur.execute("""
            UPDATE bookcopy
            SET status = 'Available'
            WHERE copy_id = %s
        """, (copy_id,))

        conn.commit()
        print(f"Return processed: copy {copy_id} is now available.")
    except Exception as e:
        conn.rollback()
        print("Error during return:", e)
    finally:
        cur.close()
        conn.close()


def overdue_report():
    """Generate a list of all currently overdue loans."""
    today = date.today()
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT
                l.loan_id,
                b.title,
                m.member_name,
                l.due_date
            FROM loan l
            JOIN bookcopy bc ON l.copy_id = bc.copy_id
            JOIN book b ON bc.book_id = b.book_id
            JOIN member m ON l.member_id = m.member_id
            WHERE l.date_returned IS NULL
              AND l.due_date < %s
            ORDER BY l.due_date
        """, (today,))
        rows = cur.fetchall()
        if not rows:
            print("No overdue loans.")
        else:
            print(f"\n{'LoanID':<6} {'Title':<30} {'Member':<20} {'Due Date':>10}")
            print("-" * 70)
            for loan_id, title, member, due in rows:
                print(f"{loan_id:<6} {title:<30} {member:<20} {due:%Y-%m-%d}")
            print()
    except Exception as e:
        print("Error generating report:", e)
    finally:
        cur.close()
        conn.close()


# --- Main CLI Loop ---

def main():
    MENU = {
        "1": ("Add new book & copies", add_book),
        "2": ("Register new member", add_member),
        "3": ("Search books", search_books),
        "4": ("Check out a book copy", checkout_book),
        "5": ("Return a book copy", return_book),
        "6": ("Overdue report", overdue_report),
        "7": ("Exit", None)
    }

    while True:
        print("\nLibrary Management CLI")
        print("-" * 25)
        for key, (desc, _) in MENU.items():
            print(f"{key}. {desc}")
        choice = input("Choose an option: ").strip()

        if choice == "7":
            print("Goodbye.")
            break
        action = MENU.get(choice)
        if action:
            action[1]()  # call the function
        else:
            print("Invalid choice; please enter 1–7.")


if __name__ == "__main__":
    main()
