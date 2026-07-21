-- Rename the privileged MadeBy application role from admin to god.
-- Safe to run more than once. Run as a database administrator.

USE madeby;

ALTER TABLE users
    MODIFY role ENUM('user', 'admin', 'god') NOT NULL DEFAULT 'user';

UPDATE users
SET role = 'god'
WHERE role = 'admin';

ALTER TABLE users
    MODIFY role ENUM('user', 'god') NOT NULL DEFAULT 'user';
