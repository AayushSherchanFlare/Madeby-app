from flask import Blueprint

from app.controllers.authController import (
    account_page,
    login_page,
    logout_user,
    register_page,
)
from app.decorators import login_required


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    return register_page()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    return login_page()


@auth_bp.post("/logout")
@login_required
def logout():
    return logout_user()


@auth_bp.get("/account")
@login_required
def account():
    return account_page()
