"""Shared utilities for loading and saving print files."""

import io
import json
import zipfile
from pathlib import Path
from typing import Any

from PIL import Image


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
    if input_path.suffix.lower() != ".zip":
        msg = "Input path must be a .zip file."
        raise ValueError(msg)

    images: dict[str, Image.Image] = {}
    with zipfile.ZipFile(input_path, "r") as zf:
        with zf.open("print_settings.json") as f:
            print_settings = json.load(f)

        # Collect all unique image names
        unique_images = set()
        for layer in print_settings.get("Layers", []):
            for img_setting in layer.get("Image settings list", []):
                unique_images.add(img_setting["Image file"])

        # Load all images
        for img_name in unique_images:
            with zf.open(f"slices/{img_name}") as f:
                images[img_name] = Image.open(f).convert("L")

    return print_settings, images


def save_print_file(output_path: Path, print_settings: dict[str, Any], images: dict[str, Image.Image]) -> None:
    """Save print settings and images to a zip file.

    Parameters
    ----------
    output_path : Path
        Path to save the output zip file.
    print_settings : dict[str, Any]
        The print settings dictionary.
    images : dict[str, Image.Image]
        Dictionary mapping filenames to PIL Image objects.

    """
    # Collect all referenced image filenames from print settings
    referenced_images = set()
    for layer in print_settings.get("Layers", []):
        for img_setting in layer.get("Image settings list", []):
            referenced_images.add(img_setting["Image file"])

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as out_zip:
        # Save settings
        out_zip.writestr("print_settings.json", json.dumps(print_settings, indent=2))

        # Save only referenced images
        for filename in referenced_images:
            if filename in images:
                img_bytes = io.BytesIO()
                images[filename].save(img_bytes, format="PNG")
                out_zip.writestr(f"slices/{filename}", img_bytes.getvalue())
            else:
                print(f"Warning: Referenced image {filename} not found in images dictionary")
