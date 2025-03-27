"""Optimize print time by combining non-overlapping images with similar settings."""

import copy
import logging
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops

from app.constants import CANVAS_HEIGHT, CANVAS_WIDTH
from app.print_file_utils import load_print_file, save_print_file

logger = logging.getLogger(__name__)


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

    logger.debug("Grouped %d images into %d distinct setting groups", len(image_settings), len(groups))
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

            # If there are any non-zero pixels in the result, there's an overlap
            if overlap.getbbox() is not None:
                logger.debug("Overlap detected between images %d and %d", i, j)
                return True

    logger.debug("No overlaps found")
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

    Returns
    -------
    tuple[list[dict[str, Any]], dict[str, Image.Image]]
        Tuple containing new settings and images

    """
    logger.debug("Combining exposures for group with %d images", len(group))
    new_settings = []
    new_images = {}
    prev_exposure = 0

    # First pass: create composite images for each unique exposure time
    composites = {}
    for i, settings in enumerate(group):
        current_exposure = settings["Layer exposure time (ms)"]
        exposure_diff = current_exposure - prev_exposure

        if exposure_diff > 0:
            logger.debug(
                "Processing exposure step %d: current=%d, prev=%d, diff=%d",
                i,
                current_exposure,
                prev_exposure,
                exposure_diff,
            )

            # Create composite of all images from this index onwards
            composite = Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)

            # Use a copy of each image to avoid modifying the original
            for j in range(i, len(group_images)):
                img_copy = group_images[j].copy()
                composite = ImageChops.lighter(composite, img_copy)

            # Only store composite if it contains non-zero pixels
            if composite.getbbox() is not None:
                composites[i] = (composite, exposure_diff)
                logger.debug("Created composite image for index %d with exposure diff %d", i, exposure_diff)

        prev_exposure = current_exposure

    # Second pass: create settings for composite images
    for i, (composite, exposure_diff) in composites.items():
        settings = copy.deepcopy(group[i])
        new_img_name = f"{Path(settings['Image file']).stem}_opt_{i}.png"
        new_setting = {**settings, "Image file": new_img_name, "Layer exposure time (ms)": exposure_diff}

        # Store a copy of the composite image to avoid any reference issues
        new_images[new_img_name] = composite.copy()
        new_settings.append(new_setting)
        logger.debug("Created optimized setting: %s with exposure %d ms", new_img_name, exposure_diff)

    logger.info("Exposure combination complete: %d source images → %d optimized images", len(group), len(new_settings))
    return new_settings, new_images


def optimize_layer(
    image_settings: list[dict[str, Any]],
    images: dict[str, Image.Image],
) -> tuple[list[dict[str, Any]], dict[str, Image.Image]]:
    """Optimize exposure times by combining non-overlapping images.

    Parameters
    ----------
    image_settings : list[dict[str, Any]]
        List of image settings dictionaries
    images : dict[str, Image.Image]
        Dictionary mapping filenames to PIL Image objects

    Returns
    -------
    tuple[list[dict[str, Any]], dict[str, Image.Image]]
        Tuple containing (optimized image settings, new/modified images)

    """
    # Skip optimization if there's only one image
    if len(image_settings) <= 1:
        logger.debug("Skipping optimization for layer with %d images", len(image_settings))
        return image_settings, {}

    # Group images by their settings (except name and exposure time)
    logger.debug("Grouping %d images by settings", len(image_settings))
    settings_groups = group_by_settings(image_settings)
    new_settings = []
    new_images = {}  # Will only contain newly created images

    # Process each group of images with the same settings
    for group_idx, group_settings in enumerate(settings_groups.values()):
        logger.debug("Processing group %d with %d images", group_idx, len(group_settings))

        # Skip groups with only one image (no optimization needed)
        if len(group_settings) <= 1:
            logger.debug("Skipping optimization for group with single image")
            new_settings.extend(group_settings)
            continue

        # Sort by exposure time to process in order
        group_settings.sort(key=lambda x: x["Layer exposure time (ms)"])

        # Create a list of image copies to avoid modifying originals
        group_images = [images[s["Image file"]].copy() for s in group_settings]

        # Skip groups with overlapping images (can't be combined)
        logger.debug("Checking for overlaps in group %d", group_idx)
        if check_overlap(group_images):
            logger.debug("Skipping optimization for group with overlapping images")
            new_settings.extend(group_settings)
            continue

        # Create optimized exposures by combining images
        logger.debug("Optimizing exposures for group %d", group_idx)
        optimized_settings, optimized_images = combine_exposures(group_settings, group_images)
        new_settings.extend(optimized_settings)
        new_images.update(optimized_images)
        logger.debug("Created %d optimized images for group %d", len(optimized_images), group_idx)

    logger.info(
        "Layer optimization complete: %d input images → %d output images, %d new images created",
        len(image_settings),
        len(new_settings),
        len(new_images),
    )
    return new_settings, new_images


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
    logger.info("Starting print settings optimization with %d images", len(images))
    new_settings = copy.deepcopy(print_settings)
    all_images = copy.deepcopy(images)  # Deep copy to avoid modifying original images

    total_layers = len(new_settings.get("Layers", []))
    logger.info("Processing %d layers", total_layers)

    # Process each layer
    for i, layer in enumerate(new_settings.get("Layers", [])):
        logger.debug("Processing layer %d/%d", i + 1, total_layers)

        # Get image settings and filter for valid images
        image_settings = layer.get("Image settings list", [])
        if not image_settings:
            logger.debug("Skipping layer %d: no image settings", i + 1)
            continue

        # Get only the images needed for this layer's settings
        layer_images = {}
        for img_setting in image_settings:
            img_name = img_setting["Image file"]
            if img_name in all_images:
                layer_images[img_name] = all_images[img_name]
            else:
                logger.warning("Image %s not found in available images", img_name)

        # Skip layers with no valid images
        if not layer_images:
            logger.debug("Skipping layer %d: no valid images found", i + 1)
            continue

        logger.info("Optimizing layer %d with %d images", i + 1, len(layer_images))
        optimized_settings, new_images = optimize_layer(image_settings, layer_images)

        # Update the layer with optimized settings
        new_settings["Layers"][i]["Image settings list"] = optimized_settings

        # Update the global images dictionary with new images
        all_images.update(new_images)
        logger.debug("Added %d new images to global image collection", len(new_images))

    logger.info("Print settings optimization complete: total images: %d", len(all_images))
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

    logger.info("Starting print file optimization: %s → %s", input_path, output_path)

    try:
        logger.info("Loading print file from %s", input_path)
        print_settings, images = load_print_file(input_path)
        logger.debug("Loaded %d images from input file", len(images))

        logger.info("Optimizing print settings")
        optimized_settings, all_images = optimize_print_settings(print_settings, images)
        logger.debug("Optimization complete: %d total images after optimization", len(all_images))

        logger.info("Saving optimized files to %s", output_path)
        save_print_file(output_path, optimized_settings, all_images)
        logger.info("Optimization complete! Files saved successfully")

    except Exception:
        logger.exception("Failed to optimize print file")
        raise


if __name__ == "__main__":
    import sys

    from app.logging_setup import setup_logging

    setup_logging()

    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
        logger.info("Starting optimization with input file: %s", input_path)
    else:
        logger.error("No input file specified")
        logger.info("Usage: python exposure_optimizer.py <path_to_print_file.zip>")
        sys.exit(1)
    optimize_print_file(input_path)
