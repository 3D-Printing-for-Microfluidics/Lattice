"""Optimize print time by combining non-overlapping images with similar settings."""

import copy
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops

from app.constants import CANVAS_HEIGHT, CANVAS_WIDTH
from app.print_file_utils import load_print_file, save_print_file


def group_by_settings(image_settings: list[dict[str, Any]]) -> dict[tuple[tuple[str, Any], ...], list[dict[str, Any]]]:
    """Group images where all image settings are the same except name and exposure time.

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


def check_overlap(images: list[Image.Image]) -> bool:
    """Detect if any images in the list have overlapping non-zero pixels.

    Uses a fast approach by first checking bounding boxes, then only checking pixel
    overlap for images with overlapping bounding boxes.

    Parameters
    ----------
    images : list[Image.Image]
        List of PIL images to check for overlaps.

    Returns
    -------
    bool
        True if any images overlap, False otherwise.

    """
    # Get non-empty bounding boxes for all images
    bboxes = []
    valid_images = []
    for img in images:
        bbox = img.getbbox()
        if bbox is not None:
            bboxes.append(bbox)
            valid_images.append(img)

    # Check each pair of bounding boxes for overlap
    for i, bbox1 in enumerate(bboxes):
        x1, y1, x2, y2 = bbox1
        for j in range(i):
            x3, y3, x4, y4 = bboxes[j]

            # Fast bounding box overlap check
            if x2 <= x3 or x4 <= x1 or y2 <= y3 or y4 <= y1:
                continue  # No overlap

            # Bounding boxes overlap, check pixel-level overlap
            img1 = valid_images[i]
            img2 = valid_images[j]

            # Get the overlapping region
            overlap_bbox = (max(x1, x3), max(y1, y3), min(x2, x4), min(y2, y4))

            # Crop to the overlapping region for faster comparison
            crop1 = img1.crop(overlap_bbox)
            crop2 = img2.crop(overlap_bbox)

            # Check if any pixels overlap
            overlap = ImageChops.multiply(crop1, crop2)
            if overlap.getextrema()[0] > 0:
                return True

    return False


def combine_exposures(
    group: list[dict[str, Any]],
    group_images: list[Image.Image],
) -> tuple[list[dict[str, Any]], dict[str, Image.Image]]:
    """Create optimized exposure settings and composite images by combining exposures.

    This helper function creates composite images for each unique exposure time
    and returns new settings and images.

    Parameters
    ----------
    group : list[dict[str, Any]]
        Group of image settings with the same parameters
    group_images : list[Image.Image]
        List of images corresponding to the settings in the group
    images : dict[str, Image.Image]
        Dictionary of existing images

    Returns
    -------
    tuple[list[dict[str, Any]], dict[str, Image.Image]]
        Tuple containing new settings and images

    """
    new_settings = []
    new_images = {}
    prev_exposure = 0

    # First pass: create composite images for each unique exposure time
    composites = {}
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
                composites[i] = (composite, exposure_diff)

        prev_exposure = current_exposure

    # Second pass: create settings for composite images
    for i, (composite, exposure_diff) in composites.items():
        settings = copy.deepcopy(group[i])
        new_img_name = f"{Path(settings['Image file']).stem}_opt_{i}.png"
        new_setting = {**settings, "Image file": new_img_name, "Layer exposure time (ms)": exposure_diff}

        new_images[new_img_name] = composite
        new_settings.append(new_setting)

    return new_settings, new_images


def optimize_layer(layer_dict: dict[str, Any]) -> dict[str, Any]:
    """Optimize exposure times in a single layer by combining non-overlapping images.

    This function combines images with the same settings (except exposure time)
    that don't overlap spatially, reducing total print time.

    Parameters
    ----------
    layer_dict : dict[str, Any]
        Dictionary containing layer settings including image settings list and images.

    Returns
    -------
    dict[str, Any]
        New layer dictionary with optimized image settings and images.

    """
    image_settings = layer_dict["Image settings list"]
    images = layer_dict["Images"]

    # Skip optimization if there's only one image
    if len(image_settings) <= 1:
        return layer_dict

    # Group images by their settings (except name and exposure time)
    settings_groups = group_by_settings(image_settings)
    new_settings = []
    new_images = images.copy()

    # Process each group of images with the same settings
    for group_settings in settings_groups.values():
        # Skip groups with only one image (no optimization needed)
        if len(group_settings) <= 1:
            new_settings.extend(group_settings)
            continue

        # Sort by exposure time to process in order
        group_settings.sort(key=lambda x: x["Layer exposure time (ms)"])
        group_images = [images[s["Image file"]] for s in group_settings]

        # Skip groups with overlapping images (can't be combined)
        if check_overlap(group_images):
            new_settings.extend(group_settings)
            continue

        # Create optimized exposures by combining images
        optimized_settings, optimized_images = combine_exposures(group_settings, group_images)
        new_settings.extend(optimized_settings)
        new_images.update(optimized_images)

    # Create new layer settings with the optimized settings
    new_layer_settings = copy.deepcopy(layer_dict)
    new_layer_settings["Image settings list"] = new_settings
    new_layer_settings["Images"] = new_images

    return new_layer_settings


def optimize_print_settings(
    print_settings: dict[str, Any],
    images: dict[str, Image.Image],
) -> tuple[dict[str, Any], dict[str, Image.Image]]:
    """Optimize print settings by combining non-overlapping images with similar settings.

    Parameters
    ----------
    print_settings : dict[str, Any]
        Dictionary containing print settings including layers.
    images : dict[str, Image.Image]
        Dictionary mapping filenames to PIL Image objects.

    Returns
    -------
    tuple[dict[str, Any], dict[str, Image.Image]]
        Tuple containing optimized settings and images.
    """
    new_settings = copy.deepcopy(print_settings)
    all_images = images.copy()

    # Process each layer
    for i, layer in enumerate(new_settings.get("Layers", [])):
        # Collect images needed for this layer
        layer_images = {}
        for img_setting in layer["Image settings list"]:
            img_name = img_setting["Image file"]
            if img_name in all_images:
                layer_images[img_name] = all_images[img_name]

        # Skip layers with no images
        if not layer_images:
            continue

        # Add images to the layer and optimize
        layer["Images"] = layer_images
        optimized_layer = optimize_layer(layer)
        new_settings["Layers"][i] = optimized_layer

        # Update the global images dictionary with new images
        all_images.update(optimized_layer["Images"])

        # Remove the images from the layer to save memory
        del optimized_layer["Images"]

    return new_settings, all_images


def optimize_print_file(input_path: Path, output_path: Path | None = None) -> None:
    """Load print file from zip, optimize it, and save the results to a zip file.

    Parameters
    ----------
    input_path : Path
        Path to input zip file containing print settings and images.
    output_path : Path | None, optional
        Path to output zip file. If None, uses input name + '_optimized.zip'.
    """
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_optimized.zip"

    print(f"Loading print file from {input_path}...")
    print_settings, images = load_print_file(input_path)

    print("Optimizing print settings...")
    optimized_settings, all_images = optimize_print_settings(print_settings, images)

    print(f"Saving optimized files to {output_path}...")
    save_print_file(output_path, optimized_settings, all_images)
    print(f"Optimization complete! Files saved to {output_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    else:
        print("Usage: python exposure_optimizer.py <path_to_print_file.zip>")
        sys.exit(1)
    optimize_print_file(input_path)
