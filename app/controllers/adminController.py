from datetime import UTC, datetime, timedelta

from flask import abort, flash, g, redirect, render_template, request, url_for

from app.forms.adminForms import (
    AdminActionForm,
    SuspendUserForm,
    WarningMessageForm,
)
from app.repository import adminRepository
from app.services.adminService import remove_post, remove_user_account


SUSPENSION_LIMITS = {
    "hours": 8760,
    "days": 3650,
    "years": 10,
}


def _manageable_user(user_id):
    user = adminRepository.find_manageable_user(user_id)
    if not user or user["role"] != "user":
        abort(404)
    return user


def dashboard_page():
    admin = g.current_user
    return render_template(
        "admin/dashboard.html",
        current_admin=admin,
        metrics=adminRepository.dashboard_metrics(),
        recent_users=adminRepository.recent_users(),
        audit_logs=adminRepository.recent_audit_logs(),
    )


def users_page():
    admin = g.current_user
    search = (request.args.get("q") or "").strip()[:120]
    return render_template(
        "admin/users.html",
        current_admin=admin,
        users=adminRepository.list_users(search or None),
        metrics=adminRepository.dashboard_metrics(),
        search=search,
        now=datetime.now(UTC).replace(tzinfo=None),
    )


def feed_page():
    admin = g.current_user
    search = (request.args.get("q") or "").strip()[:120]
    return render_template(
        "admin/feed.html",
        current_admin=admin,
        posts=adminRepository.list_posts(search or None),
        search=search,
    )


def audit_page():
    return render_template(
        "admin/audit.html",
        current_admin=g.current_user,
        audit_logs=adminRepository.recent_audit_logs(limit=100),
    )


def suspend_user_action(user_id):
    admin = g.current_user
    user = _manageable_user(user_id)
    form = SuspendUserForm()
    if (
        not form.validate_on_submit()
        or form.duration.data > SUSPENSION_LIMITS[form.unit.data]
    ):
        flash(
            "Choose 1–8,760 hours, 1–3,650 days, or 1–10 years.",
            "error",
        )
        return redirect(url_for("godhood.users"))
    duration = form.duration.data
    unit = form.unit.data
    if unit == "hours":
        delta = timedelta(hours=duration)
    elif unit == "days":
        delta = timedelta(days=duration)
    else:
        delta = timedelta(days=365 * duration)
    until = datetime.now(UTC).replace(tzinfo=None) + delta
    reason = form.reason.data or "No reason supplied"
    details = (
        f"Suspended @{user['username']} for {duration} {unit}. "
        f"Reason: {reason}"
    )
    adminRepository.suspend_user(admin["user_id"], user_id, until, details)
    flash(f"@{user['username']} is suspended for {duration} {unit}.", "success")
    return redirect(url_for("godhood.users"))


def unsuspend_user_action(user_id):
    admin = g.current_user
    user = _manageable_user(user_id)
    form = AdminActionForm()
    if not form.validate_on_submit():
        abort(400)
    adminRepository.unsuspend_user(
        admin["user_id"],
        user_id,
        f"Restored access for @{user['username']}",
    )
    flash(f"@{user['username']} can access MadeBy again.", "success")
    return redirect(url_for("godhood.users"))


def warning_action(user_id):
    admin = g.current_user
    user = _manageable_user(user_id)
    form = WarningMessageForm()
    if not form.validate_on_submit():
        flash("Write a warning between 2 and 1,000 characters.", "error")
        return redirect(url_for("godhood.users"))
    adminRepository.send_warning(admin["user_id"], user_id, form.message.data)
    flash(f"Creator message sent to @{user['username']}.", "success")
    return redirect(url_for("godhood.users"))


def delete_user_action(user_id):
    admin = g.current_user
    user = _manageable_user(user_id)
    form = AdminActionForm()
    if not form.validate_on_submit():
        abort(400)
    remove_user_account(admin["user_id"], user)
    flash(f"@{user['username']} and their content were permanently deleted.", "success")
    return redirect(url_for("godhood.users"))


def delete_post_action(project_id):
    admin = g.current_user
    form = AdminActionForm()
    if not form.validate_on_submit():
        abort(400)
    post = remove_post(admin["user_id"], project_id)
    if not post:
        abort(404)
    flash(f"Post {project_id} was permanently deleted.", "success")
    return redirect(url_for("godhood.feed"))
