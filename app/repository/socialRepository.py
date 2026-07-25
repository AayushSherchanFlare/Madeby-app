from app.database import database_cursor


def list_categories():
    with database_cursor() as cursor:
        cursor.execute(
            "SELECT category_id, category_name FROM categories ORDER BY category_name"
        )
        return cursor.fetchall()


def list_feed(user_id, limit=20, offset=0, category_id=None):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT p.project_id, p.user_id, p.title, p.description, p.cover_image,
                   p.created_at, p.status, u.full_name, u.username, u.profession,
                   u.profile_image, c.category_name,
                   (SELECT COUNT(*) FROM likes l
                    WHERE l.project_id = p.project_id) AS like_count,
                   (SELECT COUNT(*) FROM comments cm
                    WHERE cm.project_id = p.project_id) AS comment_count,
                   EXISTS(
                       SELECT 1 FROM likes mine
                       WHERE mine.project_id = p.project_id AND mine.user_id = %s
                   ) AS liked_by_user,
                   EXISTS(
                       SELECT 1 FROM saved_posts saved
                       WHERE saved.project_id = p.project_id AND saved.user_id = %s
                   ) AS saved_by_user
            FROM projects p
            JOIN users u ON u.user_id = p.user_id
            LEFT JOIN categories c ON c.category_id = p.category_id
            WHERE p.status = 'published'
              AND u.account_status = 'active'
              AND (%s IS NULL OR p.category_id = %s)
            ORDER BY
                CASE
                    WHEN p.user_id = %s THEN 2
                    WHEN EXISTS (
                        SELECT 1 FROM followers f
                        WHERE f.follower_user_id = %s
                          AND f.followed_user_id = p.user_id
                    ) THEN 0
                    ELSE 1
                END,
                p.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (
                user_id,
                user_id,
                category_id,
                category_id,
                user_id,
                user_id,
                limit,
                offset,
            ),
        )
        return cursor.fetchall()


def comments_for_projects(project_ids, per_project=3):
    if not project_ids:
        return {}
    placeholders = ", ".join(["%s"] * len(project_ids))
    with database_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT project_id, comment_id, user_id, full_name, username,
                   profile_image, comment_text, created_at
            FROM (
                SELECT cm.project_id, cm.comment_id, cm.user_id, u.full_name,
                       u.username, u.profile_image, cm.comment_text, cm.created_at,
                       ROW_NUMBER() OVER (
                           PARTITION BY cm.project_id
                           ORDER BY cm.created_at DESC
                       ) AS comment_position
                FROM comments cm
                JOIN users u ON u.user_id = cm.user_id
                WHERE cm.project_id IN ({placeholders})
                  AND u.account_status = 'active'
            ) ranked
            WHERE comment_position <= %s
            ORDER BY project_id, created_at
            """,
            (*project_ids, per_project),
        )
        grouped = {project_id: [] for project_id in project_ids}
        for comment in cursor.fetchall():
            grouped[comment["project_id"]].append(comment)
        return grouped


def suggested_users(user_id, limit=4):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT u.user_id, u.full_name, u.username, u.profession, u.profile_image,
                   EXISTS(
                       SELECT 1 FROM followers outgoing
                       WHERE outgoing.follower_user_id = %s
                         AND outgoing.followed_user_id = u.user_id
                   ) AS followed_by_viewer,
                   EXISTS(
                       SELECT 1 FROM followers incoming
                       WHERE incoming.follower_user_id = u.user_id
                         AND incoming.followed_user_id = %s
                   ) AS follows_viewer
            FROM users u
            WHERE u.user_id <> %s
              AND u.account_status = 'active'
            ORDER BY
                CASE
                    WHEN EXISTS (
                        SELECT 1 FROM followers incoming
                        WHERE incoming.follower_user_id = u.user_id
                          AND incoming.followed_user_id = %s
                    ) AND NOT EXISTS (
                        SELECT 1 FROM followers outgoing
                        WHERE outgoing.follower_user_id = %s
                          AND outgoing.followed_user_id = u.user_id
                    ) THEN 0
                    ELSE 1
                END,
                RAND()
            LIMIT %s
            """,
            (user_id, user_id, user_id, user_id, user_id, limit),
        )
        return cursor.fetchall()


