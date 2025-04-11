"""Test suite for graph coloring functionality."""

import pytest
from PIL import Image

from app.constants import CANVAS_HEIGHT, CANVAS_WIDTH
from app.graph_coloring import partition_images


@pytest.fixture
def empty_image() -> Image.Image:
    """Create an empty test image.

    Returns
    -------
    Image.Image
        Black image of size CANVAS_WIDTH x CANVAS_HEIGHT.

    """
    return Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)


def test_partition_empty_list() -> None:
    """Test partitioning with empty list."""
    partitions = partition_images({})
    assert len(partitions) == 0


def test_partition_single_image() -> None:
    """Test partitioning with single image."""
    img = Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)
    img.paste(255, (0, 0, 100, 100))
    partitions = partition_images({"test.png": img})
    assert len(partitions) == 1
    assert len(partitions[0]) == 1
    assert "test.png" in partitions[0]


def test_partition_empty_images(empty_image: Image.Image) -> None:
    """Test partitioning with empty (all black) images.

    Parameters
    ----------
    empty_image : Image.Image
        Fixture providing an empty test image.

    """
    partitions = partition_images({"img1.png": empty_image, "img2.png": empty_image})
    assert len(partitions) == 1  # Empty images can be in same group
    assert len(partitions[0]) == 2
    assert "img1.png" in partitions[0]
    assert "img2.png" in partitions[0]


def test_partition_touching_edges(empty_image: Image.Image) -> None:
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

    partitions = partition_images({"img1.png": img1, "img2.png": img2})
    assert len(partitions) == 1  # Touching edges can be in same group
    assert len(partitions[0]) == 2
    assert "img1.png" in partitions[0]
    assert "img2.png" in partitions[0]


def test_partition_overlapping_images() -> None:
    """Test that overlapping images are partitioned into separate groups."""
    img1 = Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)
    img2 = Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)

    # Create overlapping squares
    img1.paste(255, (0, 0, 100, 100))
    img2.paste(255, (50, 50, 150, 150))

    partitions = partition_images({"img1.png": img1, "img2.png": img2})
    assert len(partitions) == 2  # Overlapping images should be in separate groups
    assert len(partitions[0]) == 1
    assert len(partitions[1]) == 1
    assert "img1.png" in partitions[0] or "img1.png" in partitions[1]
    assert "img2.png" in partitions[0] or "img2.png" in partitions[1]
