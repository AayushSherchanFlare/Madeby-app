-- One-time migration: add relationship integrity triggers to an existing
-- MadeBy database. Run with an administrative MySQL account.
-- MySQL does not allow these rules as CHECK constraints because the referenced
-- columns participate in cascading foreign-key actions.

USE madeby;

DELIMITER //

DROP TRIGGER IF EXISTS trg_followers_prevent_self_insert//
CREATE TRIGGER trg_followers_prevent_self_insert
BEFORE INSERT ON followers
FOR EACH ROW
BEGIN
    IF NEW.follower_user_id = NEW.followed_user_id THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'A user cannot follow themselves';
    END IF;
END//

DROP TRIGGER IF EXISTS trg_followers_prevent_self_update//
CREATE TRIGGER trg_followers_prevent_self_update
BEFORE UPDATE ON followers
FOR EACH ROW
BEGIN
    IF NEW.follower_user_id = NEW.followed_user_id THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'A user cannot follow themselves';
    END IF;
END//

DROP TRIGGER IF EXISTS trg_notifications_validate_insert//
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

DROP TRIGGER IF EXISTS trg_notifications_validate_update//
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
