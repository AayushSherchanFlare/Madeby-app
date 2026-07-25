from app.database import database_cursor


def find_by_email(email):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, full_name, password_hash, role, account_status,
                   suspended_until
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
            SELECT user_id, full_name, username, email, role, account_status,
                   profession, biography, website_url, profile_image, cover_image,
                   suspended_until, last_seen_at,
                   (SELECT COUNT(*) FROM notifications n
                    WHERE n.recipient_user_id = users.user_id
                      AND n.is_read = FALSE) AS unread_notification_count
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


def find_pending_conflicts(username, email):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT username, email
            FROM pending_registrations
            WHERE username = %s OR email = %s
            """,
            (username, email),
        )
        return cursor.fetchall()


def save_pending_registration(
    full_name,
    username,
    email,
    password_hash,
    code_hash,
    expires_at,
    resend_available_at,
):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            "DELETE FROM pending_registrations WHERE expires_at < UTC_TIMESTAMP()"
        )
        cursor.execute(
            """
            INSERT INTO pending_registrations (
                full_name, username, email, password_hash, code_hash,
                expires_at, resend_available_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                full_name = VALUES(full_name),
                username = VALUES(username),
                password_hash = VALUES(password_hash),
                code_hash = VALUES(code_hash),
                expires_at = VALUES(expires_at),
                attempts = 0,
                resend_available_at = VALUES(resend_available_at)
            """,
            (
                full_name,
                username,
                email,
                password_hash,
                code_hash,
                expires_at,
                resend_available_at,
            ),
        )


def find_pending_by_email(email):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT verification_id, full_name, username, email, password_hash,
                   code_hash, expires_at, attempts, resend_available_at
            FROM pending_registrations
            WHERE email = %s
            LIMIT 1
            """,
            (email,),
        )
        return cursor.fetchone()


def update_pending_code(email, code_hash, expires_at, resend_available_at):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE pending_registrations
            SET code_hash = %s, expires_at = %s, attempts = 0,
                resend_available_at = %s
            WHERE email = %s
            """,
            (code_hash, expires_at, resend_available_at, email),
        )
        return cursor.rowcount == 1


def record_verification_attempt(email):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE pending_registrations
            SET attempts = LEAST(attempts + 1, 255)
            WHERE email = %s
            """,
            (email,),
        )


def complete_pending_registration(email, expected_code_hash):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT full_name, username, email, password_hash, code_hash
            FROM pending_registrations
            WHERE email = %s
            FOR UPDATE
            """,
            (email,),
        )
        pending = cursor.fetchone()
        if not pending or pending["code_hash"] != expected_code_hash:
            return None
        cursor.execute(
            """
            INSERT INTO users (
                full_name, username, email, password_hash, email_verified
            )
            VALUES (%s, %s, %s, %s, TRUE)
            """,
            (
                pending["full_name"],
                pending["username"],
                pending["email"],
                pending["password_hash"],
            ),
        )
        user_id = cursor.lastrowid
        cursor.execute(
            "DELETE FROM pending_registrations WHERE email = %s",
            (email,),
        )
        return user_id


def delete_pending_registration(email):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            "DELETE FROM pending_registrations WHERE email = %s",
            (email,),
        )


def find_password_reset_by_email(email):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT pr.reset_id, pr.user_id, pr.code_hash, pr.expires_at,
                   pr.attempts, pr.resend_available_at
            FROM password_reset_requests pr
            JOIN users u ON u.user_id = pr.user_id
            WHERE u.email = %s
            LIMIT 1
            """,
            (email,),
        )
        return cursor.fetchone()


def save_password_reset(user_id, code_hash, expires_at, resend_available_at):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            "DELETE FROM password_reset_requests WHERE expires_at < UTC_TIMESTAMP()"
        )
        cursor.execute(
            """
            INSERT INTO password_reset_requests (
                user_id, code_hash, expires_at, resend_available_at
            )
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                code_hash = VALUES(code_hash),
                expires_at = VALUES(expires_at),
                attempts = 0,
                resend_available_at = VALUES(resend_available_at)
            """,
            (user_id, code_hash, expires_at, resend_available_at),
        )


def update_password_reset_code(
    user_id, code_hash, expires_at, resend_available_at
):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE password_reset_requests
            SET code_hash = %s, expires_at = %s, attempts = 0,
                resend_available_at = %s
            WHERE user_id = %s
            """,
            (code_hash, expires_at, resend_available_at, user_id),
        )
        return cursor.rowcount == 1


def record_password_reset_attempt(user_id):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE password_reset_requests
            SET attempts = LEAST(attempts + 1, 255)
            WHERE user_id = %s
            """,
            (user_id,),
        )


def delete_password_reset(user_id):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            "DELETE FROM password_reset_requests WHERE user_id = %s",
            (user_id,),
        )


def complete_password_reset(email, expected_code_hash, password_hash):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT pr.user_id, pr.code_hash
            FROM password_reset_requests pr
            JOIN users u ON u.user_id = pr.user_id
            WHERE u.email = %s
            FOR UPDATE
            """,
            (email,),
        )
        pending = cursor.fetchone()
        if not pending or pending["code_hash"] != expected_code_hash:
            return False
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE user_id = %s",
            (password_hash, pending["user_id"]),
        )
        cursor.execute(
            "DELETE FROM password_reset_requests WHERE user_id = %s",
            (pending["user_id"],),
        )
        return True


def find_by_google_subject(subject):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, full_name, role, account_status, suspended_until
            FROM users
            WHERE google_subject = %s
            LIMIT 1
            """,
            (subject,),
        )
        return cursor.fetchone()


def username_exists(username):
    with database_cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM users WHERE username = %s LIMIT 1",
            (username,),
        )
        return cursor.fetchone() is not None


def link_google_identity(user_id, subject):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE users
            SET google_subject = %s, email_verified = TRUE
            WHERE user_id = %s
            """,
            (subject, user_id),
        )


def create_google_user(full_name, username, email, password_hash, subject):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO users (
                full_name, username, email, password_hash, google_subject,
                email_verified
            )
            VALUES (%s, %s, %s, %s, %s, TRUE)
            """,
            (full_name, username, email, password_hash, subject),
        )
        return cursor.lastrowid


def touch_last_seen(user_id):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE users
            SET last_seen_at = UTC_TIMESTAMP()
            WHERE user_id = %s
              AND (
                  last_seen_at IS NULL
                  OR last_seen_at < UTC_TIMESTAMP() - INTERVAL 1 MINUTE
              )
            """,
            (user_id,),
        )
