from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from app.repository import socialRepository


IMAGE_SIGNATURES = {
    "jpg": lambda header: header.startswith(b"\xff\xd8\xff"),
    "jpeg": lambda header: header.startswith(b"\xff\xd8\xff"),
    "png": lambda header: header.startswith(b"\x89PNG\r\n\x1a\n"),
    "webp": lambda header: header.startswith(b"RIFF") and header[8:12] == b"WEBP",
}


class InvalidImage(ValueError):
    pass


def save_image(file_storage, folder):
    extension = Path(file_storage.filename or "").suffix.lower().lstrip(".")
    if extension not in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        raise InvalidImage("Upload a JPG, PNG, or WebP image.")

    header = file_storage.stream.read(12)
    file_storage.stream.seek(0)
    if not IMAGE_SIGNATURES[extension](header):
        raise InvalidImage("The selected file is not a valid image.")

    destination = Path(folder)
    destination.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}.{extension}"
    file_storage.save(destination / filename)
    return filename


def publish_post(user_id, content, image, category_id):
    filename = None
    if image:
        filename = save_image(
            image,
            current_app.config["PROJECT_UPLOAD_FOLDER"],
        )
    try:
        return socialRepository.create_post(user_id, content, filename, category_id)
    except Exception:
        if filename:
            (Path(current_app.config["PROJECT_UPLOAD_FOLDER"]) / filename).unlink(
                missing_ok=True
            )
        raise


def update_existing_post(user_id, post, content, image, category_id):
    filename = None
    if image:
        filename = save_image(
            image,
            current_app.config["PROJECT_UPLOAD_FOLDER"],
        )
    try:
        updated = socialRepository.update_post(
            post["project_id"],
            user_id,
            content,
            filename,
            category_id,
        )
    except Exception:
        if filename:
            (Path(current_app.config["PROJECT_UPLOAD_FOLDER"]) / filename).unlink(
                missing_ok=True
            )
        raise
    if updated and filename and post["cover_image"]:
        (Path(current_app.config["PROJECT_UPLOAD_FOLDER"]) / post["cover_image"]).unlink(
            missing_ok=True
        )
    return updated


def delete_existing_post(user_id, post):
    deleted = socialRepository.delete_post(post["project_id"], user_id)
    if deleted and post["cover_image"]:
        (Path(current_app.config["PROJECT_UPLOAD_FOLDER"]) / post["cover_image"]).unlink(
            missing_ok=True
        )
    return deleted


def change_password(user_id, current_password, new_password):
    stored = socialRepository.password_hash_for_user(user_id)
    if not stored or not check_password_hash(stored["password_hash"], current_password):
        return False
    socialRepository.update_password(user_id, generate_password_hash(new_password))
    return True
