USE madeby;

INSERT IGNORE INTO categories (category_name) VALUES
    ('Graphic Design'),
    ('UI/UX Design'),
    ('Web Development'),
    ('Photography'),
    ('Videography'),
    ('Illustration'),
    ('Cinematography'),
    ('Motion Graphics'),
    ('Other');

-- No default password is shipped. After authentication is implemented in Phase 2,
-- register normally and promote the chosen account with:
-- UPDATE users SET role = 'admin' WHERE email = 'your-email@example.com';
