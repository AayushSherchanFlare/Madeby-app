from io import BytesIO

import pytest
from PIL import Image
from werkzeug.datastructures import FileStorage

from app.services.socialService import (
    POST_IMAGE_RATIOS,
    InvalidImage,
    save_image,
)


def image_upload(size, filename="post.png"):
    stream = BytesIO()
    Image.new("RGB", size, "#3526f3").save(stream, format="PNG")
    stream.seek(0)
    return FileStorage(stream=stream, filename=filename, content_type="image/png")


@pytest.mark.parametrize("dimensions", [(1000, 1000), (2000, 2000), (3000, 3000)])
def test_square_posts_accept_different_resolutions(app, tmp_path, dimensions):
    with app.app_context():
        filename = save_image(image_upload(dimensions), tmp_path, "1:1")

    saved = tmp_path / filename
    assert saved.exists()
    with Image.open(saved) as image:
        assert image.size == dimensions


@pytest.mark.parametrize(
    ("dimensions", "ratio", "expected_size"),
    [
        ((800, 600), "1:1", (600, 600)),
        ((2000, 3000), "9:16", (1683, 2992)),
        ((3000, 2000), "16:9", (2992, 1683)),
    ],
)
def test_post_image_is_center_cropped_to_selected_ratio(
    app, tmp_path, dimensions, ratio, expected_size
):
    with app.app_context():
        filename = save_image(image_upload(dimensions), tmp_path, ratio)

    with Image.open(tmp_path / filename) as image:
        assert image.size == expected_size
        ratio_width, ratio_height = POST_IMAGE_RATIOS[ratio]
        assert image.width * ratio_height == image.height * ratio_width


def test_unknown_post_ratio_is_rejected(app, tmp_path):
    with app.app_context(), pytest.raises(InvalidImage) as error:
        save_image(image_upload((800, 600)), tmp_path, "4:3")

    assert "Choose a 1:1, 9:16, or 16:9 photo shape." in str(error.value)
    assert list(tmp_path.iterdir()) == []


def test_post_crop_uses_the_image_center(app, tmp_path):
    source = Image.new("RGB", (800, 600), "green")
    for x in range(100):
        for y in range(600):
            source.putpixel((x, y), (255, 0, 0))
            source.putpixel((799 - x, y), (0, 0, 255))
    stream = BytesIO()
    source.save(stream, format="PNG")
    stream.seek(0)
    upload = FileStorage(stream=stream, filename="bands.png", content_type="image/png")

    with app.app_context():
        filename = save_image(upload, tmp_path, "1:1")

    with Image.open(tmp_path / filename) as cropped:
        assert cropped.size == (600, 600)
        assert cropped.getpixel((0, 300)) == (0, 128, 0)
        assert cropped.getpixel((599, 300)) == (0, 128, 0)
