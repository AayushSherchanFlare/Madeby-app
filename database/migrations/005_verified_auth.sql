-- Add verified email registration and Google OpenID Connect identities.
-- Run once as a database administrator.

USE madeby;

DELIMITER //

DROP PROCEDURE IF EXISTS migrate_005_verified_auth//
CREATE PROCEDURE migrate_005_verified_auth()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'users'
          AND COLUMN_NAME = 'google_subject'
    ) THEN
        ALTER TABLE users
            ADD COLUMN google_subject VARCHAR(255) NULL AFTER password_hash,
            ADD UNIQUE KEY uq_users_google_subject (google_subject);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'users'
          AND COLUMN_NAME = 'email_verified'
    ) THEN
        ALTER TABLE users
            ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT TRUE
            AFTER google_subject;
    END IF;

    CREATE TABLE IF NOT EXISTS pending_registrations (
        verification_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        full_name VARCHAR(120) NOT NULL,
        username VARCHAR(30) NOT NULL,
        email VARCHAR(254) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        code_hash CHAR(64) NOT NULL,
        expires_at DATETIME NOT NULL,
        attempts TINYINT UNSIGNED NOT NULL DEFAULT 0,
        resend_available_at DATETIME NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (verification_id),
        UNIQUE KEY uq_pending_registrations_username (username),
        UNIQUE KEY uq_pending_registrations_email (email),
        KEY idx_pending_registrations_expires (expires_at)
    ) ENGINE=InnoDB;
END//

CALL migrate_005_verified_auth()//
DROP PROCEDURE migrate_005_verified_auth//

DELIMITER ;
