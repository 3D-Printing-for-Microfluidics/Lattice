"""Test suite for exposure optimizer functions."""

import io
import json
import zipfile
from pathlib import Path
from typing import Any

import pytest
from PIL import Image, ImageChops

from app.constants import CANVAS_HEIGHT, CANVAS_WIDTH
from app.exposure_optimizer import (
    check_group_overlaps,
    group_by_settings,
    optimize_layer,
    optimize_print_file,
    optimize_print_settings,
)


@pytest.fixture
def empty_image() -> Image.Image:
    """Create an empty test image.

    Returns
    -------
    Image.Image
        Black image of size CANVAS_WIDTH x CANVAS_HEIGHT.

    """
    return Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)


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


def test_group_by_settings_empty_list() -> None:
    """Test grouping with empty input list."""
    assert group_by_settings([]) == {}


def test_group_by_settings_single_item() -> None:
    """Test grouping with a single item."""
    settings = [{"Image file": "test.png", "Layer exposure time (ms)": 1000, "param": "value"}]
    groups = group_by_settings(settings)
    assert len(groups) == 1
    assert list(groups.values())[0] == settings


def test_group_by_settings_identical_settings() -> None:
    """Test grouping with identical settings but different exposure times."""
    settings = [
        {"Image file": "img1.png", "Layer exposure time (ms)": 1000, "param": "value"},
        {"Image file": "img2.png", "Layer exposure time (ms)": 2000, "param": "value"},
    ]
    groups = group_by_settings(settings)
    assert len(groups) == 1
    assert len(list(groups.values())[0]) == 2


def test_check_group_overlaps_empty_list() -> None:
    """Test overlap detection with empty list."""
    assert not check_group_overlaps([])


def test_check_group_overlaps_single_image() -> None:
    """Test overlap detection with single image."""
    img = Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)
    img.paste(255, (0, 0, 100, 100))
    assert not check_group_overlaps([img])


def test_check_group_overlaps_empty_images(empty_image: Image.Image) -> None:
    """Test overlap detection with empty (all black) images.

    Parameters
    ----------
    empty_image : Image.Image
        Fixture providing an empty test image.

    """
    assert not check_group_overlaps([empty_image, empty_image])


def test_check_group_overlaps_touching_edges(empty_image: Image.Image) -> None:
    """Test images that touch at edges but don't overlap.

    Parameters
    ----------
    empty_image : Image.Image
        Fixture providing an empty test image.

    """
    img1 = empty_image.copy()
    img2 = empty_image.copy()

    # Create two squares that touch at (100, 100)
    img1.paste(255, (0, 0, 100, 100))
    img2.paste(255, (100, 100, 200, 200))

    assert not check_group_overlaps([img1, img2])


def test_optimize_layer_empty_list() -> None:
    """Test layer optimization with empty input list."""
    layer_dict = {"Image settings list": [], "Images": {}}
    result = optimize_layer(layer_dict)
    assert result["Image settings list"] == []
    assert result["Images"] == {}


def test_optimize_layer_single_image(sample_images: dict[str, Image.Image]) -> None:
    """Test layer optimization with single image."""
    settings = [{"Image file": "image1.png", "Layer exposure time (ms)": 1000, "Other setting": "value1"}]
    layer_dict = {"Image settings list": settings, "Images": {"image1.png": sample_images["image1.png"]}}
    result = optimize_layer(layer_dict)
    assert result["Image settings list"] == settings
    assert "image1.png" in result["Images"]


def test_optimize_layer_zero_exposure(sample_images: dict[str, Image.Image]) -> None:
    """Test layer optimization with zero exposure time."""
    settings = [
        {"Image file": "image1.png", "Layer exposure time (ms)": 0, "Other setting": "value1"},
        {"Image file": "image2.png", "Layer exposure time (ms)": 1000, "Other setting": "value1"},
    ]
    layer_dict = {
        "Image settings list": settings,
        "Images": {"image1.png": sample_images["image1.png"], "image2.png": sample_images["image2.png"]},
    }
    result = optimize_layer(layer_dict)
    assert len(result["Image settings list"]) == 1
    assert result["Image settings list"][0]["Layer exposure time (ms)"] == 1000
    assert "image1.png" in result["Images"]


def test_optimize_layer_identical_exposures(sample_images: dict[str, Image.Image]) -> None:
    """Test layer optimization with identical exposure times."""
    settings = [
        {"Image file": "image1.png", "Layer exposure time (ms)": 1000, "Other setting": "value1"},
        {"Image file": "image2.png", "Layer exposure time (ms)": 1000, "Other setting": "value1"},
    ]
    layer_dict = {
        "Image settings list": settings,
        "Images": {"image1.png": sample_images["image1.png"], "image2.png": sample_images["image2.png"]},
    }
    result = optimize_layer(layer_dict)
    assert len(result["Image settings list"]) == 1
    assert result["Image settings list"][0]["Layer exposure time (ms)"] == 1000

    # Verify that the new composite image was created
    assert any("_opt_" in name for name in result["Images"].keys())


def test_optimize_print_file_empty_layers() -> None:
    """Test print file optimization with empty layers list."""
    print_settings = {"Layers": []}
    result_settings, result_images = optimize_print_settings(print_settings, {})
    assert result_settings == {"Layers": []}
    assert result_images == {}