def notifications_for_user(user_id, limit=50):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT n.notification_id, n.notification_type, n.related_project_id,
                   n.message_text, n.is_read, n.created_at, n.sender_user_id,
                   COALESCE(sender.full_name, 'Someone') AS sender_name,
                   sender.username AS sender_username,
                   sender.profile_image AS sender_profile_image,
                   EXISTS(
                       SELECT 1 FROM followers mine
                       WHERE mine.follower_user_id = n.recipient_user_id
                         AND mine.followed_user_id = n.sender_user_id
                   ) AS followed_by_viewer,
                   EXISTS(
                       SELECT 1 FROM followers theirs
                       WHERE theirs.follower_user_id = n.sender_user_id
                         AND theirs.followed_user_id = n.recipient_user_id
                   ) AS follows_viewer
            FROM notifications n
            LEFT JOIN users sender ON sender.user_id = n.sender_user_id
            WHERE n.recipient_user_id = %s
            ORDER BY n.created_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        return cursor.fetchall()


def mark_notifications_read(user_id):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE notifications
            SET is_read = TRUE
            WHERE recipient_user_id = %s AND is_read = FALSE
            """,
            (user_id,),
        )


def post_engagement_counts(project_id):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM likes WHERE project_id = %s) AS like_count,
                (SELECT COUNT(*) FROM comments WHERE project_id = %s) AS comment_count
            """,
            (project_id, project_id),
        )
        return cursor.fetchone()


def create_post(user_id, content, image_path, category_id):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO projects (
                user_id, category_id, title, description, cover_image, status
            )
            VALUES (%s, %s, NULL, %s, %s, 'published')
            """,
            (user_id, category_id or None, content or None, image_path),
        )
        return cursor.lastrowid


def find_post_for_management(project_id, user_id):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT project_id, user_id, category_id, title, description,
                   cover_image, status, created_at, updated_at
            FROM projects
            WHERE project_id = %s AND user_id = %s
            LIMIT 1
            """,
            (project_id, user_id),
        )
        return cursor.fetchone()


def find_visible_post(project_id, viewer_id):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT p.project_id, p.user_id, p.title, p.description, p.cover_image,
                   p.status, p.created_at, u.full_name, u.username, u.profession,
                   u.profile_image, c.category_name,
                   (SELECT COUNT(*) FROM likes l
                    WHERE l.project_id = p.project_id) AS like_count,
                   (SELECT COUNT(*) FROM comments cm
                    WHERE cm.project_id = p.project_id) AS comment_count,
                   EXISTS(
                       SELECT 1 FROM likes mine
                       WHERE mine.project_id = p.project_id AND mine.user_id = %s
                   ) AS liked_by_user,
                   EXISTS(
                       SELECT 1 FROM saved_posts saved
                       WHERE saved.project_id = p.project_id AND saved.user_id = %s
                   ) AS saved_by_user
            FROM projects p
            JOIN users u ON u.user_id = p.user_id
            LEFT JOIN categories c ON c.category_id = p.category_id
            WHERE p.project_id = %s
              AND u.account_status = 'active'
              AND (
                  p.status = 'published'
                  OR (p.status = 'hidden' AND p.user_id = %s)
              )
            LIMIT 1
            """,
            (viewer_id, viewer_id, project_id, viewer_id),
        )
        return cursor.fetchone()


def update_post(project_id, user_id, content, image_path, category_id):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE projects
            SET description = %s,
                cover_image = COALESCE(%s, cover_image),
                category_id = %s
            WHERE project_id = %s AND user_id = %s
            """,
            (content or None, image_path, category_id or None, project_id, user_id),
        )
        return cursor.rowcount == 1


def delete_post(project_id, user_id):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            "DELETE FROM projects WHERE project_id = %s AND user_id = %s",
            (project_id, user_id),
        )
        return cursor.rowcount == 1


def set_post_visibility(project_id, user_id, status):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE projects
            SET status = %s
            WHERE project_id = %s AND user_id = %s
            """,
            (status, project_id, user_id),
        )
        return cursor.rowcount == 1


def toggle_saved_post(user_id, project_id):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT saved_post_id
            FROM saved_posts
            WHERE user_id = %s AND project_id = %s
            """,
            (user_id, project_id),
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                "DELETE FROM saved_posts WHERE saved_post_id = %s",
                (existing["saved_post_id"],),
            )
            return False
        cursor.execute(
            "INSERT INTO saved_posts (user_id, project_id) VALUES (%s, %s)",
            (user_id, project_id),
        )
        return True


