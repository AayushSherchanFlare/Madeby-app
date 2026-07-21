from flask import Blueprint

from app.controllers.authController import (
    account_page,
    google_callback,
    google_login,
    login_page,
    logout_user,
    resend_code,
    register_page,
    verify_email_page,
)
from app.decorators import login_required


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    return register_page()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    return login_page()


@auth_bp.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    return verify_email_page()


@auth_bp.post("/verify-email/resend")
def resend_verification():
    return resend_code()


@auth_bp.get("/login/google")
def google():
    return google_login()


@auth_bp.get("/login/google/callback", endpoint="google_callback")
def google_callback_route():
    return google_callback()


@auth_bp.post("/logout")
def logout():
    return logout_user()


@auth_bp.get("/account")
@login_required
def account():
    return account_page()
