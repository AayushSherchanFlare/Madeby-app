# MadeBy

MadeBy is an individual university web application project for creative professionals to present projects and connect around original work. Its visual direction combines portfolio-first presentation with familiar social interactions without copying an existing platform.

**Created by Aayush Thakali Sherchan.**

This repository currently contains **Phase 2: Authentication**. Profiles, projects, interactions, notifications, settings, and moderation remain reserved for later phases.

## Current features

- Flask application factory and public `main` Blueprint
- Responsive, accessible landing page with reusable Jinja2 layout and partials
- Accessible light/dark theme toggle with system preference detection and saved choice
- Supplied responsive MadeBy wordmark and matching light/dark browser icons
- `#3526f3` primary brand colour with accessible light/dark theme treatments
- Custom 403, 404, 413, and 500 responses
- Environment-based application and MySQL configuration
- Reusable, transaction-aware MySQL connection helper
- CSRF protection for state-changing forms
- Secure session defaults and a 5 MB request limit
- Complete version-one MySQL schema, constraints, indexes, and category seed data
- Controller, repository, route, service, and form layers ready for later phases
- Account registration with server-side validation and duplicate protection
- Password hashing using Werkzeug's secure password utilities
- Login, logout, persistent-session option, and protected account page
- Safe post-login redirects and account-status enforcement
- CSRF-protected authentication forms and logout action
- Automated authentication and route tests

## Technology stack

- Python 3.11+
- Flask and Jinja2
- Flask-WTF
- MySQL 8.0.16+
- MySQL Connector/Python
- HTML5, custom CSS3, and small amounts of vanilla JavaScript

## Local setup

Run commands from the `madeby` directory.

### 1. Create and activate a virtual environment

PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Create the database and application user

Open MySQL as an administrative user:

```powershell
mysql -u root -p
```

Run the following statements, replacing the example password:

```sql
CREATE DATABASE IF NOT EXISTS madeby CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER IF NOT EXISTS 'madeby_user'@'localhost' IDENTIFIED BY 'choose-a-strong-password';
GRANT SELECT, INSERT, UPDATE, DELETE ON madeby.* TO 'madeby_user'@'localhost';
FLUSH PRIVILEGES;
```

Using the same administrative MySQL session, create the tables and seed the
categories:

```sql
SOURCE E:/My App/database/schema.sql;
SOURCE E:/My App/database/seed.sql;
```

The schema script creates and selects `madeby`; the seed script selects it again
so it is safe to run independently.

When upgrading an existing Phase 1 database, install the relationship-integrity
triggers with an administrative account:

```sql
SOURCE E:/My App/database/migrations/001_add_relationship_triggers.sql;
SOURCE E:/My App/database/migrations/002_streamline_schema.sql;
```

The application database user should not be granted the elevated global
privileges required to create triggers.

### 4. Configure environment variables

Copy the example file:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set a unique secret and the database password selected above. A secret can be generated with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Do not commit `.env`. For local HTTP development, leave `SESSION_COOKIE_SECURE=false`; set it to `true` when deployed behind HTTPS.

### 5. Run MadeBy

```powershell
python app.py
```

Visit `http://127.0.0.1:5000/`. The landing page does not query MySQL, so it can render even before the database is connected. Registration and login require the configured database.

## Verification checklist

- [ ] `python app.py` starts without an import or configuration error.
- [ ] `/` returns the responsive MadeBy landing page.
- [ ] The mobile menu opens at a narrow browser width and can be used by keyboard.
- [ ] A missing URL such as `/does-not-exist` displays the custom 404 page.
- [ ] `SHOW TABLES;` in MySQL lists all ten version-one tables.
- [ ] `SELECT * FROM categories;` returns the nine seeded creative categories.
- [ ] A new account can register, log out, and log back in.
- [ ] `python -m pytest` completes successfully.
- [ ] Upload directories exist and contain only tracked `.gitkeep` placeholders.
- [ ] `.env` is ignored by Git and contains no committed credentials.

## Default administrator creation

MadeBy does not ship a default account or password. Register an account normally and promote it using an administrative MySQL session:

```sql
UPDATE users SET role = 'admin' WHERE email = 'your-email@example.com';
```

This avoids publishing reusable administrator credentials or a plaintext password.

## Security foundations

- Credentials and the Flask secret are loaded from environment variables.
- Session cookies are HTTP-only, `SameSite=Lax`, and production-ready for HTTPS-only mode.
- CSRF protection is initialized globally for future forms.
- Database access uses MySQL Connector and is designed for parameterized queries.
- The cursor helper commits only when requested, rolls back failures, and always closes resources.
- InnoDB relationships use restricted, cascading, or nullifying deletes based on data ownership.
- Duplicate likes, follows, tags, usernames, and email addresses are prevented by database constraints.
- Database triggers prevent self-following and invalid project notification links.
- Jinja2 automatic escaping remains enabled; no user content uses the `safe` filter.

## Testing

Run the automated suite with:

```powershell
python -m pytest
```

The authentication tests use isolated fakes and do not require a running MySQL server.

## Known limitations

Featured landing-page content is still presentation data. Authentication is active, while project uploads, editable profiles, social features, notifications, settings, and the admin panel are not yet implemented.

## Planned improvements

The next phases add editable profiles, project management, feed and explore, social interactions, notifications, settings, and administration. Longer-term possibilities include messaging, cloud storage, advanced analytics, OAuth, and email verification; these are outside version one.
