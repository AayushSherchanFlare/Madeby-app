from datetime import datetime

import pytest


def admin_user():
    return {
        "user_id": 1,
        "full_name": "MadeBy Creator",
        "username": "creator",
        "email": "creator@example.com",
        "role": "god",
        "account_status": "active",
        "suspended_until": None,
        "profile_image": None,
    }


def log_in_admin(client):
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["role"] = "god"


def install_admin(monkeypatch):
    monkeypatch.setattr(
        "app.repository.userRepository.find_by_id",
        lambda _user_id: admin_user(),
    )


def test_admin_dashboard_requires_login(client):
    response = client.get("/godhood/")

    assert response.status_code == 302
    assert "/login?next=/godhood/" in response.headers["Location"]


def test_non_admin_cannot_open_creator_dashboard(client, monkeypatch):
    monkeypatch.setattr(
        "app.repository.userRepository.find_by_id",
        lambda _user_id: {**admin_user(), "role": "user"},
    )
    with client.session_transaction() as session:
        session["user_id"] = 7
        session["role"] = "user"

    assert client.get("/godhood/").status_code == 403


def test_admin_dashboard_renders_metrics_and_password_safety(
    client, monkeypatch
):
    install_admin(monkeypatch)
    log_in_admin(client)
    monkeypatch.setattr(
        "app.controllers.adminController.adminRepository.dashboard_metrics",
        lambda: {
            "total_users": 12,
            "online_users": 3,
            "offline_users": 9,
            "suspended_users": 1,
            "total_posts": 24,
            "pending_registrations": 2,
        },
    )
    monkeypatch.setattr(
        "app.controllers.adminController.adminRepository.recent_users",
        lambda: [],
    )
    monkeypatch.setattr(
        "app.controllers.adminController.adminRepository.recent_audit_logs",
        lambda: [],
    )

    response = client.get("/godhood/")

    assert response.status_code == 200
    assert b"Creator overview" in response.data
    assert b"Passwords cannot be viewed." in response.data
    assert b"All feed" in response.data
    assert b"Users" in response.data


def test_admin_users_page_shows_email_status_and_actions(client, monkeypatch):
    install_admin(monkeypatch)
    log_in_admin(client)
    monkeypatch.setattr(
        "app.controllers.adminController.adminRepository.dashboard_metrics",
        lambda: {
            "total_users": 1,
            "online_users": 1,
            "offline_users": 0,
            "suspended_users": 0,
            "total_posts": 2,
            "pending_registrations": 0,
        },
    )
    monkeypatch.setattr(
        "app.controllers.adminController.adminRepository.list_users",
        lambda _search: [
            {
                "user_id": 7,
                "full_name": "Maya Shrestha",
                "username": "maya",
                "email": "maya@example.com",
                "profile_image": None,
                "account_status": "active",
                "suspended_until": None,
                "last_seen_at": datetime(2026, 7, 25),
                "created_at": datetime(2026, 7, 20),
                "email_verified": True,
                "post_count": 2,
                "is_online": True,
            }
        ],
    )

    response = client.get("/godhood/users")

    assert response.status_code == 200
    assert b"maya@example.com" in response.data
    assert b"Protected hash" in response.data
    assert b"Send to notifications" in response.data
    assert b"Delete account" in response.data
    assert b"Dark mode" in response.data
    assert b"Hours" in response.data
    assert b"Days" in response.data
    assert b"Years" in response.data


@pytest.mark.parametrize(
    ("duration", "unit", "expected_text"),
    [
        ("12", "hours", "12 hours"),
        ("14", "days", "14 days"),
        ("2", "years", "2 years"),
    ],
)
def test_admin_can_suspend_user(
    client, monkeypatch, duration, unit, expected_text
):
    install_admin(monkeypatch)
    log_in_admin(client)
    monkeypatch.setattr(
        "app.controllers.adminController.adminRepository.find_manageable_user",
        lambda _user_id: {
            "user_id": 7,
            "username": "maya",
            "email": "maya@example.com",
            "role": "user",
        },
    )
    suspended = {}
    monkeypatch.setattr(
        "app.controllers.adminController.adminRepository.suspend_user",
        lambda admin_id, user_id, until, details: suspended.update(
            admin_id=admin_id,
            user_id=user_id,
            until=until,
            details=details,
        )
        or True,
    )

    response = client.post(
        "/godhood/users/7/suspend",
        data={
            "duration": duration,
            "unit": unit,
            "reason": "Repeated spam",
        },
    )

    assert response.status_code == 302
    assert suspended["user_id"] == 7
    assert expected_text in suspended["details"]
    assert "Repeated spam" in suspended["details"]


def test_admin_rejects_suspension_beyond_unit_limit(client, monkeypatch):
    install_admin(monkeypatch)
    log_in_admin(client)
    monkeypatch.setattr(
        "app.controllers.adminController.adminRepository.find_manageable_user",
        lambda _user_id: {
            "user_id": 7,
            "username": "maya",
            "email": "maya@example.com",
            "role": "user",
        },
    )
    monkeypatch.setattr(
        "app.controllers.adminController.adminRepository.suspend_user",
        lambda *_args: pytest.fail("Invalid suspension must not reach the database"),
    )

    response = client.post(
        "/godhood/users/7/suspend",
        data={"duration": "11", "unit": "years", "reason": "Repeated spam"},
    )

    assert response.status_code == 302
