import secrets
from urllib.parse import urlparse

from authlib.integrations.base_client.errors import OAuthError
from flask import (
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from requests import RequestException

from app import oauth
from app.forms.authForms import (
    LoginForm,
    RegisterForm,
    ResendCodeForm,
    VerifyEmailForm,
)
from app.services.authService import (
    GoogleAuthenticationError,
    ResendTooSoon,
    RegistrationConflict,
    VerificationError,
    VerificationExpired,
    VerificationLocked,
    authenticate_user,
    login_or_create_google_user,
    resend_verification_code,
    start_email_registration,
    verify_email_registration,
)
from app.services.emailService import EmailDeliveryError


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


def _start_session(user, remember=False):
    session.clear()
    session["user_id"] = user["user_id"]
    session["role"] = user["role"]
    session.permanent = remember


def register_page():
    if session.get("user_id"):
        return redirect(url_for("social.feed"))

    form = RegisterForm()
    if form.validate_on_submit():
        try:
            pending_email = start_email_registration(
                full_name=form.full_name.data,
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
            )
        except RegistrationConflict as conflict:
            getattr(form, conflict.field).errors.append(conflict.message)
        except EmailDeliveryError:
            form.email.errors.append(
                "We could not send the verification email. Please try again."
            )
        else:
            session.clear()
            session["pending_verification_email"] = pending_email
            flash("We sent a six-digit code to your email.", "success")
            return redirect(url_for("auth.verify_email"))

    return render_template("auth/register.html", form=form)


def login_page():
    if session.get("user_id"):
        return redirect(url_for("social.feed"))

    form = LoginForm()
    if form.validate_on_submit():
        user = authenticate_user(form.email.data, form.password.data)
        if user:
            _start_session(user, bool(form.remember.data))
            flash(f"Welcome back, {user['full_name'].split()[0]}.", "success")
            destination = _safe_next_url(request.args.get("next"))
            return redirect(destination or url_for("social.feed"))
        form.email.errors.append("Email or password is incorrect.")

    return render_template("auth/login.html", form=form)


def verify_email_page():
    if session.get("user_id"):
        return redirect(url_for("social.feed"))
    email = session.get("pending_verification_email")
    if not email:
        flash("Start registration to receive a verification code.", "info")
        return redirect(url_for("auth.register"))

    form = VerifyEmailForm()
    resend_form = ResendCodeForm()
    if form.validate_on_submit():
        try:
            verify_email_registration(email, form.code.data)
        except (VerificationExpired, VerificationLocked, VerificationError) as error:
            form.code.errors.append(str(error))
        except RegistrationConflict:
            session.pop("pending_verification_email", None)
            flash("This account already exists. Log in to continue.", "info")
            return redirect(url_for("auth.login"))
        else:
            session.pop("pending_verification_email", None)
            flash("Email verified. You can now log in.", "success")
            return redirect(url_for("auth.login"))
    return render_template(
        "auth/verify_email.html",
        form=form,
        resend_form=resend_form,
        masked_email=_mask_email(email),
    )


def resend_code():
    email = session.get("pending_verification_email")
    if not email:
        return redirect(url_for("auth.register"))
    form = ResendCodeForm()
    if not form.validate_on_submit():
        return redirect(url_for("auth.verify_email"))
    try:
        resend_verification_code(email)
    except ResendTooSoon as error:
        flash(str(error), "info")
    except VerificationExpired:
        session.pop("pending_verification_email", None)
        flash("Registration expired. Please start again.", "info")
        return redirect(url_for("auth.register"))
    except EmailDeliveryError:
        flash("We could not send another code. Please try again.", "error")
    else:
        flash("A new six-digit code was sent.", "success")
    return redirect(url_for("auth.verify_email"))


def google_login():
    client = oauth.create_client("google")
    if client is None:
        flash("Google login has not been configured yet.", "info")
        return redirect(url_for("auth.login"))
    redirect_uri = current_app.config["GOOGLE_REDIRECT_URI"] or url_for(
        "auth.google_callback", _external=True
    )
    return client.authorize_redirect(
        redirect_uri,
        nonce=secrets.token_urlsafe(24),
    )


def google_callback():
    client = oauth.create_client("google")
    if client is None:
        return redirect(url_for("auth.login"))
    try:
        token = client.authorize_access_token()
        userinfo = token.get("userinfo") or client.userinfo(token=token)
        user = login_or_create_google_user(userinfo)
    except (OAuthError, GoogleAuthenticationError, KeyError, RequestException):
        current_app.logger.exception("Google authentication failed")
        flash("Google login could not be completed. Please try again.", "error")
        return redirect(url_for("auth.login"))

    _start_session(user)
    flash(f"Welcome, {user['full_name'].split()[0]}.", "success")
    return redirect(url_for("social.feed"))


def _mask_email(email):
    local, domain = email.split("@", 1)
    visible = local[:2]
    return f"{visible}{'*' * max(2, len(local) - 2)}@{domain}"


def logout_user():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.landing"))


def account_page():
    return render_template("auth/account.html", user=g.current_user)
