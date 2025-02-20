"""Test suite for exposure optimizer functions."""

import io
import json
import zipfile
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from constants import CANVAS_HEIGHT, CANVAS_WIDTH
from exposure_optimizer import (
    check_group_overlaps,
    group_by_settings,
    optimize_layer,
    optimize_print_file,
    optimize_print_file_from_zip,
)


@pytest.fixture
def sample_image_settings() -> list[dict[str, Any]]:
    """Create sample image settings for testing.

    Returns
    -------
    list[dict[str, Any]]
        List of image settings dictionaries with varying exposure times and settings.
        Each dictionary contains 'Image file', 'Layer exposure time (ms)', and 'Other setting' keys.

    """
    return [
        {"Image file": "image1.png", "Layer exposure time (ms)": 1000, "Other setting": "value1"},
        {"Image file": "image2.png", "Layer exposure time (ms)": 2000, "Other setting": "value1"},
        {"Image file": "image3.png", "Layer exposure time (ms)": 3000, "Other setting": "value2"},
    ]


@pytest.fixture
def sample_images() -> dict[str, Image.Image]:
    """Create sample PIL images for testing.

    Returns
    -------
    dict[str, Image.Image]
        Dictionary mapping filenames to PIL Image objects. Contains three test images:
        - image1.png: White square in top-left (0, 0, 100, 100)
        - image2.png: White square in middle (200, 200, 300, 300)
        - image3.png: White square overlapping with image1 (50, 50, 150, 150)

    """
    images = {}

    # Create non-overlapping images
    img1 = Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)
    img1.paste(255, (0, 0, 100, 100))  # White square in top-left

    img2 = Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)
    img2.paste(255, (200, 200, 300, 300))  # White square in middle

    # Create overlapping image
    img3 = Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)
    img3.paste(255, (50, 50, 150, 150))  # Overlaps with img1

    images["image1.png"] = img1
    images["image2.png"] = img2
    images["image3.png"] = img3

    return images


def test_group_by_settings(sample_image_settings: list[dict[str, Any]]) -> None:
    """Test grouping of image settings.

    Parameters
    ----------
    sample_image_settings : list[dict[str, Any]]
        Fixture providing test image settings.

    """
    groups = group_by_settings(sample_image_settings)

    # Should have two groups based on "Other setting"
    assert len(groups) == 2

    # Find group with "value1"
    value1_group = None
    for group in groups.values():
        if group[0]["Other setting"] == "value1":
            value1_group = group
            break

    assert value1_group is not None
    assert len(value1_group) == 2
    assert value1_group[0]["Layer exposure time (ms)"] == 1000
    assert value1_group[1]["Layer exposure time (ms)"] == 2000


def test_check_group_overlaps(sample_images: dict[str, Image.Image]) -> None:
    """Test overlap detection between images.

    Parameters
    ----------
    sample_images : dict[str, Image.Image]
        Fixture providing test images.

    """
    # Test non-overlapping images
    non_overlapping = [sample_images["image1.png"], sample_images["image2.png"]]
    assert not check_group_overlaps(non_overlapping)

    # Test overlapping images
    overlapping = [sample_images["image1.png"], sample_images["image3.png"]]
    assert check_group_overlaps(overlapping)


def test_optimize_layer(sample_image_settings: list[dict[str, Any]], sample_images: dict[str, Image.Image]) -> None:
    """Test layer optimization.

    Parameters
    ----------
    sample_image_settings : list[dict[str, Any]]
        Fixture providing test image settings.
    sample_images : dict[str, Image.Image]
        Fixture providing test images.

    """
    # Only optimize the non-overlapping images with same settings
    optimized_settings = optimize_layer(sample_image_settings[:2], sample_images)

    # Should combine the first two images into optimized exposures
    assert len(optimized_settings) == 2
    assert all("opt_" in s["Image file"] for s in optimized_settings)


def test_optimize_print_file(sample_images: dict[str, Image.Image]) -> None:
    """Test full print file optimization.

    Parameters
    ----------
    sample_images : dict[str, Image.Image]
        Fixture providing test images.

    """
    print_settings = {
        "Layers": [
            {
                "Image settings list": [
                    {"Image file": "image1.png", "Layer exposure time (ms)": 1000, "Other setting": "value1"},
                    {"Image file": "image2.png", "Layer exposure time (ms)": 2000, "Other setting": "value1"},
                ]
            }
        ]
    }

    optimize_print_file(print_settings, sample_images)

    # Check that the layer was optimized
    layer_settings = print_settings["Layers"][0]["Image settings list"]
    assert len(layer_settings) == 2
    assert all("opt_" in s["Image file"] for s in layer_settings)


def test_optimize_print_file_from_zip(tmp_path: Path) -> None:
    """Test end-to-end optimization from zip file.

    Parameters
    ----------
    tmp_path : Path
        Pytest fixture providing temporary directory path.

    """
    # Create a temporary zip file with test data
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        # Add print settings
        settings = {
            "Layers": [
                {
                    "Image settings list": [
                        {"Image file": "image1.png", "Layer exposure time (ms)": 1000, "Other setting": "value1"},
                        {"Image file": "image2.png", "Layer exposure time (ms)": 2000, "Other setting": "value1"},
                    ]
                }
            ]
        }
        zf.writestr("print_settings.json", json.dumps(settings))

        # Add test images
        img1 = Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)
        img1.paste(255, (0, 0, 100, 100))
        img2 = Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)
        img2.paste(255, (200, 200, 300, 300))

        # Save images to bytes
        for name, img in [("image1.png", img1), ("image2.png", img2)]:
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            zf.writestr(f"slices/{name}", img_bytes.getvalue())

    # Run optimization
    optimize_print_file_from_zip(zip_path)

    # Check output directory
    output_dir = zip_path.parent / f"{zip_path.stem}_optimized"
    assert output_dir.exists()
    assert (output_dir / "print_settings.json").exists()
    assert (output_dir / "slices").exists()

    # Check optimized settings
    with open(output_dir / "print_settings.json") as f:
        optimized_settings = json.load(f)

    layer_settings = optimized_settings["Layers"][0]["Image settings list"]
    assert len(layer_settings) == 2
    assert all("opt_" in s["Image file"] for s in layer_settings)

    # Check optimized images
    assert len(list((output_dir / "slices").glob("*.png"))) == 2
