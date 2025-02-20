"""Generate a new print flie with scaled exposure settings and composite images."""

import copy
import io
import json
import zipfile
from pathlib import Path

from PIL import Image, ImageChops

from constants import CANVAS_HEIGHT, CANVAS_WIDTH
from exposure_optimizer import optimize_print_file


def compose_group_image(base_image: Image.Image, group_settings: list[dict]) -> Image.Image:
    """Create a composite image by placing the base image in multiple positions.

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


def generate_layer_composites(
    layer_dict: dict,
    exposure_config: dict,
    input_images_dir: Path,
    output_dir: Path,
) -> None:
    """Generate new image settings for each group and update the layer_dict.

    Parameters
    ----------
    layer_dict : dict
        Dictionary representing layer settings. This is modified in place.
    exposure_config : dict
        Exposure configuration to determine offsets and exposure scaling.
    input_images_dir : Path
        Path to the directory containing input images.
    output_dir : Path
        Path to the directory where new images will be saved.

    Returns
    -------
    None
        Modifies layer_dict in place.

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


def new_print_file(input_path: Path, output_path: Path, layout_data: list, *, optimize_layers: bool = False) -> None:
    """Generate a new print file with scaled exposure settings and composite images.

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
    optimize_layers : bool, optional
        If True, run additional layer optimization, by default False.

    Returns
    -------
    None
        Creates a new zip file at output_path.

    """
    if input_path.suffix.lower() != ".zip":
        msg = "Input path must be a .zip file."
        raise ValueError(msg)

    # Convert flat list into group-based dictionary for processing
    exposure_config = {"groups": {}}
    for comp in layout_data:
        group = comp["group"]
        if group not in exposure_config["groups"]:
            exposure_config["groups"][group] = []
        exposure_config["groups"][group].append({"x": comp["x"], "y": comp["y"]})

    new_images: dict[str | Image.Image] = {}
    with zipfile.ZipFile(input_path, "r") as zf:
        with zf.open("print_settings.json") as f:
            print_settings = json.load(f)

        for layer_dict in print_settings.get("Layers", []):
            generate_layer_composites_zip(layer_dict, exposure_config, zf, new_images)

            # Optimize if requested
        if optimize_layers:
            optimize_print_file(print_settings, new_images)

    with zipfile.ZipFile(output_path, "w") as out_zip:
        out_zip.writestr("print_settings.json", json.dumps(print_settings, indent=2))
        for filename, content in new_images.items():
            out_zip.writestr(f"slices/{filename}", content.getvalue())


def generate_layer_composites_zip(
    layer_dict: dict,
    exposure_config: dict,
    zf: zipfile.ZipFile,
    new_images: dict,
) -> None:
    """Generate new image settings for each group and update the layer_dict.

    Parameters
    ----------
    layer_dict : dict
        Dictionary representing layer settings. Modified in place.
    exposure_config : dict
        Exposure configuration to determine offsets and exposure scaling.
    zf : zipfile.ZipFile
        The input zip file.
    new_images : dict
        Dictionary mapping filenames to BytesIO objects of generated images. Modified in place.

    Returns
    -------
    None
        Modifies layer_dict and new_images in place.

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
            new_images[out_filename] = img_bytes

            new = copy.deepcopy(old)
            new["Image file"] = out_filename
            if "Layer exposure time (ms)" in new:
                new["Layer exposure time (ms)"] = int(new["Layer exposure time (ms)"] * exp_scale)
            new_image_settings.append(new)

    layer_dict["Image settings list"] = new_image_settings


def main() -> None:
    """Generate a new print file with scaled exposure settings and composite images.

    Returns
    -------
    None
        Creates a new zip file with optimized print settings.

    """
    new_print_file(
        input_path=Path("test_files/small_test.zip"),
        output_path=Path("test_files/small_test_result.zip"),
        layout_data=json.loads(Path("json/components.json").read_text()),
    )


if __name__ == "__main__":
    main()
