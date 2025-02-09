"""Generate a new print flie with scaled exposure settings and composite images.

TODO:
- Read from and write to zip files
"""

import copy
import json
from pathlib import Path

from PIL import Image, ImageChops

from constants import CANVAS_HEIGHT, CANVAS_WIDTH


def load_json(filepath: str) -> dict:
    """Load and return JSON data from the given filepath.

    Parameters
    ----------
    filepath : str
        The path to the JSON file.

    Returns
    -------
    dict
        Parsed JSON content as a dictionary.

    """
    with Path(filepath).open() as f:
        return json.load(f)


def compose_group_image(base_image: Image.Image, group_settings: list[dict]) -> Image.Image:
    """Create a composite image by placing the base image in multiple positions based on group_settings.

    Parameters
    ----------
    base_image : Image.Image
        The base image to copy for each part.
    group_settings : list[dict]
        List of dictionaries containing 'x' and 'y' offsets.

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


def generate_layer_composites(
    layer_dict: dict,
    exposure_config: dict,
    input_images_dir: Path,
    output_dir: Path,
) -> None:
    """Generate new image settings for each group and updates the layer_dict.

    Parameters
    ----------
    layer_dict : dict
        Dictionary representing layer settings.
    exposure_config : dict
        Exposure configuration to determine offsets and exposure scaling.
    input_images_dir : Path
        Path to the directory containing input images.
    output_dir : Path
        Path to the directory where new images will be saved.

    """
    new_image_settings = []
    original_settings = layer_dict.get("Image settings list", [])

    for group_name, group_settings in exposure_config.items():
        exp_scale = float(group_name) / 100.0

        for old in original_settings:
            img_name = old["Image file"]
            original_img = Image.open(f"{input_images_dir}/{img_name}").convert("L")
            composite_img = compose_group_image(original_img, group_settings)
            new_name, ext = img_name.rsplit(".", 1)
            out_filename = f"{new_name}_{group_name}.{ext}"
            composite_img.save(f"{output_dir}/{out_filename}")
            new = copy.deepcopy(old)
            new["Image file"] = out_filename

            if "Layer exposure time (ms)" in new:
                new["Layer exposure time (ms)"] = int(new["Layer exposure time (ms)"] * exp_scale)
            new_image_settings.append(new)
    layer_dict["Image settings list"] = new_image_settings


def new_print_file(input_dir: Path, output_dir: Path, config_file: Path) -> None:
    """Generate a new print file with scaled exposure settings and composite images.

    Parameters
    ----------
    input_dir : Path
        Input directory containing the original print settings and images.
    output_dir : Path
        Output directory for the new print settings and images.
    config_file : Path
        Path to the JSON file containing the group definitions.

    """
    print_settings_file = input_dir / "print_settings.json"
    input_images_dir = input_dir / "slices"

    new_print_settings_file = output_dir / "print_settings.json"
    output_dir = output_dir / "slices"
    output_dir.mkdir(parents=True, exist_ok=True)

    original_print_settings = load_json(print_settings_file)
    new_json = copy.deepcopy(original_print_settings)
    exposure_config = load_json(config_file).get("groups", {})

    for layer_dict in new_json.get("Layers", []):
        generate_layer_composites(layer_dict, exposure_config, input_images_dir, output_dir)

    with new_print_settings_file.open("w") as out:
        json.dump(new_json, out, indent=2)


def main() -> None:
    """Generate a new print file with scaled exposure settings and composite images."""
    new_print_file(
        input_dir=Path("test_files/small_test"),
        output_dir=Path("test_files/small_test_result"),
        config_file=Path("json/components.json"),
    )


if __name__ == "__main__":
    main()
