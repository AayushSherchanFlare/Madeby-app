-- MadeBy database schema
-- Target: MySQL 8.0.16+ (required for enforced CHECK constraints)

CREATE DATABASE IF NOT EXISTS madeby
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

USE madeby;

CREATE TABLE users (
    user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    full_name VARCHAR(120) NOT NULL,
    username VARCHAR(30) NOT NULL,
    email VARCHAR(254) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    biography VARCHAR(1000) NULL,
    profession VARCHAR(100) NULL,
    skills VARCHAR(500) NULL,
    profile_image VARCHAR(255) NULL,
    cover_image VARCHAR(255) NULL,
    website_url VARCHAR(2048) NULL,
    role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    account_status ENUM('active', 'disabled') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_users_username (username),
    UNIQUE KEY uq_users_email (email),
    KEY idx_users_status (account_status),
    CONSTRAINT chk_users_full_name_length CHECK (CHAR_LENGTH(TRIM(full_name)) BETWEEN 2 AND 120),
    CONSTRAINT chk_users_username_length CHECK (CHAR_LENGTH(TRIM(username)) BETWEEN 3 AND 30),
    CONSTRAINT chk_users_email_not_blank CHECK (CHAR_LENGTH(TRIM(email)) > 0)
) ENGINE=InnoDB;

CREATE TABLE categories (
    category_id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    category_name VARCHAR(80) NOT NULL,
    PRIMARY KEY (category_id),
    UNIQUE KEY uq_categories_name (category_name),
    CONSTRAINT chk_categories_name_not_blank CHECK (CHAR_LENGTH(TRIM(category_name)) > 0)
) ENGINE=InnoDB;

CREATE TABLE projects (
    project_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    category_id SMALLINT UNSIGNED NOT NULL,
    title VARCHAR(160) NOT NULL,
    description TEXT NOT NULL,
    cover_image VARCHAR(255) NOT NULL,
    tools_used VARCHAR(500) NULL,
    status ENUM('draft', 'published', 'hidden') NOT NULL DEFAULT 'published',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id),
    KEY idx_projects_user (user_id),
    KEY idx_projects_category (category_id),
    KEY idx_projects_created (created_at),
    KEY idx_projects_status_created (status, created_at),
    CONSTRAINT fk_projects_user FOREIGN KEY (user_id)
        REFERENCES users (user_id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_projects_category FOREIGN KEY (category_id)
        REFERENCES categories (category_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_projects_title_length CHECK (CHAR_LENGTH(TRIM(title)) BETWEEN 1 AND 160),
    CONSTRAINT chk_projects_description_length CHECK (CHAR_LENGTH(TRIM(description)) BETWEEN 1 AND 10000)
) ENGINE=InnoDB;

CREATE TABLE project_images (
    image_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id BIGINT UNSIGNED NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    image_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (image_id),
    UNIQUE KEY uq_project_images_order (project_id, image_order),
    CONSTRAINT fk_project_images_project FOREIGN KEY (project_id)
        REFERENCES projects (project_id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE tags (
    tag_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    tag_name VARCHAR(50) NOT NULL,
    PRIMARY KEY (tag_id),
    UNIQUE KEY uq_tags_name (tag_name),
    CONSTRAINT chk_tags_name_not_blank CHECK (CHAR_LENGTH(TRIM(tag_name)) > 0)
) ENGINE=InnoDB;

CREATE TABLE project_tags (
    project_id BIGINT UNSIGNED NOT NULL,
    tag_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (project_id, tag_id),
    KEY idx_project_tags_tag (tag_id),
    CONSTRAINT fk_project_tags_project FOREIGN KEY (project_id)
        REFERENCES projects (project_id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_project_tags_tag FOREIGN KEY (tag_id)
        REFERENCES tags (tag_id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE likes (
    like_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    project_id BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (like_id),
    UNIQUE KEY uq_likes_user_project (user_id, project_id),
    KEY idx_likes_project (project_id),
    CONSTRAINT fk_likes_user FOREIGN KEY (user_id)
        REFERENCES users (user_id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_likes_project FOREIGN KEY (project_id)
        REFERENCES projects (project_id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE comments (
    comment_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    project_id BIGINT UNSIGNED NOT NULL,
    comment_text VARCHAR(1000) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (comment_id),
    KEY idx_comments_user (user_id),
    KEY idx_comments_project_created (project_id, created_at),
    CONSTRAINT fk_comments_user FOREIGN KEY (user_id)
        REFERENCES users (user_id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_comments_project FOREIGN KEY (project_id)
        REFERENCES projects (project_id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT chk_comments_text_length CHECK (CHAR_LENGTH(TRIM(comment_text)) BETWEEN 1 AND 1000)
) ENGINE=InnoDB;

CREATE TABLE followers (
    follow_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    follower_user_id BIGINT UNSIGNED NOT NULL,
    followed_user_id BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follow_id),
    UNIQUE KEY uq_followers_pair (follower_user_id, followed_user_id),
    KEY idx_followers_followed (followed_user_id),
    CONSTRAINT fk_followers_follower FOREIGN KEY (follower_user_id)
        REFERENCES users (user_id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_followers_followed FOREIGN KEY (followed_user_id)
        REFERENCES users (user_id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

DELIMITER //

CREATE TRIGGER trg_followers_prevent_self_insert
BEFORE INSERT ON followers
FOR EACH ROW
BEGIN
    IF NEW.follower_user_id = NEW.followed_user_id THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'A user cannot follow themselves';
    END IF;
END//

CREATE TRIGGER trg_followers_prevent_self_update
BEFORE UPDATE ON followers
FOR EACH ROW
BEGIN
    IF NEW.follower_user_id = NEW.followed_user_id THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'A user cannot follow themselves';
    END IF;
END//

DELIMITER ;

CREATE TABLE notifications (
    notification_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    recipient_user_id BIGINT UNSIGNED NOT NULL,
    sender_user_id BIGINT UNSIGNED NULL,
    notification_type ENUM('like', 'comment', 'follow') NOT NULL,
    related_project_id BIGINT UNSIGNED NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (notification_id),
    KEY idx_notifications_recipient_read_created (recipient_user_id, is_read, created_at),
    KEY idx_notifications_sender (sender_user_id),
    KEY idx_notifications_project (related_project_id),
    CONSTRAINT fk_notifications_recipient FOREIGN KEY (recipient_user_id)
        REFERENCES users (user_id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_notifications_sender FOREIGN KEY (sender_user_id)
        REFERENCES users (user_id) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_notifications_project FOREIGN KEY (related_project_id)
        REFERENCES projects (project_id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

DELIMITER //

CREATE TRIGGER trg_notifications_validate_insert
BEFORE INSERT ON notifications
FOR EACH ROW
BEGIN
    IF NOT (
        (NEW.notification_type IN ('like', 'comment') AND NEW.related_project_id IS NOT NULL)
        OR (NEW.notification_type = 'follow' AND NEW.related_project_id IS NULL)
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Notification type and related project do not match';
    END IF;
END//

CREATE TRIGGER trg_notifications_validate_update
BEFORE UPDATE ON notifications
FOR EACH ROW
BEGIN
    IF NOT (
        (NEW.notification_type IN ('like', 'comment') AND NEW.related_project_id IS NOT NULL)
        OR (NEW.notification_type = 'follow' AND NEW.related_project_id IS NULL)
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Notification type and related project do not match';
    END IF;
END//

DELIMITER ;
