"""Generate a new print flie with scaled exposure settings and composite images.

TODO:
- Keep all default print settings
- Scale default layer settings
-Keep all other layer settings that are currently being deleted
"""

import json
from pathlib import Path

from PIL import Image, ImageChops


def manage_exposures(input_dir, output_dir, exposure_adjust_file, images_folder="."):
    with Path(exposure_adjust_file).open() as gf:
        group_data = json.load(gf)
    groups = group_data.get("groups", {})

    with Path(input_dir).open() as f:
        data = json.load(f)

    # result = {"Header": data.get("Header", {}), "Layers": []}
    result = data.copy()
    result["Layers"] = []
    # TODO: will need to scale main image settings, as well as copy any other layer settings that aren't exposure time

    for layer_index, layer in enumerate(data.get("Layers", [])):
        new_layer = {"Image settings list": []}
        original_imgs = layer.get("Image settings list", [])

        for group_name, parts in groups.items():
            # For each original image in the layer, build a composite for this group
            for img_info in original_imgs:
                composite = Image.new("L", (2560, 1600), color=0)
                source_path = img_info["Image file"]
                base_img = Image.open(f"{images_folder}/{source_path}").convert("L")

                # Place one copy of base_img for each part in this group
                for part in parts:
                    offset_x = part["x"]
                    offset_y = part["y"]
                    temp = Image.new("L", (2560, 1600), color=0)
                    temp.paste(base_img, (offset_x, offset_y))
                    composite = ImageChops.lighter(composite, temp)

                # Save composite to a new file
                name, ext = source_path.rsplit(".", 1)
                out_filename = f"{name}_{group_name}.{ext}"
                composite.save(f"{images_folder}/{out_filename}")

                # Create new JSON entry
                temp_img_info = img_info.copy()
                temp_img_info["Image file"] = out_filename

                scale_factor = float(group_name) / 100.0
                if "Exposure time" in temp_img_info:
                    temp_img_info["Exposure time"] = temp_img_info["Exposure time"] * scale_factor
                new_layer["Image settings list"].append(temp_img_info)

        result["Layers"].append(new_layer)
    with Path(output_dir).open("w") as f:
        json.dump(result, f, indent=2)


def main():
    input_dir = "test_files/small_test/print_settings.json"
    output_dir = "test_files/expanded_print.json"
    exposure_adjust_file = "json/rectangles_v3.json"
    manage_exposures(input_dir, output_dir, exposure_adjust_file, images_folder="images")


if __name__ == "__main__":
    main()
