from urllib.parse import urlparse

from flask import (
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.forms.authForms import LoginForm, RegisterForm
from app.repository import userRepository
from app.services.authService import (
    RegistrationConflict,
    authenticate_user,
    register_user,
)


def _safe_next_url(target):
    if not target:
        return None
    destination = urlparse(target)
    if (
        not target.startswith("/")
        or target.startswith("//")
        or "\\" in target
        or destination.scheme
        or destination.netloc
    ):
        return None
    return target


def register_page():
    if session.get("user_id"):
        return redirect(url_for("auth.account"))

    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user_id = register_user(
                full_name=form.full_name.data,
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
            )
        except RegistrationConflict as conflict:
            getattr(form, conflict.field).errors.append(conflict.message)
        else:
            session.clear()
            session["user_id"] = user_id
            session["role"] = "user"
            session.permanent = True
            flash("Welcome to MadeBy. Your account is ready.", "success")
            return redirect(url_for("auth.account"))

    return render_template("auth/register.html", form=form)


def login_page():
    if session.get("user_id"):
        return redirect(url_for("auth.account"))

    form = LoginForm()
    if form.validate_on_submit():
        user = authenticate_user(form.email.data, form.password.data)
        if user:
            session.clear()
            session["user_id"] = user["user_id"]
            session["role"] = user["role"]
            session.permanent = bool(form.remember.data)
            flash(f"Welcome back, {user['full_name'].split()[0]}.", "success")
            destination = _safe_next_url(request.args.get("next"))
            return redirect(destination or url_for("auth.account"))
        form.email.errors.append("Email or password is incorrect.")

    return render_template("auth/login.html", form=form)


def logout_user():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.landing"))


def account_page():
    user = userRepository.find_by_id(session["user_id"])
    if not user or user["account_status"] != "active":
        session.clear()
        flash("Your session is no longer available. Please log in again.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/account.html", user=user)
