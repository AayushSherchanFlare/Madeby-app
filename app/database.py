from contextlib import contextmanager

import mysql.connector
from flask import current_app
from mysql.connector import Error


def get_connection():
    """Return a new MySQL connection using environment-backed configuration."""
    try:
        return mysql.connector.connect(
            host=current_app.config["MYSQL_HOST"],
            port=current_app.config["MYSQL_PORT"],
            user=current_app.config["MYSQL_USER"],
            password=current_app.config["MYSQL_PASSWORD"],
            database=current_app.config["MYSQL_DATABASE"],
            charset="utf8mb4",
            use_unicode=True,
            autocommit=False,
        )
    except Error:
        current_app.logger.exception("Could not connect to the MadeBy database")
        raise


@contextmanager
def database_cursor(dictionary=True, commit=False):
    """Provide a cursor and reliably close or roll back its connection."""
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=dictionary)
        yield cursor
        if commit:
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            connection.close()
