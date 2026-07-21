from pathlib import Path

from flask import current_app

from app.repository import adminRepository


def remove_user_account(admin_user_id, user):
    details = f"Deleted user @{user['username']} ({user['email']})"
    deleted, images = adminRepository.delete_user(
        admin_user_id,
        user["user_id"],
        details,
    )
    if deleted:
        upload_folder = Path(current_app.config["PROJECT_UPLOAD_FOLDER"])
        for image in images:
            (upload_folder / image).unlink(missing_ok=True)
        if user.get("profile_image"):
            (
                Path(current_app.config["PROFILE_UPLOAD_FOLDER"])
                / user["profile_image"]
            ).unlink(missing_ok=True)
        if user.get("cover_image"):
            (
                Path(current_app.config["COVER_UPLOAD_FOLDER"])
                / user["cover_image"]
            ).unlink(missing_ok=True)
    return deleted


def remove_post(admin_user_id, project_id):
    post = adminRepository.delete_post(admin_user_id, project_id)
    if post and post["cover_image"]:
        (
            Path(current_app.config["PROJECT_UPLOAD_FOLDER"])
            / post["cover_image"]
        ).unlink(missing_ok=True)
    return post
