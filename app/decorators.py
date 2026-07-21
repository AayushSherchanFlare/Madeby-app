from datetime import UTC, datetime
from functools import wraps

from flask import abort, current_app, flash, redirect, request, session, url_for

from app.repository import userRepository


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
        session["role"] = user["role"]
        if not current_app.config["TESTING"]:
            userRepository.touch_last_seen(user_id)
        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped_view(*args, **kwargs):
        if session.get("role") != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapped_view
