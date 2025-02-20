"""Generate test images for Dose customization."""

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO)


output_dir = Path(__file__).parent / "test_files" / "small_test" / "slices"


def write_image(s: str, x: int, y: int) -> None:
    """Write an image with the given string.

    Parameters
    ----------
    s : str
        The string to write.
    x: int
        The number of pixels in X.
    y: int
        The number of pixels in Y.

    """
    text = str(s)
    font_size = min(x, y) // 2
    font = ImageFont.truetype("arial.ttf", font_size)
    img = Image.new("L", (x, y), color=255)
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    position = ((x - text_width) // 2, (y - text_height) // 2)
    draw.text(position, text, fill=0, font=font)
    filename = output_dir / f"{s}.png"
    logging.info("Writing %s.png", filename)
    img.save(filename)


xy = 100
for i in range(1, 6):
    write_image(i, xy, xy)
    write_image(f"{i}a", xy, xy)
write_image("b", xy, xy)
