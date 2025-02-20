"""Optimize print time by combining non-overlapping images with similar settings."""

from __future__ import annotations  # For Python 3.7-3.9 compatibility

import copy
import json
import zipfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops

from constants import CANVAS_HEIGHT, CANVAS_WIDTH


def group_by_settings(image_settings: list[dict[str, Any]]) -> dict[tuple[tuple[str, Any], ...], list[dict[str, Any]]]:
    """Group images by all parameters except name and exposure time.

    Parameters
    ----------
    image_settings : list[dict[str, Any]]
        List of image settings dictionaries to group.

    Returns
    -------
    dict[tuple[tuple[str, Any], ...], list[dict[str, Any]]]
        Dictionary mapping parameter tuples to lists of image settings that share those parameters.

    """

    def get_image_key(settings: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
        return tuple((k, v) for k, v in sorted(settings.items()) if k not in {"Image file", "Layer exposure time (ms)"})

    groups: dict[tuple[tuple[str, Any], ...], list[dict[str, Any]]] = {}
    for settings in image_settings:
        key = get_image_key(settings)
        if key not in groups:
            groups[key] = []
        groups[key].append(settings)
    return groups


def check_group_overlaps(images: list[Image.Image]) -> bool:
    """Check for overlaps between images in a group.

    Parameters
    ----------
    images : list[Image.Image]
        List of PIL images to check for overlaps.

    Returns
    -------
    bool
        True if any images overlap, False otherwise.

    Notes
    -----
    This function uses PIL's ImageChops.lighter operation to detect if any
    two images in the group have overlapping non-zero pixels.

    """
    for i, img1 in enumerate(images):
        bbox1 = img1.getbbox()
        if bbox1 is None:
            continue

        for img2 in images[:i]:
            bbox2 = img2.getbbox()
            if bbox2 is None:
                continue

            # Check if bounding boxes overlap
            x1, y1, x2, y2 = bbox1
            x3, y3, x4, y4 = bbox2

            if not (x2 <= x3 or x4 <= x1 or y2 <= y3 or y4 <= y1):
                # Bounding boxes overlap, check pixel overlap
                composite = ImageChops.lighter(img1, img2)
                if composite.getbbox() is not None:
                    # Get the overlapping region
                    overlap_bbox = (max(x1, x3), max(y1, y3), min(x2, x4), min(y2, y4))
                    overlap = composite.crop(overlap_bbox)
                    if overlap.getextrema()[0] > 0:
                        return True
    return False


def optimize_layer(image_settings: list[dict[str, Any]], images: dict[str, Image.Image]) -> list[dict[str, Any]]:
    """Optimize exposures in a single layer by combining non-overlapping images with similar settings.

    Parameters
    ----------
    image_settings : list[dict[str, Any]]
        List of image settings dictionaries for the layer.
    images : dict[str, Image.Image]
        Dictionary mapping filenames to PIL Image objects. Modified in place.

    Returns
    -------
    list[dict[str, Any]]
        New list of image settings with optimized exposures.

    Notes
    -----
    This function attempts to combine images that have the same settings (except exposure time)
    and do not spatially overlap. For each group of such images, it creates new composite
    images that achieve the same result with a lower total exposure times.

    """
    image_groups = group_by_settings(image_settings)
    new_settings = []

    for group in image_groups.values():
        if len(group) <= 1:
            new_settings.extend(group)
            continue

        # Sort by exposure time to process in order
        group.sort(key=lambda x: x["Layer exposure time (ms)"])
        group_images = [images[s["Image file"]] for s in group]

        if check_group_overlaps(group_images):
            new_settings.extend(group)
            continue

        # Create optimized exposures
        prev_exposure = 0
        composite_images: dict[int, Image.Image] = {}

        # First pass: create composite images
        for i, settings in enumerate(group):
            current_exposure = settings["Layer exposure time (ms)"]
            exposure_diff = current_exposure - prev_exposure

            if exposure_diff > 0:
                # Create composite of all images from this index onwards
                composite = Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)
                for img in group_images[i:]:
                    composite = ImageChops.lighter(composite, img)

                # Only store composite if it contains non-zero pixels
                if composite.getbbox() is not None:
                    composite_images[i] = composite

            prev_exposure = current_exposure

        # Second pass: create settings for composite images
        for i, composite in composite_images.items():
            settings = copy.deepcopy(group[i])
            exposure_diff = group[i]["Layer exposure time (ms)"] - (
                0 if i == 0 else group[i - 1]["Layer exposure time (ms)"]
            )

            new_img_name = f"opt_{i}_{Path(settings['Image file']).stem}.png"
            new_setting = {**settings, "Image file": new_img_name, "Layer exposure time (ms)": exposure_diff}
            images[new_img_name] = composite
            new_settings.append(new_setting)

    return new_settings


def optimize_print_file(print_settings: dict[str, Any], images: dict[str, Image.Image]) -> None:
    """Optimize print settings by combining non-overlapping images with similar settings.

    Parameters
    ----------
    print_settings : dict[str, Any]
        Dictionary containing print settings including layers. Modified in place.
    images : dict[str, Image.Image]
        Dictionary mapping filenames to PIL Image objects. Modified in place.

    Notes
    -----
    This function processes each layer in the print settings, attempting to optimize
    the exposures by combining compatible images. Both input dictionaries are modified
    in place.
    """
    for layer_dict in print_settings.get("Layers", []):
        layer_dict["Image settings list"] = optimize_layer(layer_dict["Image settings list"], images)


def optimize_print_file_from_zip(input_path: Path, output_path: Path | None = None) -> None:
    """Load print file from zip, optimize it, and save results.

    Parameters
    ----------
    input_path : Path
        Path to input zip file containing print settings and images.
    output_path : Path | None, optional
        Path to output directory. If None, uses input name + '_optimized'.

    Notes
    -----
    This function handles the file I/O operations for the optimization process:
    1. Loads print settings and images from a zip file
    2. Optimizes the print settings and images
    3. Saves the optimized results to a new directory
    """
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_optimized"

    output_path.mkdir(exist_ok=True)
    (output_path / "slices").mkdir(exist_ok=True)

    # Load print settings and images
    images: dict[str, Image.Image] = {}
    with zipfile.ZipFile(input_path, "r") as zf:
        # Load print settings
        with zf.open("print_settings.json") as f:
            print_settings = json.load(f)

        # Load all images referenced in settings
        for layer in print_settings.get("Layers", []):
            for img_setting in layer.get("Image settings list", []):
                img_name = img_setting["Image file"]
                with zf.open(f"slices/{img_name}") as f:
                    images[img_name] = Image.open(f).convert("L")

    # Store original image names to track what to save
    original_images = set(images.keys())

    # Optimize print settings and images
    optimize_print_file(print_settings, images)

    # Save results
    output_print_file = output_path / "print_settings.json"
    output_json = json.dumps(print_settings, indent=2)
    output_print_file.write_text(output_json)

    # Only save images that are referenced in the optimized settings
    referenced_images = set()
    for layer in print_settings.get("Layers", []):
        for img_setting in layer.get("Image settings list", []):
            referenced_images.add(img_setting["Image file"])

    # Save only the optimized images (those not in original_images)
    for filename in referenced_images:
        if filename not in original_images:
            img = images[filename]
            img.save(output_path / "slices" / filename)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    else:
        print("Usage: python exposure_optimizer.py <path_to_print_file.zip>")
        sys.exit(1)
    # input_path = Path(r".\test_files\minimal_layout.zip")
    optimize_print_file_from_zip(input_path)
    print(f"Optimized files saved to {input_path.parent / f'{input_path.stem}_optimized'}")
