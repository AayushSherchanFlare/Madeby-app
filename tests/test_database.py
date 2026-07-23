import pytest

from app.database import database_cursor


class BrokenCursorConnection:
    def __init__(self):
        self.closed = False
        self.rolled_back = False

    def cursor(self, **_kwargs):
        raise RuntimeError("cursor unavailable")

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class FakeCursor:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self, **_kwargs):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_cursor_commits_and_closes_resources(app, monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr("app.database.get_connection", lambda: connection)

    with app.app_context():
        with database_cursor(commit=True) as cursor:
            assert cursor is connection.cursor_instance

    assert connection.committed
    assert connection.cursor_instance.closed
    assert connection.closed


def test_cursor_rolls_back_and_closes_after_error(app, monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr("app.database.get_connection", lambda: connection)

    with app.app_context(), pytest.raises(ValueError, match="failed statement"):
        with database_cursor():
            raise ValueError("failed statement")

    assert connection.rolled_back
    assert connection.cursor_instance.closed
    assert connection.closed


def test_connection_closes_when_cursor_creation_fails(app, monkeypatch):
    connection = BrokenCursorConnection()
    monkeypatch.setattr("app.database.get_connection", lambda: connection)

    with app.app_context(), pytest.raises(RuntimeError, match="cursor unavailable"):
        with database_cursor():
            pass

    assert connection.rolled_back
    assert connection.closed
