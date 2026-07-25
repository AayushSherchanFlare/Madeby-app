# MadeBy

MadeBy is an individual university web application project for creative professionals to present projects and connect around original work. Its visual direction combines portfolio-first presentation with familiar social interactions without copying an existing platform.

**Created by Aayush Thakali Sherchan.**

This repository currently contains **Phase 3: Social feed and profiles**. It keeps the original public landing page while giving signed-in members a separate social workspace.

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
- Secure session defaults and a 20 MB request limit
- Complete MySQL schema, constraints, indexes, migrations, and category seed data
- Focused controller, repository, route, service, and form layers
- Account registration with server-side validation and duplicate protection
- Six-digit email verification with expiration, attempt limits, and resend cooldown
- Google OpenID Connect login with verified-email account linking
- Six-digit email password recovery with expiration, attempt limits, and resend cooldown
- Password hashing using Werkzeug's secure password utilities
- Login, logout, persistent-session option, and protected account page
- Safe post-login redirects and account-status enforcement
- CSRF-protected authentication forms and logout action
- Signed-in feed combining the member's work, followed creators, and community posts
- Text-or-photo post composer with live preview, category selection, image-signature validation, and center-cropped 1:1, 9:16, or 16:9 photos
- Owner-only post editing, deletion, and private profile visibility controls
- Likes, comments, saved posts, shareable post links, persistent follow suggestions, and category feed filters
- Notification inbox and unread count for likes, comments, and new followers
- Follow, follow-back, and unfollow states across suggestions and member lists
- Public member profiles with clickable follower and following lists
- Mutual-follow friends list with a messaging placeholder
- Profile editing and secure password changes
- Creator-only administration dashboard with user and feed search
- Timed account suspension, warning notifications, and permanent moderation actions
- Online/offline activity summaries and a permanent creator audit trail
- One-way password storage that prevents anyone from reading member passwords
- Responsive desktop/mobile dashboard derived from the supplied UI reference
- Automated authentication, social, database-helper, route, and schema tests

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
SOURCE E:/My App/database/migrations/003_social_feed_posts.sql;
SOURCE E:/My App/database/migrations/004_add_saved_posts.sql;
SOURCE E:/My App/database/migrations/005_verified_auth.sql;
SOURCE E:/My App/database/migrations/006_admin_dashboard.sql;
SOURCE E:/My App/database/migrations/007_godhood_role.sql;
SOURCE E:/My App/database/migrations/008_password_reset.sql;
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

To enable verified registration, configure the `SMTP_*` values in `.env`.
For Gmail, use an app password rather than your normal Google password.

To enable Google login, create a Google OAuth web client and add its client ID
and secret as `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`. Set
`GOOGLE_REDIRECT_URI` and register the same exact authorized redirect URI. For
local development, the example is:

```text
http://127.0.0.1:5000/login/google/callback
```

The scheme, host, port, path, and trailing slash must match the Google Cloud
configuration exactly.

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
- [ ] `SHOW TABLES;` in MySQL lists all fourteen tables.
- [ ] `SELECT * FROM categories;` returns the nine seeded creative categories.
- [ ] A new account can receive a verification code, verify, and log in.
- [ ] “Continue with Google” creates or safely links a verified account.
- [ ] The promoted creator account can open `/godhood/`.
- [ ] Creator suspensions block access and expire automatically.
- [ ] Creator warnings appear in the target member's notifications.
- [ ] `python -m pytest` completes successfully.
- [ ] Upload directories exist and contain only tracked `.gitkeep` placeholders.
- [ ] `.env` is ignored by Git and contains no committed credentials.

## Creator account setup

MadeBy does not ship a default creator account or password. Register an account normally and promote it using an administrative MySQL session:

```sql
UPDATE users SET role = 'god' WHERE email = 'your-email@example.com';
```

This avoids publishing reusable creator credentials or a plaintext password.

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

The automated tests use isolated fakes and do not require a running MySQL server.

## Known limitations

Featured landing-page content is presentation data. Direct messaging is not yet implemented.

## Planned improvements

The next phase can add direct messaging. Longer-term possibilities include cloud storage, advanced analytics, and additional OAuth providers.
