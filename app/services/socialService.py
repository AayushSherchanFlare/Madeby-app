from pathlib import Path
from uuid import uuid4

from flask import current_app
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.security import check_password_hash, generate_password_hash

from app.repository import socialRepository


IMAGE_SIGNATURES = {
    "jpg": lambda header: header.startswith(b"\xff\xd8\xff"),
    "jpeg": lambda header: header.startswith(b"\xff\xd8\xff"),
    "png": lambda header: header.startswith(b"\x89PNG\r\n\x1a\n"),
    "webp": lambda header: header.startswith(b"RIFF") and header[8:12] == b"WEBP",
}
POST_IMAGE_RATIOS = {
    "1:1": (1, 1),
    "9:16": (9, 16),
    "16:9": (16, 9),
}


class InvalidImage(ValueError):
    pass


def _remove_image(folder, filename):
    if filename:
        (Path(folder) / filename).unlink(missing_ok=True)


def _center_crop(image, ratio):
    ratio_width, ratio_height = POST_IMAGE_RATIOS[ratio]
    scale = min(image.width // ratio_width, image.height // ratio_height)
    if scale < 1:
        raise InvalidImage("The selected image is too small for that photo shape.")
    crop_width = ratio_width * scale
    crop_height = ratio_height * scale
    left = (image.width - crop_width) // 2
    top = (image.height - crop_height) // 2
    return image.crop((left, top, left + crop_width, top + crop_height))


def save_image(file_storage, folder, crop_ratio=None):
    extension = Path(file_storage.filename or "").suffix.lower().lstrip(".")
    if extension not in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        raise InvalidImage("Upload a JPG, PNG, or WebP image.")

    header = file_storage.stream.read(12)
    file_storage.stream.seek(0)
    if not IMAGE_SIGNATURES[extension](header):
        raise InvalidImage("The selected file is not a valid image.")

    try:
        with Image.open(file_storage.stream) as image:
            image.load()
            prepared_image = ImageOps.exif_transpose(image)
            if crop_ratio:
                if crop_ratio not in POST_IMAGE_RATIOS:
                    raise InvalidImage("Choose a 1:1, 9:16, or 16:9 photo shape.")
                prepared_image = _center_crop(prepared_image, crop_ratio)
            else:
                prepared_image = prepared_image.copy()
    except (UnidentifiedImageError, OSError, SyntaxError):
        raise InvalidImage("The selected file is damaged or is not a valid image.")
    finally:
        file_storage.stream.seek(0)

    destination = Path(folder)
    destination.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}.{extension}"
    if extension in {"jpg", "jpeg"} and prepared_image.mode not in {"RGB", "L"}:
        prepared_image = prepared_image.convert("RGB")
    if extension == "png":
        save_options = {"optimize": True}
    elif extension == "webp":
        save_options = {"quality": 90, "method": 4}
    else:
        save_options = {"quality": 90, "optimize": True}
    prepared_image.save(destination / filename, **save_options)
    prepared_image.close()
    return filename


def publish_post(user_id, content, image, category_id, aspect_ratio="1:1"):
    filename = None
    if image:
        filename = save_image(
            image,
            current_app.config["PROJECT_UPLOAD_FOLDER"],
            aspect_ratio,
        )
    try:
        return socialRepository.create_post(user_id, content, filename, category_id)
    except Exception:
        _remove_image(current_app.config["PROJECT_UPLOAD_FOLDER"], filename)
        raise


def update_existing_post(
    user_id,
    post,
    content,
    image,
    category_id,
    aspect_ratio="1:1",
):
    filename = None
    if image:
        filename = save_image(
            image,
            current_app.config["PROJECT_UPLOAD_FOLDER"],
            aspect_ratio,
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
        _remove_image(current_app.config["PROJECT_UPLOAD_FOLDER"], filename)
        raise
    if not updated:
        _remove_image(current_app.config["PROJECT_UPLOAD_FOLDER"], filename)
    elif filename:
        _remove_image(
            current_app.config["PROJECT_UPLOAD_FOLDER"],
            post["cover_image"],
        )
    return updated


def delete_existing_post(user_id, post):
    deleted = socialRepository.delete_post(post["project_id"], user_id)
    if deleted:
        _remove_image(
            current_app.config["PROJECT_UPLOAD_FOLDER"],
            post["cover_image"],
        )
    return deleted


def update_user_profile(
    user_id,
    current_profile_image,
    full_name,
    profession,
    biography,
    website_url,
    image,
):
    filename = None
    if image:
        filename = save_image(
            image,
            current_app.config["PROFILE_UPLOAD_FOLDER"],
        )
    try:
        updated = socialRepository.update_profile(
            user_id,
            full_name,
            profession,
            biography,
            website_url,
            filename,
        )
    except Exception:
        _remove_image(current_app.config["PROFILE_UPLOAD_FOLDER"], filename)
        raise
    if not updated:
        _remove_image(current_app.config["PROFILE_UPLOAD_FOLDER"], filename)
        return filename is None
    if filename:
        _remove_image(
            current_app.config["PROFILE_UPLOAD_FOLDER"],
            current_profile_image,
        )
    return True


def change_password(user_id, current_password, new_password):
    stored = socialRepository.password_hash_for_user(user_id)
    if not stored or not check_password_hash(stored["password_hash"], current_password):
        return False
    socialRepository.update_password(user_id, generate_password_hash(new_password))
    return True
