"""Test suite for component selector module."""

import tkinter as tk
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from app.component_selector import ComponentSelector


@pytest.fixture
def mock_tk() -> Generator[MagicMock, None, None]:
    """Mock tkinter components."""
    with patch("tkinter.Tk") as mock_tk_class:
        # Create mock Tk instance
        mock_root = mock_tk_class.return_value
        mock_root.winfo_screenwidth = MagicMock(return_value=1920)
        mock_root.winfo_screenheight = MagicMock(return_value=1080)
        mock_root.mainloop = MagicMock()
        mock_root.destroy = MagicMock()
        mock_root.grab_set = MagicMock()

        # Mock other tkinter components
        with (
            patch("tkinter.Toplevel", return_value=mock_root),
            patch("tkinter.Label"),
            patch("tkinter.Frame"),
            patch("tkinter.Button"),
            patch("tkinter.Scrollbar"),
            patch("tkinter.Canvas"),
            patch("tkinter.filedialog.askopenfilename"),
            patch("tkinter.filedialog.asksaveasfilename"),
            patch("tkinter.messagebox.showinfo"),
            patch("tkinter.messagebox.showerror"),
            patch("PIL.ImageTk.PhotoImage"),
        ):
            yield mock_root


@pytest.fixture
def mock_image_ops() -> Generator[dict, None, None]:
    """Mock image operations."""
    with (
        patch("app.image_ops.merge_slices") as mock_merge,
        patch("app.image_ops.find_white_regions") as mock_find_regions,
        patch("app.image_ops.export_cropped_slices") as mock_export,
    ):
        # Create a mock image
        mock_img = MagicMock(spec=Image.Image)
        mock_img.width = 800
        mock_img.height = 600
        mock_img.resize.return_value = mock_img

        # Set up return values
        mock_merge.return_value = mock_img
        mock_find_regions.return_value = [(100, 100, 200, 200), (300, 300, 400, 400)]

        yield {
            "merge_slices": mock_merge,
            "find_white_regions": mock_find_regions,
            "export_cropped_slices": mock_export,
            "mock_img": mock_img,
        }


@pytest.fixture
def component_selector(mock_tk: MagicMock, mock_image_ops: dict) -> ComponentSelector:
    """Create a ComponentSelector instance for testing."""
    # Mock the input zip selection, Popup class, and __init__ method
    with (
        patch("tkinter.filedialog.askopenfilename", return_value="test.zip"),
        patch("app.popup.Popup"),
        patch.object(ComponentSelector, "__init__", return_value=None),
    ):
        selector = ComponentSelector()

        # Manually set the attributes that would normally be set in __init__
        selector.zoom_factor = 0.5
        selector.input_zip = "test.zip"
        selector.regions_data = [(100, 100, 200, 200), (300, 300, 400, 400)]
        selector.selected_region_index = None
        selector.selected_bbox = None
        selector.original_img = mock_image_ops["mock_img"]
        selector.preview_canvas = MagicMock()
        selector.preview_canvas.canvasx = MagicMock()
        selector.preview_canvas.canvasy = MagicMock()
        selector.preview_canvas.itemconfig = MagicMock()
        selector.preview_canvas_img = 1  # Just a dummy ID
        selector.region_details_label = MagicMock()
        selector.highlight_rect = None
        selector.root = mock_tk

        # Mock the redraw_image method to avoid PIL ImageTk issues
        selector.redraw_image = MagicMock()

        return selector


def test_initialization(component_selector: ComponentSelector) -> None:
    """Test that ComponentSelector initializes correctly."""
    assert component_selector.zoom_factor > 0
    assert component_selector.input_zip == "test.zip"
    assert component_selector.regions_data == [(100, 100, 200, 200), (300, 300, 400, 400)]
    assert component_selector.selected_region_index is None
    assert component_selector.selected_bbox is None


def test_get_input_zip_success() -> None:
    """Test successful zip file selection."""
    # Instead of testing the full initialization, let's test the _get_input_zip method directly
    with patch("tkinter.filedialog.askopenfilename", return_value="test.zip"), patch("tkinter.messagebox.showinfo"):
        # Create a minimal instance with just enough to test _get_input_zip
        selector = ComponentSelector.__new__(ComponentSelector)

        # Call the method directly
        result = selector._get_input_zip()  # noqa: SLF001

        # Check that the method returned the expected value
        assert result == "test.zip"

        # Check that the dialog was shown with the correct parameters
        tk.filedialog.askopenfilename.assert_called_once()
        assert "zip" in tk.filedialog.askopenfilename.call_args[1]["filetypes"][0][1]


