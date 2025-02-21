"""Test suite for image operations."""

import io
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from src.image_ops import export_cropped_slices, find_white_regions, merge_slices


@pytest.fixture
def test_image() -> Image.Image:
    """Create a test image with white regions."""
    img = Image.new("L", (100, 100), 0)
    # Create two white regions
    img.paste(255, (10, 10, 20, 20))
    img.paste(255, (50, 50, 60, 60))
    return img


@pytest.fixture
def test_zip(tmp_path: Path, test_image: Image.Image) -> Path:
    """Create a test zip file with slices."""
    zip_path = tmp_path / "test.zip"

    with zipfile.ZipFile(zip_path, "w") as zf:
        # Save multiple slices
        for i in range(3):
            buf = io.BytesIO()
            test_image.save(buf, format="PNG")
            zf.writestr(f"slices/slice_{i}.png", buf.getvalue())

        # Add a non-slice file
        zf.writestr("other/file.txt", "test")

    return zip_path


def test_find_white_regions(test_image: Image.Image) -> None:
    """Test white region detection."""
    regions = find_white_regions(test_image)
    assert len(regions) == 2

    # Check region coordinates
    assert (10, 10, 19, 19) in regions
    assert (50, 50, 59, 59) in regions


def test_merge_slices(test_zip: Path) -> None:
    """Test slice merging."""
    merged = merge_slices(str(test_zip))

    # Check merged image dimensions
    assert merged.width == 100
    assert merged.height == 100

    # Check that white regions are preserved
    regions = find_white_regions(merged)
    assert len(regions) == 2


def test_merge_slices_empty_zip(tmp_path: Path) -> None:
    """Test error handling for zip with no slices."""
    empty_zip = tmp_path / "empty.zip"
    with zipfile.ZipFile(empty_zip, "w"):
        pass

    with pytest.raises(ValueError, match="No slices found"):
        merge_slices(str(empty_zip))


def test_export_cropped_slices(test_zip: Path, tmp_path: Path) -> None:
    """Test slice cropping and export."""
    output_zip = tmp_path / "output.zip"
    bbox = (10, 10, 20, 20)

    export_cropped_slices(test_zip, output_zip, bbox)

    with zipfile.ZipFile(output_zip) as zf:
        # Check that non-slice files were preserved
        assert "other/file.txt" in zf.namelist()

        # Check cropped slices
        slices = [n for n in zf.namelist() if n.startswith("slices/")]
        assert len(slices) == 3

        # Check dimensions of cropped images
        for slice_name in slices:
            with zf.open(slice_name) as f:
                img = Image.open(f)
                assert img.width == 11  # bbox width
                assert img.height == 11  # bbox height
