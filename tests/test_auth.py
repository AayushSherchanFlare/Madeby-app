import pytest
from werkzeug.security import generate_password_hash


def test_registration_page_renders(client):
    response = client.get("/register")

    assert response.status_code == 200
    assert b"Join MadeBy" in response.data
    assert b'name="username"' in response.data
    assert b'class="brand"' in response.data


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


def test_successful_registration_creates_session(client, monkeypatch):
    submitted = {}

    def fake_register(**details):
        submitted.update(details)
        return 42

    monkeypatch.setattr(
        "app.controllers.authController.register_user",
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
    assert response.headers["Location"].endswith("/account")
    with client.session_transaction() as session:
        assert session["user_id"] == 42
        assert session["role"] == "user"
    assert submitted["username"] == "maya_studio"
    assert submitted["email"] == "maya@example.com"


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
    assert response.headers["Location"].endswith("/account")
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
    assert response.headers["Location"].endswith("/account")


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
    assert response.headers["Location"].endswith("/account")


def test_account_requires_login(client):
    response = client.get("/account")

    assert response.status_code == 302
    assert "/login?next=/account" in response.headers["Location"]


def test_account_renders_for_active_user(client, monkeypatch):
    monkeypatch.setattr(
        "app.controllers.authController.userRepository.find_by_id",
        lambda _user_id: {
            "user_id": 7,
            "full_name": "Sofia Chen",
            "username": "sofia",
            "email": "sofia@example.com",
            "role": "user",
            "account_status": "active",
        },
    )
    with client.session_transaction() as session:
        session["user_id"] = 7
        session["role"] = "user"

    response = client.get("/account")

    assert response.status_code == 200
    assert b"Hello, Sofia." in response.data
    assert b"@sofia" in response.data


def test_logout_clears_session(client):
    with client.session_transaction() as session:
        session["user_id"] = 7
        session["role"] = "user"

    response = client.post("/logout")

    assert response.status_code == 302
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_passwords_are_hashed_before_storage(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "app.services.authService.userRepository.find_registration_conflicts",
        lambda *_args: [],
    )

    def fake_create_user(**details):
        captured.update(details)
        return 10

    monkeypatch.setattr(
        "app.services.authService.userRepository.create_user",
        fake_create_user,
    )

    from app.services.authService import register_user

    user_id = register_user(
        "Maya Shrestha", "maya", "maya@example.com", "correct-horse"
    )

    assert user_id == 10
    assert captured["password_hash"] != "correct-horse"
    assert captured["password_hash"].startswith(("scrypt:", "pbkdf2:"))


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
def test_registration_reports_database_conflicts(monkeypatch, conflicts, field):
    monkeypatch.setattr(
        "app.services.authService.userRepository.find_registration_conflicts",
        lambda *_args: conflicts,
    )

    from app.services.authService import RegistrationConflict, register_user

    with pytest.raises(RegistrationConflict) as raised:
        register_user("Maya Shrestha", "maya", "maya@example.com", "correct-horse")

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
