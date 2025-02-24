"""Test suite for print file generation."""

import io
import json
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from src.gen_print_file import new_print_file


@pytest.fixture
def test_component_zip(tmp_path: Path) -> Path:
    """Create a test component zip file."""
    zip_path = tmp_path / "test_component.zip"

    with zipfile.ZipFile(zip_path, "w") as zf:
        # Create test print settings
        settings = {
            "Layers": [
                {
                    "Layer height (mm)": 0.05,
                    "Exposure time (ms)": 1000,
                    "Image settings list": [
                        {
                            "Image file": "slice_1.png",
                            "Layer exposure time (ms)": 1000,
                        },
                    ],
                },
            ],
        }
        zf.writestr("print_settings.json", json.dumps(settings))

        # Create a test image
        img = Image.new("L", (100, 100), 0)
        img.putpixel((50, 50), 255)  # Single white pixel

        # Save test image properly
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        zf.writestr("slices/slice_1.png", buf.getvalue())

    return zip_path


def test_new_print_file_basic(tmp_path: Path, test_component_zip: Path) -> None:
    """Test basic print file generation."""
    output_path = tmp_path / "output.zip"
    components = [
        {"x": 0, "y": 0, "group": "1.0"},
        {"x": 200, "y": 0, "group": "2.0"},
    ]

    new_print_file(test_component_zip, output_path, components)

    assert output_path.exists()

    with zipfile.ZipFile(output_path) as zf:
        # Check print settings were updated
        settings = json.loads(zf.read("print_settings.json"))
        assert len(settings["Layers"]) > 0

        # Check slices were created
        slices = [n for n in zf.namelist() if n.startswith("slices/")]
        assert len(slices) > 0


def test_new_print_file_invalid_input(tmp_path: Path) -> None:
    """Test error handling for invalid inputs."""
    output_path = tmp_path / "output.zip"
    components = [{"x": 0, "y": 0, "group": "1.0"}]

    # Test with non-existent input file
    with pytest.raises(FileNotFoundError):
        new_print_file(Path("nonexistent.zip"), output_path, components)

    # Test with invalid zip file
    invalid_zip = tmp_path / "invalid.zip"
    invalid_zip.write_text("not a zip file")
    with pytest.raises(zipfile.BadZipFile):
        new_print_file(invalid_zip, output_path, components)


def test_new_print_file_group_scaling(tmp_path: Path, test_component_zip: Path) -> None:
    """Test exposure scaling based on group names."""
    output_path = tmp_path / "output.zip"
    components = [
        {"x": 0, "y": 0, "group": "100"},  # Normal exposure (100%)
        {"x": 200, "y": 0, "group": "200"},  # Double exposure (200%)
        {"x": 400, "y": 0, "group": "50"},  # Half exposure (50%)
    ]

    new_print_file(test_component_zip, output_path, components)

    with zipfile.ZipFile(output_path) as zf:
        settings = json.loads(zf.read("print_settings.json"))

        # Get all exposures from all layers
        exposures = [
            setting["Layer exposure time (ms)"]
            for layer in settings["Layers"]
            for setting in layer["Image settings list"]
        ]

        found_exposures = set(exposures)
        base_exposure = 1000  # Original exposure from test_component_zip
        expected_exposures = {base_exposure, base_exposure * 2, base_exposure * 0.5}

        assert (
            expected_exposures == found_exposures
        ), f"Incorrect exposure scaling. Expected {expected_exposures}, found {found_exposures}"
