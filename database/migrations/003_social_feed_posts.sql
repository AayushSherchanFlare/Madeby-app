-- Adapt projects so they can also serve as text-or-photo feed posts.
-- Safe to run again if a previous attempt completed or stopped partway through.

USE madeby;

DROP PROCEDURE IF EXISTS migrate_003_social_feed_posts;

DELIMITER //

CREATE PROCEDURE migrate_003_social_feed_posts()
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.REFERENTIAL_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = 'projects'
          AND CONSTRAINT_NAME = 'fk_projects_category'
    ) THEN
        ALTER TABLE projects DROP FOREIGN KEY fk_projects_category;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = 'projects'
          AND CONSTRAINT_NAME = 'chk_projects_title_length'
          AND CONSTRAINT_TYPE = 'CHECK'
    ) THEN
        ALTER TABLE projects DROP CHECK chk_projects_title_length;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = 'projects'
          AND CONSTRAINT_NAME = 'chk_projects_description_length'
          AND CONSTRAINT_TYPE = 'CHECK'
    ) THEN
        ALTER TABLE projects DROP CHECK chk_projects_description_length;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = 'projects'
          AND CONSTRAINT_NAME = 'chk_projects_has_content'
          AND CONSTRAINT_TYPE = 'CHECK'
    ) THEN
        ALTER TABLE projects DROP CHECK chk_projects_has_content;
    END IF;

    ALTER TABLE projects
        MODIFY category_id SMALLINT UNSIGNED NULL,
        MODIFY title VARCHAR(160) NULL,
        MODIFY description TEXT NULL,
        MODIFY cover_image VARCHAR(255) NULL,
        ADD CONSTRAINT fk_projects_category FOREIGN KEY (category_id)
            REFERENCES categories (category_id)
            ON UPDATE CASCADE
            ON DELETE SET NULL,
        ADD CONSTRAINT chk_projects_title_length CHECK (
            title IS NULL OR CHAR_LENGTH(TRIM(title)) BETWEEN 1 AND 160
        ),
        ADD CONSTRAINT chk_projects_description_length CHECK (
            description IS NULL OR CHAR_LENGTH(TRIM(description)) BETWEEN 1 AND 10000
        ),
        ADD CONSTRAINT chk_projects_has_content CHECK (
            title IS NOT NULL OR description IS NOT NULL OR cover_image IS NOT NULL
        );
END//

DELIMITER ;

CALL migrate_003_social_feed_posts();
DROP PROCEDURE migrate_003_social_feed_posts;
