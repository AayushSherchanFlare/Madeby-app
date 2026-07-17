-- Add account-backed post saving for the social feed.
-- Safe to run more than once.

USE madeby;

CREATE TABLE IF NOT EXISTS saved_posts (
    saved_post_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    project_id BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (saved_post_id),
    UNIQUE KEY uq_saved_posts_user_project (user_id, project_id),
    KEY idx_saved_posts_project (project_id),
    CONSTRAINT fk_saved_posts_user FOREIGN KEY (user_id)
        REFERENCES users (user_id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_saved_posts_project FOREIGN KEY (project_id)
        REFERENCES projects (project_id) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;
