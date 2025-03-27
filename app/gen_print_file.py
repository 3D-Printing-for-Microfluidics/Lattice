"""Generate a new print file with scaled exposure settings and composite images."""

import copy
import logging
from pathlib import Path

from PIL import Image, ImageChops

from app.constants import CANVAS_HEIGHT, CANVAS_WIDTH
from app.exposure_optimizer import optimize_print_settings
from app.print_file_utils import load_print_file, save_print_file

logger = logging.getLogger(__name__)


def gen_group_composite(base_image: Image.Image, group_settings: list[dict]) -> Image.Image:
    """Generate a composite image by placing the base image in multiple positions.

    Parameters
    ----------
    base_image : Image.Image
        The base image to copy for each part.
    group_settings : list[dict]
        List of dictionaries containing 'x' and 'y' offsets where the base image should be placed.

    Returns
    -------
    Image.Image
        The composite image combining all parts.

    """
    composite_image = Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)
    for component in group_settings:
        offset_x = component["x"]
        offset_y = component["y"]
        temp_img = Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)
        temp_img.paste(base_image, (offset_x, offset_y))
        composite_image = ImageChops.lighter(composite_image, temp_img)
    return composite_image


def create_exposure_config(layout_data: list) -> dict:
    """Create exposure groups from component layout data.

    Parameters
    ----------
    layout_data : list
        List of components with their groups and positions.
        Format: [{"group": "1.0", "x": 100, "y": 200}, ...].

    Returns
    -------
    dict
        Dictionary with groups mapping to lists of component settings.

    """
    config = {"groups": {}}
    for component in layout_data:
        group_name = component["group"]
        if group_name not in config["groups"]:
            config["groups"][group_name] = []
        config["groups"][group_name].append({"x": component["x"], "y": component["y"]})

    logger.info("Created exposure config with %d groups", len(config["groups"]))
    for group_name, components in config["groups"].items():
        logger.debug("Group %s: %d components", group_name, len(components))

    return config


def new_print_file(input_path: Path, output_path: Path, layout_data: list, *, optimize: bool = False) -> None:
    """Create a new zip file at output_path with scaled exposure settings and composite images.

    Input zip file must contain:
      - print_settings.json
      - a "slices" folder of images

    Parameters
    ----------
    input_path : Path
        Path to the input component .zip file.
    output_path : Path
        Path for the output .zip file.
    layout_data : list
        List of components with their groups and positions.
        Format: [{"group": "1.0", "x": 100, "y": 200}, ...].
    optimize : bool, optional
        If True, run additional layer optimization, by default False.

    Returns
    -------
    None
        Creates a new zip file at output_path.

    """
    logger.info("Generating new print file: %s → %s", input_path, output_path)
    logger.info("Layout contains %d components, optimize=%s", len(layout_data), optimize)

    exposure_config = create_exposure_config(layout_data)

    logger.info("Loading input print file")
    print_settings, old_images = load_print_file(input_path)
    logger.debug("Loaded %d images from input file", len(old_images))

    new_images: dict[str, Image.Image] = {}

    # Process each layer
    layers_count = len(print_settings.get("Layers", []))
    logger.info("Processing %d layers", layers_count)

    for layer_idx, layer_settings in enumerate(print_settings.get("Layers", [])):
        logger.debug("Processing layer %d/%d", layer_idx + 1, layers_count)
        old_image_settings = layer_settings.get("Image settings list", [])
        new_image_settings = []

        for group_name, group_settings in exposure_config["groups"].items():
            exp_scale = float(group_name) / 100.0
            logger.debug(
                "Processing group %s with scale factor %.2f, %d components",
                group_name,
                exp_scale,
                len(group_settings),
            )

            for old_setting in old_image_settings:
                old_name = old_setting["Image file"]
                old_img = old_images[old_name]

                logger.debug("Generating composite for image %s in group %s", old_name, group_name)
                composite_img = gen_group_composite(old_img, group_settings)

                basename, ext = old_name.rsplit(".", 1)
                new_name = f"{basename}_{group_name}.{ext}"
                new_images[new_name] = composite_img

                new_setting = copy.deepcopy(old_setting)
                new_setting["Image file"] = new_name
                if "Layer exposure time (ms)" in new_setting:
                    original_exposure = new_setting["Layer exposure time (ms)"]
                    new_setting["Layer exposure time (ms)"] = int(original_exposure * exp_scale)
                    logger.debug(
                        "Scaled exposure: %d → %d ms (%.2fx)",
                        original_exposure,
                        new_setting["Layer exposure time (ms)"],
                        exp_scale,
                    )
                new_image_settings.append(new_setting)

        layer_settings["Image settings list"] = new_image_settings
        logger.debug(
            "Layer %d processed: %d input settings → %d output settings",
            layer_idx + 1,
            len(old_image_settings),
            len(new_image_settings),
        )

    logger.info("Created %d composite images", len(new_images))

    if optimize:
        logger.info("Running exposure optimization")
        print_settings, new_images = optimize_print_settings(print_settings, new_images)
        logger.info("Optimization complete, %d total images", len(new_images))

    logger.info("Saving print file to %s", output_path)
    save_print_file(output_path, print_settings, new_images)
    logger.info("Print file generated successfully")
