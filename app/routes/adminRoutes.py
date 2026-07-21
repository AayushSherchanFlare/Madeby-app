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
from app.decorators import admin_required


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/")
@admin_required
def dashboard():
    return dashboard_page()


@admin_bp.get("/feed")
@admin_required
def feed():
    return feed_page()


@admin_bp.get("/users")
@admin_required
def users():
    return users_page()


@admin_bp.get("/audit")
@admin_required
def audit():
    return audit_page()


@admin_bp.post("/users/<int:user_id>/suspend")
@admin_required
def suspend_user(user_id):
    return suspend_user_action(user_id)


@admin_bp.post("/users/<int:user_id>/unsuspend")
@admin_required
def unsuspend_user(user_id):
    return unsuspend_user_action(user_id)


@admin_bp.post("/users/<int:user_id>/warning")
@admin_required
def send_warning(user_id):
    return warning_action(user_id)


@admin_bp.post("/users/<int:user_id>/delete")
@admin_required
def delete_user(user_id):
    return delete_user_action(user_id)


@admin_bp.post("/posts/<int:project_id>/delete")
@admin_required
def delete_post(project_id):
    return delete_post_action(project_id)