def test_optimize_print_file_empty_settings_list() -> None:
    """Test print file optimization with empty image settings list."""
    print_settings = {"Layers": [{"Image settings list": []}]}
    result_settings, result_images = optimize_print_settings(print_settings, {})
    assert result_settings == {"Layers": [{"Image settings list": []}]}
    assert result_images == {}


def test_optimize_print_file_missing_slices(tmp_path: Path) -> None:
    """Test handling of missing slices directory in zip."""
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        settings = {"Layers": [{"Image settings list": []}]}
        zf.writestr("print_settings.json", json.dumps(settings))

    output_path = zip_path.parent / f"{zip_path.stem}_optimized.zip"
    optimize_print_file(zip_path)

    assert output_path.exists()
    with zipfile.ZipFile(output_path, "r") as zf:
        assert "print_settings.json" in zf.namelist()


def test_optimize_print_file_invalid_json(tmp_path: Path) -> None:
    """Test handling of invalid JSON in print settings."""
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("print_settings.json", "invalid json")

    with pytest.raises(json.JSONDecodeError):
        optimize_print_file(zip_path)


def test_optimize_print_file_custom_output(tmp_path: Path) -> None:
    """Test optimization with custom output path."""
    zip_path = tmp_path / "test.zip"
    output_path = tmp_path / "custom_output.zip"

    with zipfile.ZipFile(zip_path, "w") as zf:
        settings = {"Layers": [{"Image settings list": []}]}
        zf.writestr("print_settings.json", json.dumps(settings))

    optimize_print_file(zip_path, output_path)
    assert output_path.exists()
    with zipfile.ZipFile(output_path, "r") as zf:
        assert "print_settings.json" in zf.namelist()


def test_optimize_layer_mixed_settings(sample_images: dict[str, Image.Image]) -> None:
    """Test optimization with mix of combinable and non-combinable settings."""
    settings = [
        {"Image file": "image1.png", "Layer exposure time (ms)": 1000, "Other setting": "value1"},
        {"Image file": "image2.png", "Layer exposure time (ms)": 1000, "Other setting": "value1"},
        {"Image file": "image3.png", "Layer exposure time (ms)": 1000, "Other setting": "value2"},
    ]
    layer_dict = {"Image settings list": settings, "Images": sample_images}
    result = optimize_layer(layer_dict)

    # Should have two settings: one combined (image1+image2) and one original (image3)
    assert len(result["Image settings list"]) == 2

    # Find the combined and uncombined settings
    combined = next(s for s in result["Image settings list"] if "_opt_" in s["Image file"])
    uncombined = next(s for s in result["Image settings list"] if "_opt_" not in s["Image file"])

    # Check combined setting
    assert combined["Layer exposure time (ms)"] == 1000
    assert combined["Other setting"] == "value1"

    # Check uncombined setting
    assert uncombined["Image file"] == "image3.png"
    assert uncombined["Other setting"] == "value2"

    # Verify image contents
    combined_img = result["Images"][combined["Image file"]]
    # The combined image should be the union of image1 and image2
    expected_combined = ImageChops.lighter(sample_images["image1.png"], sample_images["image2.png"])
    assert ImageChops.difference(combined_img, expected_combined).getbbox() is None


def test_optimize_layer_overlapping_images(sample_images: dict[str, Image.Image]) -> None:
    """Test that overlapping images are not combined even with identical settings."""
    settings = [
        {"Image file": "image1.png", "Layer exposure time (ms)": 1000, "Other setting": "value1"},
        {"Image file": "image3.png", "Layer exposure time (ms)": 1000, "Other setting": "value1"},
    ]
    layer_dict = {
        "Image settings list": settings,
        "Images": {"image1.png": sample_images["image1.png"], "image3.png": sample_images["image3.png"]},
    }
    result = optimize_layer(layer_dict)

    # Should keep original settings since images overlap
    assert len(result["Image settings list"]) == 2
    assert {s["Image file"] for s in result["Image settings list"]} == {"image1.png", "image3.png"}


def test_optimize_layer_progressive_exposures(sample_images: dict[str, Image.Image]) -> None:
    """Test optimization with progressive exposure times."""
    # Only use image1 and image2 for this test
    test_images = {name: img for name, img in sample_images.items() if name in ["image1.png", "image2.png"]}

    settings = [
        {"Image file": "image1.png", "Layer exposure time (ms)": 1000, "Other setting": "value1"},
        {"Image file": "image2.png", "Layer exposure time (ms)": 2000, "Other setting": "value1"},
    ]
    layer_dict = {"Image settings list": settings, "Images": test_images}
    result = optimize_layer(layer_dict)

    # Should have two optimized settings
    assert len(result["Image settings list"]) == 2

    # Sort settings by exposure time to ensure order
    sorted_settings = sorted(result["Image settings list"], key=lambda x: x["Layer exposure time (ms)"])
    first, second = sorted_settings

    # First setting should be both images exposed for 1000ms
    assert first["Layer exposure time (ms)"] == 1000
    assert "_opt_" in first["Image file"]
    first_img = result["Images"][first["Image file"]]
    expected_first = ImageChops.lighter(test_images["image1.png"], test_images["image2.png"])
    assert ImageChops.difference(first_img, expected_first).getbbox() is None

    # Second setting should be just image2 exposed for additional 1000ms
    assert second["Layer exposure time (ms)"] == 1000
    assert "_opt_" in second["Image file"]
    second_img = result["Images"][second["Image file"]]
    # The second image should be just image2 since it needs more exposure
    assert ImageChops.difference(second_img, test_images["image2.png"]).getbbox() is None
