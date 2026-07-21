from flask import Blueprint

from app.controllers.adminController import (
    audit_page,
    dashboard_page,
    delete_post_action,
    delete_user_action,
    feed_page,
    suspend_user_action,
    unsuspend_user_action,
    users_page,
    warning_action,
)
from app.decorators import god_required


godhood_bp = Blueprint("godhood", __name__, url_prefix="/godhood")


@godhood_bp.get("/")
@god_required
def dashboard():
    return dashboard_page()


@godhood_bp.get("/feed")
@god_required
def feed():
    return feed_page()


@godhood_bp.get("/users")
@god_required
def users():
    return users_page()


@godhood_bp.get("/audit")
@god_required
def audit():
    return audit_page()


@godhood_bp.post("/users/<int:user_id>/suspend")
@god_required
def suspend_user(user_id):
    return suspend_user_action(user_id)


@godhood_bp.post("/users/<int:user_id>/unsuspend")
@god_required
def unsuspend_user(user_id):
    return unsuspend_user_action(user_id)


@godhood_bp.post("/users/<int:user_id>/warning")
@god_required
def send_warning(user_id):
    return warning_action(user_id)


@godhood_bp.post("/users/<int:user_id>/delete")
@god_required
def delete_user(user_id):
    return delete_user_action(user_id)


@godhood_bp.post("/posts/<int:project_id>/delete")
@god_required
def delete_post(project_id):
    return delete_post_action(project_id)
