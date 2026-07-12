from datetime import date


def test_landing_page_renders_without_database(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Make it." in response.data
    assert b"madeby-logo.png" not in response.data
    assert b'class="brand"' in response.data


def test_footer_uses_current_year(client):
    response = client.get("/")

    assert str(date.today().year).encode() in response.data


def test_missing_page_uses_custom_404(client):
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert b"That page wandered off." in response.data


def test_security_headers_are_added(client):
    response = client.get("/")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_logged_in_navigation_uses_post_logout(client):
    with client.session_transaction() as session:
        session["user_id"] = 7
        session["role"] = "user"

    response = client.get("/")

    assert response.status_code == 200
    assert b'action="/logout"' in response.data
    assert b'method="post"' in response.data
