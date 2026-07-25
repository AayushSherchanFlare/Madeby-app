import re

import pytest
from werkzeug.security import generate_password_hash


def test_registration_page_renders(client):
    response = client.get("/register")

    assert response.status_code == 200
    assert b"Join MadeBy" in response.data
    assert b'name="username"' in response.data
    assert b'class="brand"' in response.data


def test_registration_accepts_valid_csrf_token(monkeypatch):
    from app import create_app
    from config import TestConfig

    class CsrfTestConfig(TestConfig):
        WTF_CSRF_ENABLED = True

    monkeypatch.setattr(
        "app.controllers.authController.start_email_registration",
        lambda **details: details["email"],
    )
    client = create_app(CsrfTestConfig).test_client()
    page = client.get("/register")
    token_match = re.search(
        rb'name="csrf_token" type="hidden" value="([^"]+)"',
        page.data,
    )

    assert token_match is not None
    response = client.post(
        "/register",
        data={
            "csrf_token": token_match.group(1).decode(),
            "full_name": "Maya Shrestha",
            "username": "maya",
            "email": "maya@example.com",
            "password": "correct-horse",
            "confirm_password": "correct-horse",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/verify-email")


def test_registration_validates_input_before_database_use(client):
    response = client.post(
        "/register",
        data={
            "full_name": "A",
            "username": "not valid!",
            "email": "invalid",
            "password": "short",
            "confirm_password": "different",
        },
    )

    assert response.status_code == 200
    assert b"Use only letters, numbers, and underscores." in response.data
    assert b"Enter a valid email address." in response.data
    assert b"Passwords must match." in response.data


def test_successful_registration_requires_login(client, monkeypatch):
    submitted = {}

    def fake_register(**details):
        submitted.update(details)
        return details["email"]

    monkeypatch.setattr(
        "app.controllers.authController.start_email_registration",
        fake_register,
    )

    response = client.post(
        "/register",
        data={
            "full_name": "Maya Shrestha",
            "username": "Maya_Studio",
            "email": "MAYA@example.com",
            "password": "correct-horse",
            "confirm_password": "correct-horse",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/verify-email")
    with client.session_transaction() as session:
        assert "user_id" not in session
        assert "role" not in session
    verification_page = client.get("/verify-email")
    assert b"We sent a six-digit code to your email." in verification_page.data
    assert b"Enter your code" in verification_page.data
    assert submitted["username"] == "maya_studio"
    assert submitted["email"] == "maya@example.com"


def test_verified_registration_redirects_to_login(client, monkeypatch):
    monkeypatch.setattr(
        "app.controllers.authController.verify_email_registration",
        lambda email, code: 42,
    )
    with client.session_transaction() as session:
        session["pending_verification_email"] = "maya@example.com"

    response = client.post("/verify-email", data={"code": "123456"})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    login_page = client.get("/login")
    assert b"Email verified. You can now log in." in login_page.data


def test_verification_rejects_non_six_digit_code(client):
    with client.session_transaction() as session:
        session["pending_verification_email"] = "maya@example.com"

    response = client.post("/verify-email", data={"code": "12345"})

    assert response.status_code == 200
    assert b"Enter the six-digit code." in response.data


def test_google_login_without_credentials_returns_to_login(client):
    response = client.get("/login/google")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    page = client.get("/login")
    assert b"Google login has not been configured yet." in page.data


def test_google_oauth_uses_direct_endpoints_without_discovery(monkeypatch):
    from app import create_app
    from config import TestConfig

    class GoogleTestConfig(TestConfig):
        GOOGLE_CLIENT_ID = "test-client"
        GOOGLE_CLIENT_SECRET = "test-secret"

    registered = {}
    monkeypatch.setattr(
        "app.oauth.register",
        lambda **settings: registered.update(settings),
    )

    create_app(GoogleTestConfig)

    assert registered["authorize_url"] == (
        "https://accounts.google.com/o/oauth2/v2/auth"
    )
    assert registered["access_token_url"] == "https://oauth2.googleapis.com/token"
    assert registered["jwks_uri"] == "https://www.googleapis.com/oauth2/v3/certs"
    assert "server_metadata_url" not in registered
    assert registered["client_kwargs"]["default_timeout"] == 15


def test_login_rejects_invalid_credentials(client, monkeypatch):
    monkeypatch.setattr(
        "app.controllers.authController.authenticate_user",
        lambda *_args: None,
    )

    response = client.post(
        "/login",
        data={"email": "maya@example.com", "password": "incorrect"},
    )

    assert response.status_code == 200
    assert b"Email or password is incorrect." in response.data


def test_login_starts_session(client, monkeypatch):
    monkeypatch.setattr(
        "app.controllers.authController.authenticate_user",
        lambda *_args: {
            "user_id": 7,
            "full_name": "Arun Rai",
            "role": "user",
        },
    )

    response = client.post(
        "/login",
        data={"email": "arun@example.com", "password": "valid-password"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/feed")
    with client.session_transaction() as session:
        assert session["user_id"] == 7


def test_login_does_not_redirect_to_another_host(client, monkeypatch):
    monkeypatch.setattr(
        "app.controllers.authController.authenticate_user",
        lambda *_args: {
            "user_id": 7,
            "full_name": "Arun Rai",
            "role": "user",
        },
    )

    response = client.post(
        "/login?next=https://example.org/steal",
        data={"email": "arun@example.com", "password": "valid-password"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/feed")


def test_login_accepts_safe_local_redirect(client, monkeypatch):
    monkeypatch.setattr(
        "app.controllers.authController.authenticate_user",
        lambda *_args: {
            "user_id": 7,
            "full_name": "Arun Rai",
            "role": "user",
        },
    )

    response = client.post(
        "/login?next=/projects?page=2",
        data={"email": "arun@example.com", "password": "valid-password"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/projects?page=2")


def test_login_rejects_backslash_redirect(client, monkeypatch):
    monkeypatch.setattr(
        "app.controllers.authController.authenticate_user",
        lambda *_args: {
            "user_id": 7,
            "full_name": "Arun Rai",
            "role": "user",
        },
    )

    response = client.post(
        r"/login?next=\example.org",
        data={"email": "arun@example.com", "password": "valid-password"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/feed")


def test_account_requires_login(client):
    response = client.get("/account")

    assert response.status_code == 302
    assert "/login?next=/account" in response.headers["Location"]


def test_account_renders_for_active_user(client, monkeypatch):
    lookups = []

    def find_user(user_id):
        lookups.append(user_id)
        return {
            "user_id": 7,
            "full_name": "Sofia Chen",
            "username": "sofia",
            "email": "sofia@example.com",
            "role": "user",
            "account_status": "active",
        }

    monkeypatch.setattr(
        "app.repository.userRepository.find_by_id",
        find_user,
    )
    with client.session_transaction() as session:
        session["user_id"] = 7
        session["role"] = "user"

    response = client.get("/account")

    assert response.status_code == 200
    assert b"Hello, Sofia." in response.data
    assert b"@sofia" in response.data
    assert lookups == [7]


def test_last_seen_write_is_throttled_per_session(client, monkeypatch):
    user = {
        "user_id": 7,
        "full_name": "Sofia Chen",
        "username": "sofia",
        "email": "sofia@example.com",
        "role": "user",
        "account_status": "active",
    }
    touches = []
    monkeypatch.setattr(
        "app.repository.userRepository.find_by_id",
        lambda _user_id: user,
    )
    monkeypatch.setattr(
        "app.repository.userRepository.touch_last_seen",
        lambda user_id: touches.append(user_id),
    )
    client.application.config["TESTING"] = False
    with client.session_transaction() as session:
        session["user_id"] = 7
        session["role"] = "user"

    assert client.get("/account").status_code == 200
    assert client.get("/account").status_code == 200
    assert touches == [7]


def test_logout_clears_session(client):
    with client.session_transaction() as session:
        session["user_id"] = 7
        session["role"] = "user"

    response = client.post("/logout")

    assert response.status_code == 302
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_pending_registration_hashes_password_and_email_code(app, monkeypatch):
    captured = {}
    delivered = {}
    monkeypatch.setattr(
        "app.services.authService.userRepository.find_registration_conflicts",
        lambda *_args: [],
    )
    monkeypatch.setattr(
        "app.services.authService.userRepository.find_pending_conflicts",
        lambda *_args: [],
    )

    def fake_save(**details):
        captured.update(details)

    monkeypatch.setattr(
        "app.services.authService.userRepository.save_pending_registration",
        fake_save,
    )
    monkeypatch.setattr(
        "app.services.authService.send_verification_code",
        lambda email, code: delivered.update(email=email, code=code),
    )

    from app.services.authService import start_email_registration

    with app.app_context():
        email = start_email_registration(
            "Maya Shrestha", "maya", "maya@example.com", "correct-horse"
        )

    assert email == "maya@example.com"
    assert captured["password_hash"] != "correct-horse"
    assert captured["password_hash"].startswith(("scrypt:", "pbkdf2:"))
    assert re.fullmatch(r"\d{6}", delivered["code"])
    assert captured["code_hash"] != delivered["code"]


@pytest.mark.parametrize(
    ("conflicts", "field"),
    [
        ([{"username": "other", "email": "maya@example.com"}], "email"),
        ([{"username": "maya", "email": "other@example.com"}], "username"),
        (
            [
                {"username": "maya", "email": "other@example.com"},
                {"username": "other", "email": "maya@example.com"},
            ],
            "email",
        ),
    ],
)
def test_registration_reports_database_conflicts(app, monkeypatch, conflicts, field):
    monkeypatch.setattr(
        "app.services.authService.userRepository.find_registration_conflicts",
        lambda *_args: conflicts,
    )

    from app.services.authService import RegistrationConflict, start_email_registration

    with app.app_context(), pytest.raises(RegistrationConflict) as raised:
        start_email_registration(
            "Maya Shrestha", "maya", "maya@example.com", "correct-horse"
        )

    assert raised.value.field == field
    assert str(raised.value) == raised.value.message


def test_authentication_accepts_valid_hash(monkeypatch):
    monkeypatch.setattr(
        "app.services.authService.userRepository.find_by_email",
        lambda _email: {
            "user_id": 3,
            "full_name": "Maya Shrestha",
            "role": "user",
            "account_status": "active",
            "password_hash": generate_password_hash("correct-horse"),
        },
    )

    from app.services.authService import authenticate_user

    assert authenticate_user("maya@example.com", "correct-horse")["user_id"] == 3
    assert authenticate_user("maya@example.com", "wrong") is None


def test_authentication_rejects_disabled_account(monkeypatch):
    monkeypatch.setattr(
        "app.services.authService.userRepository.find_by_email",
        lambda _email: {
            "user_id": 3,
            "full_name": "Maya Shrestha",
            "role": "user",
            "account_status": "disabled",
            "password_hash": generate_password_hash("correct-horse"),
        },
    )

    from app.services.authService import authenticate_user

    assert authenticate_user("maya@example.com", "correct-horse") is None
