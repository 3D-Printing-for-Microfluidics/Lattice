"""Graph coloring algorithms for partitioning non-overlapping images into optimal groups."""

import logging
from collections import defaultdict

import networkx as nx
from PIL import Image, ImageChops

logger = logging.getLogger(__name__)


def check_overlap(img1: Image.Image, img2: Image.Image) -> bool:
    """Efficiently check if two images have overlapping white pixels."""
    # First check bounding boxes for quick rejection
    bbox1 = img1.getbbox()
    bbox2 = img2.getbbox()

    if bbox1 is None or bbox2 is None:
        return False  # One image is empty

    # Check if bounding boxes overlap
    x1, y1, x2, y2 = bbox1
    x3, y3, x4, y4 = bbox2

    if x2 <= x3 or x4 <= x1 or y2 <= y3 or y4 <= y1:
        return False  # Bounding boxes don't overlap

    # Find the overlapping region
    overlap_bbox = (max(x1, x3), max(y1, y3), min(x2, x4), min(y2, y4))

    # Crop to the overlapping region
    crop1 = img1.crop(overlap_bbox)
    crop2 = img2.crop(overlap_bbox)

    # Check if any pixels overlap
    overlap = ImageChops.multiply(crop1, crop2)
    return overlap.getbbox() is not None


def create_spatial_grid(images: dict[str, Image.Image], grid_size: int = 10) -> dict[tuple[int, int], list[str]]:
    """Create a spatial grid for efficient overlap detection."""
    grid_cells: dict[tuple[int, int], list[str]] = defaultdict(list)

    # Assign images to grid cells
    for filename, img in images.items():
        bbox = img.getbbox()
        if bbox is None:
            continue

        x1, y1, x2, y2 = bbox
        width, height = img.size

        # Calculate grid cells
        cell_x1 = max(0, x1 * grid_size // width)
        cell_y1 = max(0, y1 * grid_size // height)
        cell_x2 = min(grid_size - 1, x2 * grid_size // width)
        cell_y2 = min(grid_size - 1, y2 * grid_size // height)

        for x in range(cell_x1, cell_x2 + 1):
            for y in range(cell_y1, cell_y2 + 1):
                grid_cells[(x, y)].append(filename)

    return grid_cells


def build_conflict_graph(
    images: dict[str, Image.Image],
    grid_cells: dict[tuple[int, int], list[str]],
) -> tuple[nx.Graph, int]:
    """Build a graph where nodes are images and edges represent overlaps."""
    # Build the conflict graph
    graph = nx.Graph()
    for filename in images:
        graph.add_node(filename)

    # Check for overlaps
    logger.info("Checking for overlaps between images")
    checked_pairs: set[tuple[str, str]] = set()
    overlap_count = 0

    for cell_images in grid_cells.values():
        for i in range(len(cell_images)):
            for j in range(i + 1, len(cell_images)):
                img1_name = cell_images[i]
                img2_name = cell_images[j]

                # Skip if already checked
                pair = tuple(sorted([img1_name, img2_name]))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)

                # Check for overlap
                img1 = images[img1_name]
                img2 = images[img2_name]

                if check_overlap(img1, img2):
                    graph.add_edge(img1_name, img2_name)
                    overlap_count += 1

    return graph, overlap_count


def partition_images(images: dict[str, Image.Image]) -> dict[int, list[str]]:
    """Partition images into non-overlapping groups using graph coloring."""
    logger.info("Starting partitioning of %d images", len(images))

    # Create spatial grid for overlap detection
    grid_cells = create_spatial_grid(images)

    # Build conflict graph
    graph, overlap_count = build_conflict_graph(images, grid_cells)

    logger.info("Found %d overlapping image pairs", overlap_count)
    logger.info("Graph has %d nodes and %d edges", graph.number_of_nodes(), graph.number_of_edges())

    # Apply graph coloring
    logger.info("Applying graph coloring")
    coloring = nx.coloring.greedy_color(graph, strategy="largest_first")

    # Group by color
    groups: dict[int, list[str]] = defaultdict(list)
    for filename, color in coloring.items():
        groups[color].append(filename)

    num_groups = len(groups)
    logger.info("Partitioned into %d groups", num_groups)
    for color, group_images in groups.items():
        logger.debug("Group %d: %d images", color, len(group_images))

    return dict(groups)
