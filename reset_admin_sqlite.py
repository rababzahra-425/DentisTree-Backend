"""
Reset admin password directly in SQLite (no MongoDB required).
Run: python reset_admin_sqlite.py
"""
import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db.sqlite3")
USERNAME = "admin"
PASSWORD = "admin123"


def main():
    if not os.path.isfile(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        sys.exit(1)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
    import django

    django.setup()
    from django.contrib.auth.hashers import make_password

    hashed = make_password(PASSWORD)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM auth_user WHERE username = ?", (USERNAME,))
    row = cur.fetchone()

    if row:
        cur.execute(
            "UPDATE auth_user SET password = ?, is_active = 1, is_staff = 1, is_superuser = 1 WHERE username = ?",
            (hashed, USERNAME),
        )
        print(f"Updated user '{USERNAME}'.")
    else:
        cur.execute(
            """INSERT INTO auth_user
               (password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined)
               VALUES (?, NULL, 1, ?, '', '', 'admin@dentistree.pk', 1, 1, datetime('now'))""",
            (hashed, USERNAME),
        )
        print(f"Created user '{USERNAME}'.")

    conn.commit()
    conn.close()
    print(f"\nSign in with:\n  Username: {USERNAME}\n  Password: {PASSWORD}\n")


if __name__ == "__main__":
    main()