def toggle_like(user_id, project_id):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            "SELECT like_id FROM likes WHERE user_id = %s AND project_id = %s",
            (user_id, project_id),
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute("DELETE FROM likes WHERE like_id = %s", (existing["like_id"],))
            cursor.execute(
                """
                DELETE FROM notifications
                WHERE recipient_user_id = (
                    SELECT user_id FROM projects WHERE project_id = %s
                )
                  AND sender_user_id = %s
                  AND notification_type = 'like'
                  AND related_project_id = %s
                """,
                (project_id, user_id, project_id),
            )
            return False

        cursor.execute(
            "INSERT INTO likes (user_id, project_id) VALUES (%s, %s)",
            (user_id, project_id),
        )
        cursor.execute("SELECT user_id FROM projects WHERE project_id = %s", (project_id,))
        owner = cursor.fetchone()
        if owner and owner["user_id"] != user_id:
            cursor.execute(
                """
                INSERT INTO notifications (
                    recipient_user_id, sender_user_id, notification_type,
                    related_project_id
                )
                VALUES (%s, %s, 'like', %s)
                """,
                (owner["user_id"], user_id, project_id),
            )
        return True


def add_comment(user_id, project_id, comment_text):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO comments (user_id, project_id, comment_text)
            VALUES (%s, %s, %s)
            """,
            (user_id, project_id, comment_text),
        )
        comment_id = cursor.lastrowid
        cursor.execute("SELECT user_id FROM projects WHERE project_id = %s", (project_id,))
        owner = cursor.fetchone()
        if owner and owner["user_id"] != user_id:
            cursor.execute(
                """
                INSERT INTO notifications (
                    recipient_user_id, sender_user_id, notification_type,
                    related_project_id
                )
                VALUES (%s, %s, 'comment', %s)
                """,
                (owner["user_id"], user_id, project_id),
            )
        return comment_id


def toggle_follow(user_id, target_user_id):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT follow_id FROM followers
            WHERE follower_user_id = %s AND followed_user_id = %s
            """,
            (user_id, target_user_id),
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                "DELETE FROM followers WHERE follow_id = %s",
                (existing["follow_id"],),
            )
            cursor.execute(
                """
                DELETE FROM notifications
                WHERE recipient_user_id = %s
                  AND sender_user_id = %s
                  AND notification_type = 'follow'
                  AND related_project_id IS NULL
                """,
                (target_user_id, user_id),
            )
            return False
        cursor.execute(
            """
            INSERT INTO followers (follower_user_id, followed_user_id)
            VALUES (%s, %s)
            """,
            (user_id, target_user_id),
        )
        cursor.execute(
            """
            INSERT INTO notifications (
                recipient_user_id, sender_user_id, notification_type
            )
            VALUES (%s, %s, 'follow')
            """,
            (target_user_id, user_id),
        )
        return True


def find_profile_by_username(username, viewer_id):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT u.user_id, u.full_name, u.username, u.email, u.biography,
                   u.profession, u.profile_image, u.cover_image, u.website_url,
                   u.created_at,
                   (SELECT COUNT(*) FROM projects p
                    WHERE p.user_id = u.user_id
                      AND (
                          p.status = 'published'
                          OR (p.status = 'hidden' AND u.user_id = %s)
                      )) AS post_count,
                   (SELECT COUNT(*) FROM followers f
                    WHERE f.followed_user_id = u.user_id) AS follower_count,
                   (SELECT COUNT(*) FROM followers f
                    WHERE f.follower_user_id = u.user_id) AS following_count,
                   EXISTS(
                       SELECT 1 FROM followers f
                       WHERE f.follower_user_id = %s
                         AND f.followed_user_id = u.user_id
                   ) AS followed_by_viewer,
                   EXISTS(
                       SELECT 1 FROM followers f
                       WHERE f.follower_user_id = u.user_id
                         AND f.followed_user_id = %s
                   ) AS follows_viewer
            FROM users u
            WHERE u.username = %s AND u.account_status = 'active'
            LIMIT 1
            """,
            (viewer_id, viewer_id, viewer_id, username),
        )
        return cursor.fetchone()


def followers_for_user(user_id, viewer_id):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT u.user_id, u.full_name, u.username, u.profession, u.profile_image,
                   EXISTS(
                       SELECT 1 FROM followers mine
                       WHERE mine.follower_user_id = %s
                         AND mine.followed_user_id = u.user_id
                   ) AS followed_by_viewer,
                   EXISTS(
                       SELECT 1 FROM followers theirs
                       WHERE theirs.follower_user_id = u.user_id
                         AND theirs.followed_user_id = %s
                   ) AS follows_viewer
            FROM followers f
            JOIN users u ON u.user_id = f.follower_user_id
            WHERE f.followed_user_id = %s
              AND u.account_status = 'active'
            ORDER BY u.full_name
            """,
            (viewer_id, viewer_id, user_id),
        )
        return cursor.fetchall()


