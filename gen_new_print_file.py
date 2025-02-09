"""Generate a new print flie with scaled exposure settings and composite images.

TODO:
- Read from and write to zip files
- Integrate with GUI
"""

import copy
import io
import json
import zipfile
from pathlib import Path

from PIL import Image, ImageChops

from constants import CANVAS_HEIGHT, CANVAS_WIDTH


def load_json(filepath: Path) -> dict:
    """Load and return JSON data from the given filepath.

    Parameters
    ----------
    filepath : Path
        The path to the JSON file.

    Returns
    -------
    dict
        Parsed JSON content as a dictionary.

    """
    with filepath.open() as f:
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


def new_print_file(input_path: Path, output_path: Path, config_file: Path) -> None:
    """Generate a new print file with scaled exposure settings and composite images.

    Now supports zip files containing:
      - print_settings.json
      - a "slices" folder of images

    Parameters
    ----------
    input_path : Path
        If this is a .zip, read print_settings.json and slices from inside the zip.
        Otherwise, read from a directory containing the same structure.
    output_path : Path
        If a .zip, write the new print_settings.json and new slices folder into this output zip.
        Otherwise, write them to a directory.
    config_file : Path
        Path to the JSON file containing group definitions.

    """
    # Detect if we're dealing with zip input
    if input_path.suffix.lower() != ".zip":
        # TODO: Issue an error message
        return
    generated_files = []
    with zipfile.ZipFile(input_path, "r") as zf:
        # Load original print settings from zip
        with zf.open("print_settings.json") as f:
            original_print_settings = json.load(f)
        new_json = copy.deepcopy(original_print_settings)

        # Load group definitions
        exposure_config = (
            json.loads(zf.read(config_file.name)).get("groups", {})
            if config_file.suffix.lower() == ".json" and config_file.name in zf.namelist()
            else load_json(config_file)
        )

        # Process each layer to generate composite images
        for layer_dict in new_json.get("Layers", []):
            generate_layer_composites_zip(layer_dict, exposure_config, zf, generated_files)

    # Create a new output zip
    with zipfile.ZipFile(output_path, "w") as out_zip:
        # Write updated print_settings.json
        out_zip.writestr("print_settings.json", json.dumps(new_json, indent=2))

        # Write newly generated images
        for filename, content in generated_files:
            out_zip.writestr(f"slices/{filename}", content.getvalue())


def generate_layer_composites_zip(
    layer_dict: dict,
    exposure_config: dict,
    zf: zipfile.ZipFile,
    generated_files: list,
) -> None:
    """Generate new image settings for each group and updates the layer_dict.

    Parameters
    ----------
    layer_dict : dict
        Dictionary representing layer settings.
    exposure_config : dict
        Exposure configuration to determine offsets and exposure scaling.
    zf : zipfile.ZipFile
        The input zip file.
    generated_files : list
        List of tuples containing the filename and BytesIO of the generated images.

    """
    original_settings = layer_dict.get("Image settings list", [])
    new_image_settings = []

    for group_name, group_settings in exposure_config.get("groups", {}).items():
        exp_scale = float(group_name) / 100.0
        for old in original_settings:
            img_name = old["Image file"]
            with zf.open(f"slices/{img_name}") as img_file:
                original_img = Image.open(img_file).convert("L")

            composite_img = compose_group_image(original_img, group_settings)
            new_name, ext = img_name.rsplit(".", 1)
            out_filename = f"{new_name}_{group_name}.{ext}"

            # Save composite to in-memory bytes
            img_bytes = io.BytesIO()
            composite_img.save(img_bytes, format=ext.upper())
            img_bytes.seek(0)  # reset pointer for later reading
            generated_files.append((out_filename, img_bytes))

            new = copy.deepcopy(old)
            new["Image file"] = out_filename
            if "Layer exposure time (ms)" in new:
                new["Layer exposure time (ms)"] = int(new["Layer exposure time (ms)"] * exp_scale)
            new_image_settings.append(new)

    layer_dict["Image settings list"] = new_image_settings


def main() -> None:
    """Generate a new print file with scaled exposure settings and composite images."""
    new_print_file(
        input_path=Path("test_files/small_test.zip"),
        output_path=Path("test_files/small_test_result.zip"),
        config_file=Path("json/components.json"),
    )


if __name__ == "__main__":
    main()
