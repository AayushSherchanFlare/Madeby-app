from app.database import database_cursor


def find_by_email(email):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, full_name, password_hash, role, account_status
            FROM users
            WHERE email = %s
            LIMIT 1
            """,
            (email,),
        )
        return cursor.fetchone()


def find_by_id(user_id):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, full_name, username, email, role, account_status
            FROM users
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        return cursor.fetchone()


def find_registration_conflicts(username, email):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT username, email
            FROM users
            WHERE username = %s OR email = %s
            """,
            (username, email),
        )
        return cursor.fetchall()


def create_user(full_name, username, email, password_hash):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO users (full_name, username, email, password_hash)
            VALUES (%s, %s, %s, %s)
            """,
            (full_name, username, email, password_hash),
        )
        return cursor.lastrowid