def following_for_user(user_id, viewer_id):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT u.user_id, u.full_name, u.username, u.profession, u.profile_image,
                   EXISTS(
                       SELECT 1 FROM followers mine
                       WHERE mine.follower_user_id = %s
                         AND mine.followed_user_id = u.user_id
                   ) AS followed_by_viewer,
                   EXISTS(
                       SELECT 1 FROM followers theirs
                       WHERE theirs.follower_user_id = u.user_id
                         AND theirs.followed_user_id = %s
                   ) AS follows_viewer
            FROM followers f
            JOIN users u ON u.user_id = f.followed_user_id
            WHERE f.follower_user_id = %s
              AND u.account_status = 'active'
            ORDER BY u.full_name
            """,
            (viewer_id, viewer_id, user_id),
        )
        return cursor.fetchall()


def posts_by_user(user_id, viewer_id):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT p.project_id, p.user_id, p.title, p.description, p.cover_image,
                   p.created_at, c.category_name,
                   (SELECT COUNT(*) FROM likes l
                    WHERE l.project_id = p.project_id) AS like_count,
                   (SELECT COUNT(*) FROM comments cm
                    WHERE cm.project_id = p.project_id) AS comment_count,
                   EXISTS(
                       SELECT 1 FROM likes mine
                       WHERE mine.project_id = p.project_id AND mine.user_id = %s
                   ) AS liked_by_user,
                   EXISTS(
                       SELECT 1 FROM saved_posts saved
                       WHERE saved.project_id = p.project_id AND saved.user_id = %s
                   ) AS saved_by_user,
                   p.status
            FROM projects p
            LEFT JOIN categories c ON c.category_id = p.category_id
            WHERE p.user_id = %s
              AND (
                  p.status = 'published'
                  OR (p.status = 'hidden' AND p.user_id = %s)
              )
            ORDER BY p.created_at DESC
            """,
            (viewer_id, viewer_id, user_id, viewer_id),
        )
        return cursor.fetchall()


def friends_for_user(user_id):
    with database_cursor() as cursor:
        cursor.execute(
            """
            SELECT u.user_id, u.full_name, u.username, u.profession, u.profile_image
            FROM users u
            JOIN followers outgoing
              ON outgoing.followed_user_id = u.user_id
             AND outgoing.follower_user_id = %s
            JOIN followers incoming
              ON incoming.follower_user_id = u.user_id
             AND incoming.followed_user_id = %s
            WHERE u.account_status = 'active'
            ORDER BY u.full_name
            """,
            (user_id, user_id),
        )
        return cursor.fetchall()


def update_profile(
    user_id, full_name, profession, biography, website_url, profile_image=None
):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE users
            SET full_name = %s, profession = %s, biography = %s, website_url = %s,
                profile_image = COALESCE(%s, profile_image)
            WHERE user_id = %s
            """,
            (full_name, profession, biography, website_url, profile_image, user_id),
        )


def password_hash_for_user(user_id):
    with database_cursor() as cursor:
        cursor.execute(
            "SELECT password_hash FROM users WHERE user_id = %s",
            (user_id,),
        )
        return cursor.fetchone()


def update_password(user_id, password_hash):
    with database_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE user_id = %s",
            (password_hash, user_id),
        )