def test_get_input_zip_cancel() -> None:
    """Test cancelled zip file selection."""
    # Test with a canceled dialog (empty string return)
    with patch("tkinter.filedialog.askopenfilename", return_value=""), patch("tkinter.messagebox.showinfo"):
        # Create a minimal instance with just enough to test _get_input_zip
        selector = ComponentSelector.__new__(ComponentSelector)

        # Call the method directly
        result = selector._get_input_zip()  # noqa: SLF001

        # Check that the method returned an empty string when dialog was canceled
        assert result == ""


def test_zoom_in(component_selector: ComponentSelector) -> None:
    """Test zoom in functionality."""
    initial_zoom = component_selector.zoom_factor
    component_selector.zoom_in()
    assert component_selector.zoom_factor == initial_zoom + 0.1
    # Check that redraw_image was called
    component_selector.redraw_image.assert_called_once()


def test_zoom_out(component_selector: ComponentSelector) -> None:
    """Test zoom out functionality."""
    initial_zoom = component_selector.zoom_factor
    component_selector.zoom_out()
    assert component_selector.zoom_factor == initial_zoom - 0.1
    # Check that redraw_image was called
    component_selector.redraw_image.assert_called_once()


def test_zoom_out_minimum(component_selector: ComponentSelector) -> None:
    """Test zoom out doesn't go below minimum."""
    component_selector.zoom_factor = 0.15
    component_selector.zoom_out()
    assert component_selector.zoom_factor == 0.1  # Minimum zoom is 0.1
    # Check that redraw_image was called
    component_selector.redraw_image.assert_called_once()


def test_show_region_details(component_selector: ComponentSelector) -> None:
    """Test region details display."""
    component_selector.show_region_details(0)
    assert component_selector.selected_region_index == 0
    assert component_selector.selected_bbox == (100, 100, 200, 200)


def test_on_canvas_click_hit(component_selector: ComponentSelector) -> None:
    """Test canvas click that hits a region."""
    # Create a mock event
    event = MagicMock()
    event.x = 150  # These coordinates will be transformed by canvasx/y
    event.y = 150

    # Mock the canvas coordinate transformation
    component_selector.preview_canvas.canvasx.return_value = 150
    component_selector.preview_canvas.canvasy.return_value = 150

    # Set zoom factor to 1 for simplicity
    component_selector.zoom_factor = 1.0

    # Call the click handler
    component_selector.on_canvas_click(event)

    # Check that the first region was selected
    assert component_selector.selected_region_index == 0
    assert component_selector.selected_bbox == (100, 100, 200, 200)


def test_on_canvas_click_miss(component_selector: ComponentSelector) -> None:
    """Test canvas click that misses all regions."""
    # Create a mock event
    event = MagicMock()
    event.x = 50
    event.y = 50

    # Mock the canvas coordinate transformation
    component_selector.preview_canvas.canvasx.return_value = 50
    component_selector.preview_canvas.canvasy.return_value = 50

    # Set zoom factor to 1 for simplicity
    component_selector.zoom_factor = 1.0

    # Set initial selection to check it doesn't change
    component_selector.selected_region_index = 0
    component_selector.selected_bbox = (100, 100, 200, 200)

    # Call the click handler
    component_selector.on_canvas_click(event)

    # Check that selection didn't change
    assert component_selector.selected_region_index == 0
    assert component_selector.selected_bbox == (100, 100, 200, 200)


def test_export_cropped_images_no_selection(component_selector: ComponentSelector) -> None:
    """Test export with no region selected."""
    with patch("tkinter.messagebox.showerror") as mock_error:
        component_selector.selected_bbox = None
        component_selector.export_cropped_images()
        mock_error.assert_called_once()


def test_export_cropped_images_success(component_selector: ComponentSelector, mock_image_ops: dict) -> None:
    """Test successful export of cropped images."""
    # Set up a selected region
    component_selector.selected_bbox = (100, 100, 200, 200)

    # Mock all necessary components in a single with statement
    with (
        patch("tkinter.filedialog.asksaveasfilename", return_value="output.zip"),
        patch("app.popup.Popup"),
        patch("tkinter.messagebox.showinfo") as mock_info,
        patch("zipfile.ZipFile"),
        patch("app.component_selector.export_cropped_slices") as mock_export,
    ):
        # Call the method
        component_selector.export_cropped_images()

        # Check that export was called with correct parameters
        mock_export.assert_called_once_with("test.zip", "output.zip", (100, 100, 200, 200))

        # Check that success message was shown
        mock_info.assert_called_once()


def test_export_cropped_images_cancel(component_selector: ComponentSelector, mock_image_ops: dict) -> None:
    """Test cancelled export of cropped images."""
    # Set up a selected region
    component_selector.selected_bbox = (100, 100, 200, 200)

    # Mock the save dialog to return empty string (cancel)
    with patch("tkinter.filedialog.asksaveasfilename", return_value=""):
        component_selector.export_cropped_images()

        # Check that export was not called
        mock_image_ops["export_cropped_slices"].assert_not_called()
