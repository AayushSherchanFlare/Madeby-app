-- Restart-safe migration for an existing MadeBy database.
-- Run with an administrative MySQL account.

USE madeby;

DELIMITER //

DROP PROCEDURE IF EXISTS migrate_002_streamline_schema//

CREATE PROCEDURE migrate_002_streamline_schema()
BEGIN
    IF EXISTS (
        SELECT 1 FROM users
        WHERE CHAR_LENGTH(TRIM(full_name)) NOT BETWEEN 2 AND 120
           OR CHAR_LENGTH(TRIM(username)) NOT BETWEEN 3 AND 30
           OR CHAR_LENGTH(TRIM(email)) = 0
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Migration blocked by invalid user text fields';
    END IF;

    IF EXISTS (
        SELECT 1 FROM categories WHERE CHAR_LENGTH(TRIM(category_name)) = 0
    ) OR EXISTS (
        SELECT 1 FROM tags WHERE CHAR_LENGTH(TRIM(tag_name)) = 0
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Migration blocked by a blank category or tag';
    END IF;

    IF EXISTS (
        SELECT 1 FROM projects
        WHERE CHAR_LENGTH(TRIM(title)) NOT BETWEEN 1 AND 160
           OR CHAR_LENGTH(TRIM(description)) NOT BETWEEN 1 AND 10000
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Migration blocked by invalid project text fields';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = DATABASE()
          AND table_name = 'users'
          AND constraint_name = 'chk_users_full_name_length'
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT chk_users_full_name_length
                CHECK (CHAR_LENGTH(TRIM(full_name)) BETWEEN 2 AND 120);
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = DATABASE()
          AND table_name = 'users'
          AND constraint_name = 'chk_users_username_length'
    ) THEN
        ALTER TABLE users DROP CHECK chk_users_username_length;
    END IF;

    ALTER TABLE users
        ADD CONSTRAINT chk_users_username_length
            CHECK (CHAR_LENGTH(TRIM(username)) BETWEEN 3 AND 30);

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = DATABASE()
          AND table_name = 'users'
          AND constraint_name = 'chk_users_email_not_blank'
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT chk_users_email_not_blank
                CHECK (CHAR_LENGTH(TRIM(email)) > 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = DATABASE()
          AND table_name = 'categories'
          AND constraint_name = 'chk_categories_name_not_blank'
    ) THEN
        ALTER TABLE categories
            ADD CONSTRAINT chk_categories_name_not_blank
                CHECK (CHAR_LENGTH(TRIM(category_name)) > 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = DATABASE()
          AND table_name = 'tags'
          AND constraint_name = 'chk_tags_name_not_blank'
    ) THEN
        ALTER TABLE tags
            ADD CONSTRAINT chk_tags_name_not_blank
                CHECK (CHAR_LENGTH(TRIM(tag_name)) > 0);
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = DATABASE()
          AND table_name = 'projects'
          AND constraint_name = 'chk_projects_title_length'
    ) THEN
        ALTER TABLE projects DROP CHECK chk_projects_title_length;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema = DATABASE()
          AND table_name = 'projects'
          AND constraint_name = 'chk_projects_description_length'
    ) THEN
        ALTER TABLE projects DROP CHECK chk_projects_description_length;
    END IF;

    ALTER TABLE projects
        ADD CONSTRAINT chk_projects_title_length
            CHECK (CHAR_LENGTH(TRIM(title)) BETWEEN 1 AND 160),
        ADD CONSTRAINT chk_projects_description_length
            CHECK (CHAR_LENGTH(TRIM(description)) BETWEEN 1 AND 10000);

    IF EXISTS (
        SELECT 1 FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = 'project_images'
          AND index_name = 'idx_project_images_project'
    ) THEN
        ALTER TABLE project_images DROP INDEX idx_project_images_project;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = 'comments'
          AND index_name = 'idx_comments_project'
    ) THEN
        ALTER TABLE comments DROP INDEX idx_comments_project;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = 'notifications'
          AND index_name = 'idx_notifications_recipient'
    ) THEN
        ALTER TABLE notifications DROP INDEX idx_notifications_recipient;
    END IF;
END//

CALL migrate_002_streamline_schema()//
DROP PROCEDURE migrate_002_streamline_schema//

DELIMITER ;
