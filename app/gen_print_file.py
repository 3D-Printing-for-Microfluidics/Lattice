"""Generate a new print flie with scaled exposure settings and composite images."""

import copy
from pathlib import Path

from PIL import Image, ImageChops

from app.constants import CANVAS_HEIGHT, CANVAS_WIDTH
from app.exposure_optimizer import optimize_print_settings
from app.print_file_utils import load_print_file, save_print_file


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


def create_exposure_config(layout_data: list[dict]) -> dict:
    """Convert layout data into exposure configuration dictionary.

    Parameters
    ----------
    layout_data : list[dict]
        List of components with their groups and positions.
        Format: [{"group": "1.0", "x": 100, "y": 200}, ...].

    Returns
    -------
    dict
        Dictionary with groups as keys and lists of component positions as values.
        Format: {"groups": {"1.0": [{"x": 100, "y": 200}, ...], ...}}.

    """
    exposure_config = {"groups": {}}
    for comp in layout_data:
        group = comp["group"]
        if group not in exposure_config["groups"]:
            exposure_config["groups"][group] = []
        exposure_config["groups"][group].append({"x": comp["x"], "y": comp["y"]})
    return exposure_config


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
    exposure_config = create_exposure_config(layout_data)
    print_settings, old_images = load_print_file(input_path)
    new_images: dict[str, Image.Image] = {}

    # Process each layer
    for layer_settings in print_settings.get("Layers", []):
        old_image_settings = layer_settings.get("Image settings list", [])
        new_image_settings = []

        for group_name, group_settings in exposure_config["groups"].items():
            exp_scale = float(group_name) / 100.0
            for old_setting in old_image_settings:
                old_name = old_setting["Image file"]
                old_img = old_images[old_name]
                composite_img = gen_group_composite(old_img, group_settings)

                basename, ext = old_name.rsplit(".", 1)
                new_name = f"{basename}_{group_name}.{ext}"
                new_images[new_name] = composite_img

                new_setting = copy.deepcopy(old_setting)
                new_setting["Image file"] = new_name
                if "Layer exposure time (ms)" in new_setting:
                    new_setting["Layer exposure time (ms)"] = int(new_setting["Layer exposure time (ms)"] * exp_scale)
                new_image_settings.append(new_setting)

        layer_settings["Image settings list"] = new_image_settings

    if optimize:
        print_settings, new_images = optimize_print_settings(print_settings, new_images)

    save_print_file(output_path, print_settings, new_images)
