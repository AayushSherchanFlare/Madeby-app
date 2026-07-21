from app.database import database_cursor


def dashboard_metrics():
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_users,
                SUM(
                    account_status = 'active'
                    AND (suspended_until IS NULL OR suspended_until <= UTC_TIMESTAMP())
                    AND last_seen_at >= UTC_TIMESTAMP() - INTERVAL 5 MINUTE
                ) AS online_users,
                SUM(
                    account_status <> 'active'
                    OR suspended_until > UTC_TIMESTAMP()
                    OR last_seen_at IS NULL
                    OR last_seen_at < UTC_TIMESTAMP() - INTERVAL 5 MINUTE
                ) AS offline_users,
                SUM(suspended_until > UTC_TIMESTAMP()) AS suspended_users
            FROM users
            WHERE role = 'user'
            """
        )
        metrics = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) AS total_posts FROM projects")
        metrics["total_posts"] = cursor.fetchone()["total_posts"]
        cursor.execute(
            "SELECT COUNT(*) AS pending FROM pending_registrations"
        )
        metrics["pending_registrations"] = cursor.fetchone()["pending"]
        return metrics


def list_users(search=None, limit=100):
    pattern = f"%{search}%" if search else None
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT u.user_id, u.full_name, u.username, u.email, u.profile_image,
                   u.account_status, u.suspended_until, u.last_seen_at,
                   u.created_at, u.email_verified,
                   (SELECT COUNT(*) FROM projects p
                    WHERE p.user_id = u.user_id) AS post_count,
                   (
                       u.account_status = 'active'
                       AND (u.suspended_until IS NULL OR u.suspended_until <= UTC_TIMESTAMP())
                       AND u.last_seen_at >= UTC_TIMESTAMP() - INTERVAL 5 MINUTE
                   ) AS is_online
            FROM users u
            WHERE u.role = 'user'
              AND (
                  %s IS NULL
                  OR u.full_name LIKE %s
                  OR u.username LIKE %s
                  OR u.email LIKE %s
              )
            ORDER BY is_online DESC, u.created_at DESC
            LIMIT %s
            """,
            (pattern, pattern, pattern, pattern, limit),
        )
        return cursor.fetchall()


def list_posts(search=None, limit=100):
    pattern = f"%{search}%" if search else None
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT p.project_id, p.user_id, p.description, p.cover_image,
                   p.status, p.created_at, u.full_name, u.username, u.email,
                   (SELECT COUNT(*) FROM likes l
                    WHERE l.project_id = p.project_id) AS like_count,
                   (SELECT COUNT(*) FROM comments c
                    WHERE c.project_id = p.project_id) AS comment_count
            FROM projects p
            JOIN users u ON u.user_id = p.user_id
            WHERE (
                %s IS NULL
                OR p.description LIKE %s
                OR u.full_name LIKE %s
                OR u.username LIKE %s
                OR u.email LIKE %s
            )
            ORDER BY p.created_at DESC
            LIMIT %s
            """,
            (pattern, pattern, pattern, pattern, pattern, limit),
        )
        return cursor.fetchall()


def recent_users(limit=6):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, full_name, username, email, created_at
            FROM users
            WHERE role = 'user'
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()


def recent_audit_logs(limit=12):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT a.audit_id, a.action_type, a.details, a.created_at,
                   admin.full_name AS admin_name
            FROM admin_audit_logs a
            LEFT JOIN users admin ON admin.user_id = a.admin_user_id
            ORDER BY a.created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()


def find_manageable_user(user_id):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, full_name, username, email, role, account_status,
                   suspended_until, profile_image, cover_image
            FROM users
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        return cursor.fetchone()


def suspend_user(admin_user_id, user_id, suspended_until, details):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE users
            SET suspended_until = %s
            WHERE user_id = %s AND role = 'user'
            """,
            (suspended_until, user_id),
        )
        if cursor.rowcount:
            cursor.execute(
                """
                INSERT INTO admin_audit_logs (
                    admin_user_id, action_type, target_user_id, details
                )
                VALUES (%s, 'suspend_user', %s, %s)
                """,
                (admin_user_id, user_id, details),
            )
        return cursor.rowcount == 1


def unsuspend_user(admin_user_id, user_id, details):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE users
            SET suspended_until = NULL
            WHERE user_id = %s AND role = 'user'
            """,
            (user_id,),
        )
        if cursor.rowcount:
            cursor.execute(
                """
                INSERT INTO admin_audit_logs (
                    admin_user_id, action_type, target_user_id, details
                )
                VALUES (%s, 'unsuspend_user', %s, %s)
                """,
                (admin_user_id, user_id, details),
            )
        return cursor.rowcount == 1


def send_warning(admin_user_id, user_id, message):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO notifications (
                recipient_user_id, sender_user_id, notification_type,
                related_project_id, message_text
            )
            VALUES (%s, %s, 'admin_message', NULL, %s)
            """,
            (user_id, admin_user_id, message),
        )
        cursor.execute(
            """
            INSERT INTO admin_audit_logs (
                admin_user_id, action_type, target_user_id, details
            )
            VALUES (%s, 'send_warning', %s, %s)
            """,
            (admin_user_id, user_id, message),
        )


def delete_user(admin_user_id, user_id, details):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            "SELECT cover_image FROM projects WHERE user_id = %s",
            (user_id,),
        )
        images = [row["cover_image"] for row in cursor.fetchall() if row["cover_image"]]
        cursor.execute(
            """
            INSERT INTO admin_audit_logs (
                admin_user_id, action_type, target_user_id, details
            )
            VALUES (%s, 'delete_user', %s, %s)
            """,
            (admin_user_id, user_id, details),
        )
        cursor.execute(
            "DELETE FROM users WHERE user_id = %s AND role = 'user'",
            (user_id,),
        )
        return cursor.rowcount == 1, images


def delete_post(admin_user_id, project_id):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT p.project_id, p.user_id, p.cover_image, u.username
            FROM projects p
            JOIN users u ON u.user_id = p.user_id
            WHERE p.project_id = %s
            LIMIT 1
            """,
            (project_id,),
        )
        post = cursor.fetchone()
        if not post:
            return None
        cursor.execute(
            """
            INSERT INTO admin_audit_logs (
                admin_user_id, action_type, target_user_id,
                target_project_id, details
            )
            VALUES (%s, 'delete_post', %s, %s, %s)
            """,
            (
                admin_user_id,
                post["user_id"],
                project_id,
                f"Deleted post {project_id} by @{post['username']}",
            ),
        )
        cursor.execute("DELETE FROM projects WHERE project_id = %s", (project_id,))
        return post
