from flask import Blueprint

from app.controllers.socialController import (
    comment_on_post,
    create_post_page,
    change_post_visibility,
    delete_post_action,
    edit_post_page,
    feed_page,
    follow_user,
    friends_page,
    like_post,
    messages_page,
    notifications_page,
    post_detail_page,
    profile_connections_page,
    profile_page,
    save_post_action,
    settings_page,
    update_password,
    update_profile,
)
from app.decorators import login_required


social_bp = Blueprint("social", __name__)


@social_bp.get("/feed")
@login_required
def feed():
    return feed_page()


@social_bp.route("/posts/new", methods=["GET", "POST"])
@login_required
def create_post():
    return create_post_page()


@social_bp.get("/posts/<int:project_id>")
@login_required
def post_detail(project_id):
    return post_detail_page(project_id)


@social_bp.route("/posts/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(project_id):
    return edit_post_page(project_id)


@social_bp.post("/posts/<int:project_id>/visibility")
@login_required
def post_visibility(project_id):
    return change_post_visibility(project_id)


@social_bp.post("/posts/<int:project_id>/delete")
@login_required
def delete_post(project_id):
    return delete_post_action(project_id)


@social_bp.post("/posts/<int:project_id>/save")
@login_required
def save_post(project_id):
    return save_post_action(project_id)


@social_bp.post("/posts/<int:project_id>/like")
@login_required
def like(project_id):
    return like_post(project_id)


@social_bp.post("/posts/<int:project_id>/comments")
@login_required
def comment(project_id):
    return comment_on_post(project_id)


@social_bp.post("/users/<int:target_user_id>/follow")
@login_required
def follow(target_user_id):
    return follow_user(target_user_id)


@social_bp.get("/profile")
@login_required
def profile():
    return profile_page()


@social_bp.get("/users/<username>")
@login_required
def user_profile(username):
    return profile_page(username)


@social_bp.get("/users/<username>/followers")
@login_required
def followers(username):
    return profile_connections_page(username, "followers")


@social_bp.get("/users/<username>/following")
@login_required
def following(username):
    return profile_connections_page(username, "following")


@social_bp.get("/notifications")
@login_required
def notifications():
    return notifications_page()


@social_bp.get("/friends")
@login_required
def friends():
    return friends_page()


@social_bp.get("/messages")
@login_required
def messages():
    return messages_page()


@social_bp.get("/settings")
@login_required
def settings():
    return settings_page()


@social_bp.post("/settings/profile")
@login_required
def save_profile():
    return update_profile()


@social_bp.post("/settings/password")
@login_required
def save_password():
    return update_password()
