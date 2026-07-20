from io import BytesIO

import pytest
from PIL import Image
from werkzeug.datastructures import FileStorage

from app.services.socialService import (
    POST_IMAGE_RESOLUTIONS,
    InvalidImage,
    save_image,
)


def image_upload(size, filename="post.png"):
    stream = BytesIO()
    Image.new("RGB", size, "#3526f3").save(stream, format="PNG")
    stream.seek(0)
    return FileStorage(stream=stream, filename=filename, content_type="image/png")


@pytest.mark.parametrize("dimensions", sorted(POST_IMAGE_RESOLUTIONS))
def test_supported_post_resolutions_are_saved(app, tmp_path, dimensions):
    with app.app_context():
        filename = save_image(
            image_upload(dimensions),
            tmp_path,
            POST_IMAGE_RESOLUTIONS,
        )

    saved = tmp_path / filename
    assert saved.exists()
    with Image.open(saved) as image:
        assert image.size == dimensions


def test_unsupported_post_resolution_is_rejected(app, tmp_path):
    with app.app_context(), pytest.raises(InvalidImage) as error:
        save_image(
            image_upload((800, 600)),
            tmp_path,
            POST_IMAGE_RESOLUTIONS,
        )

    assert "1000×1000, 1920×1080, or 1080×1920" in str(error.value)
    assert list(tmp_path.iterdir()) == []
