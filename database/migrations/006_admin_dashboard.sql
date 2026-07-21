-- Add creator moderation, activity tracking, warning notifications, and audit logs.
-- Run as a database administrator.

USE madeby;

DELIMITER //

DROP PROCEDURE IF EXISTS migrate_006_admin_dashboard//
CREATE PROCEDURE migrate_006_admin_dashboard()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'
          AND COLUMN_NAME = 'suspended_until'
    ) THEN
        ALTER TABLE users ADD COLUMN suspended_until DATETIME NULL
            AFTER account_status;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'
          AND COLUMN_NAME = 'last_seen_at'
    ) THEN
        ALTER TABLE users ADD COLUMN last_seen_at DATETIME NULL
            AFTER suspended_until;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'notifications'
          AND COLUMN_NAME = 'message_text'
    ) THEN
        ALTER TABLE notifications ADD COLUMN message_text VARCHAR(1000) NULL
            AFTER related_project_id;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'notifications'
          AND COLUMN_NAME = 'notification_type'
          AND COLUMN_TYPE LIKE '%admin_message%'
    ) THEN
        ALTER TABLE notifications
            MODIFY notification_type
            ENUM('like', 'comment', 'follow', 'admin_message') NOT NULL;
    END IF;

    CREATE TABLE IF NOT EXISTS admin_audit_logs (
        audit_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        admin_user_id BIGINT UNSIGNED NULL,
        action_type ENUM(
            'suspend_user', 'unsuspend_user', 'delete_user',
            'delete_post', 'send_warning'
        ) NOT NULL,
        target_user_id BIGINT UNSIGNED NULL,
        target_project_id BIGINT UNSIGNED NULL,
        details VARCHAR(1000) NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (audit_id),
        KEY idx_admin_audit_created (created_at),
        KEY idx_admin_audit_admin (admin_user_id),
        KEY idx_admin_audit_target_user (target_user_id),
        CONSTRAINT fk_admin_audit_admin FOREIGN KEY (admin_user_id)
            REFERENCES users (user_id) ON UPDATE CASCADE ON DELETE SET NULL,
        CONSTRAINT fk_admin_audit_target_user FOREIGN KEY (target_user_id)
            REFERENCES users (user_id) ON UPDATE CASCADE ON DELETE SET NULL,
        CONSTRAINT fk_admin_audit_target_project FOREIGN KEY (target_project_id)
            REFERENCES projects (project_id) ON UPDATE CASCADE ON DELETE SET NULL
    ) ENGINE=InnoDB;
END//

CALL migrate_006_admin_dashboard()//
DROP PROCEDURE migrate_006_admin_dashboard//

DROP TRIGGER IF EXISTS trg_notifications_validate_insert//
CREATE TRIGGER trg_notifications_validate_insert
BEFORE INSERT ON notifications
FOR EACH ROW
BEGIN
    IF NOT (
        (
            NEW.notification_type IN ('like', 'comment')
            AND NEW.related_project_id IS NOT NULL
            AND NEW.message_text IS NULL
        )
        OR (
            NEW.notification_type = 'follow'
            AND NEW.related_project_id IS NULL
            AND NEW.message_text IS NULL
        )
        OR (
            NEW.notification_type = 'admin_message'
            AND NEW.related_project_id IS NULL
            AND CHAR_LENGTH(TRIM(NEW.message_text)) BETWEEN 1 AND 1000
        )
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Notification fields do not match its type';
    END IF;
END//

DROP TRIGGER IF EXISTS trg_notifications_validate_update//
CREATE TRIGGER trg_notifications_validate_update
BEFORE UPDATE ON notifications
FOR EACH ROW
BEGIN
    IF NOT (
        (
            NEW.notification_type IN ('like', 'comment')
            AND NEW.related_project_id IS NOT NULL
            AND NEW.message_text IS NULL
        )
        OR (
            NEW.notification_type = 'follow'
            AND NEW.related_project_id IS NULL
            AND NEW.message_text IS NULL
        )
        OR (
            NEW.notification_type = 'admin_message'
            AND NEW.related_project_id IS NULL
            AND CHAR_LENGTH(TRIM(NEW.message_text)) BETWEEN 1 AND 1000
        )
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Notification fields do not match its type';
    END IF;
END//

DELIMITER ;
