"""Image operations used in ComponentSelector."""

import io
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops
from scipy.ndimage import find_objects, label

RegionBBox = tuple[int, int, int, int]  # (x_min, y_min, x_max, y_max)


def merge_slices(input_zip: str) -> Image.Image:
    """Read all slice images from input_zip and combine them using ImageChops.lighter."""
    with zipfile.ZipFile(input_zip, "r") as zf:
        slices = [n for n in zf.namelist() if n.startswith("slices/") and not n.endswith("/")]
        if not slices:
            msg = "No slices found in the zip file."
            raise ValueError(msg)

        with zf.open(slices[0]) as img_file:
            final_img = Image.open(img_file).convert("L")

        for slice_name in slices[1:]:
            with zf.open(slice_name) as img_file:
                img = Image.open(img_file).convert("L")
                final_img = ImageChops.lighter(final_img, img)

        return final_img


def find_white_regions(pil_img: Image.Image) -> list[RegionBBox]:
    """Find all groups of white pixels in a PIL image and return their bounding boxes."""
    # Convert the PIL image to a NumPy array
    img_array = np.array(pil_img)

    # Label connected components
    WHITE_PIXEL_VALUE = 255  # noqa:N806
    labeled_array, num_features = label(img_array == WHITE_PIXEL_VALUE)

    # Find bounding boxes for each labeled region
    bboxes = find_objects(labeled_array)

    # Convert bounding boxes to a list of tuples (x_min, y_min, x_max, y_max)
    regions = []
    for bbox in bboxes:
        y_min, x_min = bbox[0].start, bbox[1].start
        y_max, x_max = bbox[0].stop - 1, bbox[1].stop - 1
        regions.append((x_min, y_min, x_max, y_max))

    return regions


def export_cropped_slices(input_zip: str | Path, output_zip: str | Path, bbox: RegionBBox) -> None:
    """Export cropped region from all slices, preserving other zip contents."""
    x_min, y_min, x_max, y_max = bbox

    with zipfile.ZipFile(input_zip, "r") as zf_in, zipfile.ZipFile(output_zip, "w") as zf_out:
        # Copy non-slice files
        for item in zf_in.namelist():
            if not item.startswith("slices/"):
                with zf_in.open(item) as source:
                    zf_out.writestr(item, source.read())

        # Crop and save all slices
        slices = [n for n in zf_in.namelist() if n.startswith("slices/") and not n.endswith("/")]
        for name in slices:
            with zf_in.open(name) as src:
                img = Image.open(src).convert("L")
                cropped = img.crop((x_min, y_min, x_max + 1, y_max + 1))
                buf = io.BytesIO()
                cropped.save(buf, format="PNG")
                zf_out.writestr(name, buf.getvalue())


def load_component_dimensions(file_path: str) -> tuple[int, int]:
    """Return (width, height) by scanning the slices in a zip file."""
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        for file_name in zip_ref.namelist():
            if file_name.startswith("slices/") and file_name.endswith(".png"):
                with zip_ref.open(file_name) as image_file:
                    image = Image.open(image_file)
                    return image.width, image.height
    raise ValueError("No slices found in zip file.")
