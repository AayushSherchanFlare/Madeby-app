from flask import (
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.forms.socialForms import (
    CommentForm,
    PasswordChangeForm,
    PostForm,
    ProfileSettingsForm,
)
from app.repository import socialRepository, userRepository
from app.services.socialService import (
    InvalidImage,
    change_password,
    delete_existing_post,
    publish_post,
    update_existing_post,
    update_user_profile,
)


def _post_form():
    form = PostForm()
    categories = socialRepository.list_categories()
    form.category_id.choices = [(0, "No category")] + [
        (category["category_id"], category["category_name"])
        for category in categories
    ]
    return form


def _return_path(default_endpoint="social.feed"):
    target = request.form.get("next")
    if (
        target
        and target.startswith("/")
        and not target.startswith("//")
        and "\\" not in target
    ):
        return target
    return url_for(default_endpoint)


def _wants_json():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def feed_page():
    current_user = g.current_user

    category_id = request.args.get("category", type=int)
    posts = socialRepository.list_feed(
        current_user["user_id"],
        category_id=category_id,
    )
    comments = socialRepository.comments_for_projects(
        [post["project_id"] for post in posts]
    )
    for post in posts:
        post["comments"] = comments.get(post["project_id"], [])

    categories = socialRepository.list_categories()
    return render_template(
        "social/feed.html",
        current_user=current_user,
        posts=posts,
        comment_form=CommentForm(),
        suggestions=socialRepository.suggested_users(current_user["user_id"]),
        categories=categories,
        selected_category_id=category_id,
    )


def create_post_page():
    current_user = g.current_user
    form = _post_form()
    if form.validate_on_submit():
        try:
            publish_post(
                current_user["user_id"],
                form.content.data,
                form.image.data,
                form.category_id.data,
                form.aspect_ratio.data,
            )
        except InvalidImage as error:
            form.image.errors.append(str(error))
        else:
            flash("Your post is now live.", "success")
            return redirect(url_for("social.feed"))
    return render_template(
        "social/create_post.html",
        current_user=current_user,
        form=form,
    )


def post_detail_page(project_id):
    current_user = g.current_user
    post = socialRepository.find_visible_post(project_id, current_user["user_id"])
    if not post:
        abort(404)
    comments = socialRepository.comments_for_projects([project_id])
    post["comments"] = comments.get(project_id, [])
    return render_template(
        "social/post_detail.html",
        current_user=current_user,
        post=post,
    )


def edit_post_page(project_id):
    current_user = g.current_user
    post = socialRepository.find_post_for_management(
        project_id, current_user["user_id"]
    )
    if not post:
        abort(404)

    form = _post_form()
    form.existing_image = bool(post["cover_image"])
    if request.method == "GET":
        form.content.data = post["description"]
        form.category_id.data = post["category_id"] or 0
    if form.validate_on_submit():
        try:
            update_existing_post(
                current_user["user_id"],
                post,
                form.content.data,
                form.image.data,
                form.category_id.data,
                form.aspect_ratio.data,
            )
        except InvalidImage as error:
            form.image.errors.append(str(error))
        else:
            flash("Post updated.", "success")
            return redirect(url_for("social.post_detail", project_id=project_id))
    return render_template(
        "social/edit_post.html",
        current_user=current_user,
        post=post,
        form=form,
    )


def change_post_visibility(project_id):
    post = socialRepository.find_post_for_management(project_id, session["user_id"])
    if not post:
        abort(404)
    status = request.form.get("status")
    if status not in {"published", "hidden"}:
        abort(400)
    socialRepository.set_post_visibility(
        project_id,
        session["user_id"],
        status,
    )
    message = (
        "Post is visible to everyone."
        if status == "published"
        else "Post is now visible only to you on your profile."
    )
    flash(message, "success")
    return redirect(_return_path("social.profile"))


def delete_post_action(project_id):
    post = socialRepository.find_post_for_management(project_id, session["user_id"])
    if not post:
        abort(404)
    delete_existing_post(session["user_id"], post)
    flash("Post deleted.", "success")
    return redirect(url_for("social.profile"))


def save_post_action(project_id):
    post = socialRepository.find_visible_post(project_id, session["user_id"])
    if not post:
        abort(404)
    if post["user_id"] == session["user_id"]:
        abort(400)
    saved = socialRepository.toggle_saved_post(session["user_id"], project_id)
    flash("Post saved." if saved else "Post removed from saved items.", "success")
    return redirect(_return_path())


def like_post(project_id):
    if not socialRepository.find_visible_post(project_id, session["user_id"]):
        abort(404)
    liked = socialRepository.toggle_like(session["user_id"], project_id)
    if _wants_json():
        counts = socialRepository.post_engagement_counts(project_id)
        return jsonify(
            {
                "liked": liked,
                "like_count": counts["like_count"],
                "comment_count": counts["comment_count"],
            }
        )
    return redirect(_return_path())


def comment_on_post(project_id):
    if not socialRepository.find_visible_post(project_id, session["user_id"]):
        abort(404)
    form = CommentForm()
    if form.validate_on_submit():
        socialRepository.add_comment(
            session["user_id"], project_id, form.comment_text.data
        )
        if _wants_json():
            current_user = g.current_user
            counts = socialRepository.post_engagement_counts(project_id)
            return jsonify(
                {
                    "comment": {
                        "full_name": current_user["full_name"],
                        "text": form.comment_text.data,
                    },
                    "like_count": counts["like_count"],
                    "comment_count": counts["comment_count"],
                }
            )
    else:
        if _wants_json():
            return jsonify(
                {"error": "Write a comment of up to 1,000 characters."}
            ), 400
        flash("Write a comment of up to 1,000 characters.", "error")
    return redirect(_return_path())


def follow_user(target_user_id):
    if target_user_id == session["user_id"]:
        abort(400)
    target = userRepository.find_by_id(target_user_id)
    if not target or target["account_status"] != "active":
        abort(404)
    following = socialRepository.toggle_follow(session["user_id"], target_user_id)
    if _wants_json():
        return jsonify(
            {
                "following": following,
                "target_user_id": target_user_id,
            }
        )
    flash(
        f"You are now following {target['full_name']}."
        if following
        else f"You unfollowed {target['full_name']}.",
        "success",
    )
    return redirect(_return_path())


def profile_page(username=None):
    current_user = g.current_user
    username = username or current_user["username"]
    profile = socialRepository.find_profile_by_username(
        username, current_user["user_id"]
    )
    if not profile:
        abort(404)
    posts = socialRepository.posts_by_user(
        profile["user_id"], current_user["user_id"]
    )
    return render_template(
        "social/profile.html",
        current_user=current_user,
        profile=profile,
        posts=posts,
    )


def profile_connections_page(username, relationship):
    current_user = g.current_user
    profile = socialRepository.find_profile_by_username(
        username, current_user["user_id"]
    )
    if not profile:
        abort(404)
    if relationship == "followers":
        people = socialRepository.followers_for_user(
            profile["user_id"], current_user["user_id"]
        )
        heading = "Followers"
    elif relationship == "following":
        people = socialRepository.following_for_user(
            profile["user_id"], current_user["user_id"]
        )
        heading = "Following"
    else:
        abort(404)
    return render_template(
        "social/connections.html",
        current_user=current_user,
        profile=profile,
        people=people,
        relationship=relationship,
        heading=heading,
    )


def notifications_page():
    current_user = g.current_user
    notifications = socialRepository.notifications_for_user(current_user["user_id"])
    socialRepository.mark_notifications_read(current_user["user_id"])
    current_user["unread_notification_count"] = 0
    return render_template(
        "social/notifications.html",
        current_user=current_user,
        notifications=notifications,
    )


def friends_page():
    current_user = g.current_user
    return render_template(
        "social/friends.html",
        current_user=current_user,
        friends=socialRepository.friends_for_user(current_user["user_id"]),
    )


def messages_page():
    current_user = g.current_user
    return render_template("social/messages.html", current_user=current_user)


def _render_settings(current_user, profile_form=None, password_form=None):
    if profile_form is None:
        profile_form = ProfileSettingsForm(prefix="profile")
        profile_form.full_name.data = current_user["full_name"]
        profile_form.profession.data = current_user["profession"]
        profile_form.biography.data = current_user["biography"]
        profile_form.website_url.data = current_user["website_url"]
    return render_template(
        "social/settings.html",
        current_user=current_user,
        profile_form=profile_form,
        password_form=password_form or PasswordChangeForm(prefix="password"),
    )


def settings_page():
    return _render_settings(g.current_user)


def update_profile():
    current_user = g.current_user
    form = ProfileSettingsForm(prefix="profile")
    if not form.validate_on_submit():
        return _render_settings(current_user, profile_form=form)

    try:
        updated = update_user_profile(
            current_user["user_id"],
            current_user["profile_image"],
            form.full_name.data,
            form.profession.data,
            form.biography.data,
            form.website_url.data,
            form.profile_image.data,
        )
    except InvalidImage as error:
        form.profile_image.errors.append(str(error))
        return _render_settings(current_user, profile_form=form)
    if not updated:
        abort(404)
    flash("Profile updated.", "success")
    return redirect(url_for("social.settings"))


def update_password():
    current_user = g.current_user
    form = PasswordChangeForm(prefix="password")
    if not form.validate_on_submit():
        return _render_settings(current_user, password_form=form)
    if not change_password(
        current_user["user_id"],
        form.current_password.data,
        form.new_password.data,
    ):
        form.current_password.errors.append("Current password is incorrect.")
        return _render_settings(current_user, password_form=form)
    flash("Password changed successfully.", "success")
    return redirect(url_for("social.settings"))
