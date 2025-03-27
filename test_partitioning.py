"""Visualization utilities for image group partitioning."""
# ruff: noqa: S311

import colorsys
import logging
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from graph_coloring import check_overlap, partition_images

logger = logging.getLogger(__name__)


def generate_test_images(
    count: int = 30,
    width: int = 2560,
    height: int = 1600,
) -> dict[str, Image.Image]:
    """Generate random test images with white shapes on black background."""
    images = {}

    # Random shape generator functions
    def random_rect(draw: ImageDraw.Draw, w: int, h: int) -> None:
        x1 = random.randint(0, w - 100)
        y1 = random.randint(0, h - 100)
        x2 = random.randint(x1 + 50, min(x1 + 800, w))
        y2 = random.randint(y1 + 50, min(y1 + 800, h))
        draw.rectangle((x1, y1, x2, y2), fill=255)

    def random_ellipse(draw: ImageDraw.Draw, w: int, h: int) -> None:
        x1 = random.randint(0, w - 100)
        y1 = random.randint(0, h - 100)
        x2 = random.randint(x1 + 50, min(x1 + 500, w))
        y2 = random.randint(y1 + 50, min(y1 + 500, h))
        draw.ellipse((x1, y1, x2, y2), fill=255)

    shape_funcs = [random_rect, random_ellipse]

    for i in range(count):
        # Create a black image
        img = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(img)

        # Add random white shape
        shape_func = random.choice(shape_funcs)
        shape_func(draw, width, height)

        filename = f"test_image_{i}.png"
        images[filename] = img

    return images


def visualize_image_partitioning(
    images: dict[str, Image.Image],
    groups: dict[int, list[str]],
    output_dir: str = "output",
) -> None:
    """Visualize image groups to verify non-overlapping partitioning."""
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)

    # Save original images
    _save_original_images(images, output_dir)

    # Generate distinct colors for each group
    group_colors = _get_distinct_colors(len(groups))

    # Create and save visualizations
    _create_group_visualizations(images, groups, group_colors, output_dir)
    _create_overlay_composite(images, groups, group_colors, output_dir)
    _create_master_composite(groups, output_dir)


def _save_original_images(images: dict[str, Image.Image], output_dir: str) -> None:
    """Save the original images to the output directory."""
    logger.info("Saving original images...")
    for filename, img in images.items():
        img.save(Path(output_dir) / filename)


def _get_distinct_colors(n: int) -> list[tuple[int, int, int]]:
    """Generate visually distinct colors for each group."""
    colors = []
    for i in range(n):
        hue = i / n
        # High saturation and value for vibrant colors
        r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
        colors.append((int(r * 255), int(g * 255), int(b * 255)))
    return colors


def _create_group_visualizations(
    images: dict[str, Image.Image],
    groups: dict[int, list[str]],
    group_colors: list[tuple[int, int, int]],
    output_dir: str,
) -> None:
    """Create and save visualization for each group."""
    for i, (group_id, filenames) in enumerate(groups.items()):
        # Get color for this group
        color_rgb = group_colors[i]

        # Create composite image showing all images in this group
        composite = Image.new("RGB", (2560, 1600), (0, 0, 0))
        draw = ImageDraw.Draw(composite)

        # Add each image to the composite with a colored border
        for filename in filenames:
            # Convert to RGB and colorize
            img = images[filename].convert("RGB")
            colored_img = Image.new("RGB", img.size, color_rgb)

            # Use the original image as a mask
            mask = images[filename].point(lambda p: p > 0 and 255)
            composite.paste(colored_img, (0, 0), mask)

        # Add text label for the group
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except OSError:
            font = ImageFont.load_default()

        draw.text((50, 50), f"Group {group_id}: {len(filenames)} images", fill=(255, 255, 255), font=font)

        # Save the composite
        group_filename = Path(output_dir) / f"group_{group_id}.png"
        composite.save(group_filename)
        logger.info("Saved group visualization to %s", group_filename)


