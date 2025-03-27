"""Shared utilities for loading and saving print files."""

import io
import json
import logging
import zipfile
from pathlib import Path
from typing import Any

from PIL import Image

from app.constants import CANVAS_HEIGHT, CANVAS_WIDTH

logger = logging.getLogger(__name__)


def ensure_default_image(print_settings: dict[str, Any], images: dict[str, Image.Image]) -> None:
    """Ensure print settings has a valid default image by adding a black image if needed.

    Parameters
    ----------
    print_settings : dict[str, Any]
        The print settings dictionary to update.
    images : dict[str, Image.Image]
        Dictionary mapping filenames to PIL Image objects.

    """
    if "Default layer settings" in print_settings and "Image settings" in print_settings["Default layer settings"]:
        default_image = print_settings["Default layer settings"]["Image settings"]["Image file"]
        if default_image not in images:
            black_image = Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)
            images["black.png"] = black_image
            print_settings["Default layer settings"]["Image settings"]["Image file"] = "black.png"


def collect_referenced_images(print_settings: dict[str, Any]) -> set[str]:
    """Collect all image filenames referenced in the print settings.

    Parameters
    ----------
    print_settings : dict[str, Any]
        The print settings dictionary.

    Returns
    -------
    set[str]
        Set of all referenced image filenames.

    """
    referenced_images = set()
    # Keep default image if it exists
    if "Default layer settings" in print_settings and "Image settings" in print_settings["Default layer settings"]:
        referenced_images.add(print_settings["Default layer settings"]["Image settings"]["Image file"])

    # Get images for each layer
    for layer in print_settings.get("Layers", []):
        for img_setting in layer.get("Image settings list", []):
            referenced_images.add(img_setting["Image file"])
    return referenced_images


def load_print_file(input_path: Path) -> tuple[dict[str, Any], dict[str, Image.Image]]:
    """Load print settings and images from a zip file.

    Parameters
    ----------
    input_path : Path
        Path to input zip file containing print settings and images.

    Returns
    -------
    tuple[dict[str, Any], dict[str, Image.Image]]
        Tuple containing:
        - Dictionary with print settings
        - Dictionary mapping filenames to PIL Image objects

    """
    logger.info("Loading print file from %s", input_path)
    if input_path.suffix.lower() != ".zip":
        msg = "Input path must be a .zip file."
        logger.error(msg)
        raise ValueError(msg)

    images: dict[str, Image.Image] = {}
    with zipfile.ZipFile(input_path, "r") as zf:
        logger.debug("Reading print_settings.json from zip")
        with zf.open("print_settings.json") as f:
            print_settings = json.load(f)

        # Collect unique image names to avoid reloading same file every time it is referenced
        unique_images = set()
        for layer in print_settings.get("Layers", []):
            for img_setting in layer.get("Image settings list", []):
                unique_images.add(img_setting["Image file"])

        logger.info("Loading %d unique images", len(unique_images))

        # Load all images
        for img_name in unique_images:
            try:
                with zf.open(f"slices/{img_name}") as f:
                    logger.debug("Loading image: %s", img_name)
                    images[img_name] = Image.open(f).convert("L")
            except (KeyError, OSError):
                logger.exception("Failed to load image %s", img_name)
                raise

    logger.info(
        "Print file loaded successfully: %d layers, %d images",
        len(print_settings.get("Layers", [])),
        len(images),
    )
    return print_settings, images


def save_print_file(output_path: Path, print_settings: dict[str, Any], images: dict[str, Image.Image]) -> None:
    """Save print settings and images to a zip file."""
    logger.info("Saving print file to %s", output_path)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Save print settings
        logger.debug("Writing print_settings.json")
        zf.writestr("print_settings.json", json.dumps(print_settings, indent=2))

        # Create slices directory in zip
        zf.writestr("slices/", "")

        # Save all images
        logger.info("Saving %d images", len(images))
        for img_name, img in images.items():
            logger.debug("Saving image: %s", img_name)
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            zf.writestr(f"slices/{img_name}", img_bytes.getvalue())

    logger.info("Print file saved successfully")
