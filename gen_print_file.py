"""Generate a new print flie with scaled exposure settings and composite images."""

import copy
import io
import json
import tempfile
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


def new_print_file(input_path: Path, output_path: Path, layout_data: dict, is_absolute: bool = True) -> None:
    """Generate a new print file with modified exposure settings based on component layout.

    Parameters
    ----------
    input_path : Path
        Path to the input component zip file.
    output_path : Path
        Path where the new print file will be saved.
    layout_data : dict
        Dictionary containing group names and component positions.
    is_absolute : bool, optional
        If True, group names are used as absolute exposure times.
        If False, group names are used as scaling factors for original exposure times.
        Default is True.

    Raises
    ------
    ValueError
        If multiple components affect the same layer (indicates overlap).
    """
    # Create temporary directory for zip operations
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Extract input zip
        with zipfile.ZipFile(input_path, "r") as zip_ref:
            zip_ref.extractall(temp_path)

        # Load exposure settings
        settings_path = temp_path / "settings.json"
        with settings_path.open("r") as f:
            settings = json.load(f)

        # Get original exposure times for scaling mode
        original_exposures = {layer["filename"]: layer["exposure_time"] for layer in settings["layers"]}

        # Create mapping of image files to their new exposure times
        exposure_map = {}
        for group_name, components in layout_data.items():
            group_value = float(group_name)
            for comp in components:
                x, y = comp["x"], comp["y"]
                w, h = comp["width"], comp["height"]
                bbox = (x, y, x + w, y + h)

                # Find all images that this component affects
                for layer in settings["layers"]:
                    filename = layer["filename"]
                    if overlaps_component(temp_path / filename, bbox):
                        if filename in exposure_map:
                            raise ValueError(
                                f"Multiple components affect layer {filename} - components must not overlap"
                            )

                        if is_absolute:
                            exposure_map[filename] = group_value
                        else:  # scaling mode
                            original_time = original_exposures[filename]
                            exposure_map[filename] = original_time * group_value

        # Update exposure times in settings
        for layer in settings["layers"]:
            filename = layer["filename"]
            if filename in exposure_map:
                layer["exposure_time"] = exposure_map[filename]

        # Save modified settings
        with settings_path.open("w") as f:
            json.dump(settings, f, indent=4)

        # Create new zip file
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
            for file_path in temp_path.rglob("*"):
                if file_path.is_file():
                    zip_ref.write(file_path, file_path.relative_to(temp_path))


def overlaps_component(image_path: Path, bbox: tuple[int, int, int, int]) -> bool:
    """Check if an image overlaps with a component's bounding box.

    Parameters
    ----------
    image_path : Path
        Path to the image file.
    bbox : tuple[int, int, int, int]
        Component bounding box (x1, y1, x2, y2).

    Returns
    -------
    bool
        True if the image overlaps with the component.

    """
    with Image.open(image_path) as img:
        # Convert image to binary (0 or 255)
        img = img.convert("L").point(lambda x: 255 if x > 128 else 0, "1")

        # Crop to bounding box
        x1, y1, x2, y2 = bbox
        crop = img.crop((x1, y1, x2, y2))

        # Check if there are any white pixels in the cropped region
        return any(crop.getdata())


def generate_layer_composites_zip(
    layer_dict: dict,
    exposure_config: dict,
    zf: zipfile.ZipFile,
    generated_files: dict,
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
    generated_files : dict
        Dictionary mapping the filename to BytesIO of the generated images.

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
            generated_files[out_filename] = img_bytes

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
        layout_data=json.loads(Path("json/components.json").read_text()),
    )


if __name__ == "__main__":
    main()