def _create_overlay_composite(
    images: dict[str, Image.Image],
    groups: dict[int, list[str]],
    group_colors: list[tuple[int, int, int]],
    output_dir: str,
) -> None:
    """Create and save an overlay composite of all groups."""
    overlay_composite = Image.new("RGB", (2560, 1600), (0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay_composite)

    # Add each group to the overlay
    for i, (_, filenames) in enumerate(groups.items()):
        color_rgb = group_colors[i]
        for filename in filenames:
            colored_img = Image.new("RGB", images[filename].size, color_rgb)
            mask = images[filename].point(lambda p: p > 0 and 255)
            overlay_composite.paste(colored_img, (0, 0), mask)

    # Add legend to the overlay composite
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except OSError:
        font = ImageFont.load_default()

    overlay_draw.text(
        (50, 50),
        "All groups overlaid - different colors show non-overlapping groups",
        fill=(255, 255, 255),
        font=font,
    )

    # Add a legend showing colors for each group
    y_pos = 120
    for i, group_id in enumerate(groups.keys()):
        # Draw color square
        color = group_colors[i]
        overlay_draw.rectangle((50, y_pos, 90, y_pos + 40), fill=color)
        # Draw group name
        overlay_draw.text((100, y_pos), f"Group {group_id}", fill=(255, 255, 255), font=font)
        y_pos += 50

    # Save the overlay composite
    overlay_filename = Path(output_dir) / "all_groups_overlay.png"
    overlay_composite.save(overlay_filename)
    logger.info("Saved overlay visualization to %s", overlay_filename)


def _create_master_composite(groups: dict[int, list[str]], output_dir: str) -> None:
    """Create and save a master composite showing all groups in a grid layout."""
    num_groups = len(groups)
    grid_size = max(1, int(num_groups**0.5))  # Square root to get a balanced grid

    # Thumbnail size for each group preview
    thumb_width = 500
    thumb_height = 300

    # Create a master image with enough room for all thumbnails
    master = Image.new(
        "RGB",
        (thumb_width * min(grid_size, num_groups), thumb_height * ((num_groups + grid_size - 1) // grid_size)),
        (30, 30, 30),
    )

    # Add each group as a thumbnail
    for i, group_id in enumerate(groups.keys()):
        # Load the group image
        group_img = Image.open(Path(output_dir) / f"group_{group_id}.png")

        # Resize to thumbnail
        group_img.thumbnail((thumb_width, thumb_height))

        # Calculate position
        x = (i % grid_size) * thumb_width
        y = (i // grid_size) * thumb_height

        # Paste into master image
        master.paste(group_img, (x, y))

    # Save master composite
    master_filename = Path(output_dir) / "all_groups.png"
    master.save(master_filename)
    logger.info("Saved master visualization to %s", master_filename)


def test_image_partitioning() -> None:
    """Generate, partition, and visualize test images."""
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Set output directory
    output_dir = "test_files/partition_results"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Generate test images with more variability for better visualization
    logger.info("Generating test images...")
    images = generate_test_images(count=50, width=2560, height=1600)

    # Partition the images
    logger.info("Partitioning images...")
    groups = partition_images(images)

    # Print partitioning statistics
    logger.info("Partitioning results:")
    total_images = sum(len(group) for group in groups.values())
    logger.info("Total images: %d", total_images)
    logger.info("Number of groups: %d", len(groups))

    for group_id, filenames in groups.items():
        logger.info("Group %d: %d images", group_id, len(filenames))

    # Verify no overlaps within groups
    errors = 0
    for group_id, filenames in groups.items():
        for i, img1_name in enumerate(filenames):
            for j in range(i + 1, len(filenames)):
                img2_name = filenames[j]
                if check_overlap(images[img1_name], images[img2_name]):
                    logger.error("Overlap detected in group %d between %s and %s", group_id, img1_name, img2_name)
                    errors += 1

    if errors == 0:
        logger.info("Verification successful: No overlaps within groups")
    else:
        logger.error("Verification failed: %d overlaps detected", errors)

    # Generate visualizations
    logger.info("Generating visualizations...")
    visualize_image_partitioning(images, groups, output_dir)

    logger.info("Results saved to %s", Path(output_dir).resolve())
    logger.info("Check the following files:")
    logger.info("  all_groups_overlay.png to see all groups with different colors")
    logger.info("  all_groups.png to see all groups as thumbnails")
    logger.info("  Individual group images in separate files")

    return groups, images


if __name__ == "__main__":
    test_image_partitioning()
