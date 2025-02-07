"""Generate a new print flie with scaled exposure settings and composite images.

TODO:
- Read from and write to zip files
"""

import copy
import json
from pathlib import Path

from PIL import Image, ImageChops

from constants import CANVAS_HEIGHT, CANVAS_WIDTH


def generate_new_print_file(input_dir: str, output_dir: str, config_file: str) -> None:
    """Generate a new print file with scaled exposure settings and composite images.

    Parameters
    ----------
    input_dir : str
        Input directory containing the original print settings and images.
    output_dir : str
        Output directory for the new print settings and images.
    config_file : str
        Path to the JSON file containing the group definitions.

    """
    print_settings_file = Path(input_dir) / "print_settings.json"
    input_images_dir = Path(input_dir) / "slices"

    new_print_settings_file = Path(output_dir) / "print_settings.json"
    new_images_dir = Path(output_dir) / "slices"
    new_images_dir.mkdir(parents=True, exist_ok=True)

    exp_time_key = "Layer exposure time (ms)"

    with print_settings_file.open() as f:
        original_json = json.load(f)

    # Make a complete copy so all non-layer fields remain intact
    new_json = copy.deepcopy(original_json)

    # Retrieve group info from the same structure or another location if needed
    with Path(config_file).open() as f:
        dose_config = json.load(f).get("groups", {})

    # Iterate over each layer, modifying only the Image settings
    for layer in new_json.get("Layers", []):
        new_image_settings = []

        # Original “Image settings list”
        original_imgs = layer.get("Image settings list", [])

        # For each group, generate a composite image
        for group_name, parts in dose_config.items():
            scale_factor = float(group_name) / 100.0

            # For each image in the layer
            for img_info in original_imgs:
                # Compose a new 2560x1600 image, black background
                composite = Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)
                source_path = img_info["Image file"]
                base_img = Image.open(f"{input_images_dir}/{source_path}").convert("L")

                # Place base_img in all positions for this group
                for part in parts:
                    offset_x = part["x"]
                    offset_y = part["y"]
                    temp_img = Image.new("L", (CANVAS_WIDTH, CANVAS_HEIGHT), color=0)
                    temp_img.paste(base_img, (offset_x, offset_y))
                    composite = ImageChops.lighter(composite, temp_img)

                # Save composite under a new name
                name, ext = source_path.rsplit(".", 1)
                out_filename = f"{name}_{group_name}.{ext}"
                composite.save(f"{new_images_dir}/{out_filename}")

                # Deep-copy original image settings to preserve anything else
                new_img_info = copy.deepcopy(img_info)
                new_img_info["Image file"] = out_filename

                # Scale the exposure time if present
                if exp_time_key in new_img_info:
                    new_time = int(new_img_info[exp_time_key] * scale_factor)
                    new_img_info[exp_time_key] = new_time

                new_image_settings.append(new_img_info)

        # Replace just the image settings for this layer
        layer["Image settings list"] = new_image_settings

    with new_print_settings_file.open("w") as out:
        json.dump(new_json, out, indent=2)


def main() -> None:
    """Generate a new print file with scaled exposure settings and composite images."""
    generate_new_print_file(
        input_dir="test_files/small_test",
        output_dir="test_files/small_test_result",
        config_file="json/components.json",
    )


if __name__ == "__main__":
    main()
