from datetime import UTC, datetime
from functools import wraps

from flask import abort, current_app, flash, g, redirect, request, session, url_for

from app.repository import userRepository


LAST_SEEN_TOUCH_INTERVAL_SECONDS = 60


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            flash("Log in to continue.", "info")
            return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
        user = userRepository.find_by_id(user_id)
        suspended_until = user.get("suspended_until") if user else None
        now = datetime.now(UTC).replace(tzinfo=None)
        if (
            not user
            or user["account_status"] != "active"
            or (suspended_until and suspended_until > now)
        ):
            session.clear()
            flash(
                "This account is suspended or unavailable. Contact the MadeBy creator.",
                "error",
            )
            return redirect(url_for("auth.login"))
        if session.get("role") != user["role"]:
            session["role"] = user["role"]
        g.current_user = user
        if not current_app.config["TESTING"]:
            now_timestamp = int(datetime.now(UTC).timestamp())
            last_touch = session.get("_last_seen_touch", 0)
            if now_timestamp - last_touch >= LAST_SEEN_TOUCH_INTERVAL_SECONDS:
                userRepository.touch_last_seen(user_id)
                session["_last_seen_touch"] = now_timestamp
        return view(*args, **kwargs)

    return wrapped_view


def god_required(view):
    @wraps(view)
    @login_required
    def wrapped_view(*args, **kwargs):
        if g.current_user["role"] != "god":
            abort(403)
        return view(*args, **kwargs)

    return wrapped_view
