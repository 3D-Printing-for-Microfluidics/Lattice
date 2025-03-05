"""Test suite for file menu module."""

import json
import tkinter as tk
from pathlib import Path
from unittest.mock import ANY, MagicMock, mock_open, patch

import pytest

from app.menus.file_menu import FileMenu


@pytest.fixture
def mock_app() -> MagicMock:
    """Create a mock app for testing."""
    mock = MagicMock()
    mock.root = MagicMock(spec=tk.Tk)
    mock.canvas = MagicMock(spec=tk.Canvas)
    mock.comp_width = 100
    mock.comp_height = 100
    mock.colors = {"Group1": "red", "Group2": "blue"}
    mock.groups = {"Group1": [], "Group2": []}
    mock.selection = []
    return mock


@pytest.fixture
def file_menu(mock_app: MagicMock) -> FileMenu:
    """Create a FileMenu instance for testing."""
    with patch("tkinter.Menu"):
        mock_menubar = MagicMock()
        menu = FileMenu(mock_app, mock_menubar)
        return menu


@pytest.fixture(autouse=True)
def mock_tkinter_dialogs():
    """Mock all tkinter dialogs to prevent them from appearing during tests."""
    with (
        patch("tkinter.messagebox.showinfo"),
        patch("tkinter.messagebox.showerror"),
        patch("tkinter.messagebox.showwarning"),
        patch("tkinter.messagebox.askyesno"),
        patch("tkinter.filedialog.askopenfilename"),
        patch("tkinter.filedialog.asksaveasfilename"),
        patch("tkinter.simpledialog.askstring"),
        patch("tkinter.colorchooser.askcolor"),
        patch("tkinter.Toplevel"),
    ):
        yield


def test_create_menu(file_menu: FileMenu) -> None:
    """Test menu creation."""
    mock_menubar = MagicMock()
    file_menu._create_menu(mock_menubar)

    # Verify menubar interactions
    mock_menubar.add_cascade.assert_called_once()

    # Verify menu commands were added
    assert file_menu.menu.add_command.call_count >= 2


def test_bind_shortcuts(file_menu: FileMenu) -> None:
    """Test shortcut binding."""
    file_menu._bind_shortcuts()

    # Verify bindings were created
    file_menu.app.root.bind_all.assert_any_call("<Control-l>", ANY)
    file_menu.app.root.bind_all.assert_any_call("<Control-o>", ANY)


def test_load_component_success(file_menu: FileMenu) -> None:
    """Test loading a component successfully."""
    # Mock file dialog to return a file path
    mock_file_path = "test_component.zip"

    # Reset the mock app's attributes to ensure they're updated correctly
    file_menu.app.comp_width = None
    file_menu.app.comp_height = None
    file_menu.app.component_file = None

    with (
        patch("tkinter.filedialog.askopenfilename", return_value=mock_file_path),
        patch("app.menus.file_menu.get_component_dimensions", return_value=(200, 150)),
        patch("tkinter.messagebox.showinfo"),
    ):
        file_menu.load_component()

        # Verify component dimensions were set
        assert file_menu.app.comp_width == 200
        assert file_menu.app.comp_height == 150
        assert file_menu.app.component_file == mock_file_path


def test_load_component_cancelled(file_menu: FileMenu) -> None:
    """Test cancelling component loading."""
    # Mock file dialog to return empty string (cancelled)
    with patch("tkinter.filedialog.askopenfilename", return_value=""):
        file_menu.load_component()

        # Verify component dimensions were not changed
        assert file_menu.app.comp_width == 100
        assert file_menu.app.comp_height == 100


def test_get_layout_data(file_menu: FileMenu) -> None:
    """Test getting layout data."""
    # Setup mock components
    mock_comp1 = MagicMock()
    mock_comp1.group = "Group1"
    mock_comp1.x = 10
    mock_comp1.y = 20

    mock_comp2 = MagicMock()
    mock_comp2.group = "Group2"
    mock_comp2.x = 30
    mock_comp2.y = 40

    file_menu.app.groups = {"Group1": [mock_comp1], "Group2": [mock_comp2]}
    file_menu.app.colors = {"Group1": "red", "Group2": "blue"}

    layout_data = file_menu.get_layout_data()

    # Verify layout data structure
    assert "colors" in layout_data
    assert "components" in layout_data
    assert len(layout_data["components"]) == 2
    assert layout_data["colors"] == {"Group1": "red", "Group2": "blue"}

    # Check that components are correctly included
    component_data = layout_data["components"]
    assert {"group": "Group1", "x": 10, "y": 20} in component_data
    assert {"group": "Group2", "x": 30, "y": 40} in component_data


def test_save_json_success(file_menu: FileMenu) -> None:
    """Test saving layout to JSON successfully."""
    # Setup mock data
    mock_data = {
        "colors": {"Group1": "red"},
        "components": [{"group": "Group1", "x": 10, "y": 20}],
    }

    # Mock get_layout_data to return our test data
    file_menu.get_layout_data = MagicMock(return_value=mock_data)

    with (
        patch("tkinter.filedialog.asksaveasfilename", return_value="test_layout.json"),
        patch("pathlib.Path.open", mock_open()) as mock_file,
    ):
        file_menu.save_json()

        # Verify file was opened and written to
        mock_file.assert_called_once_with("w")


def test_save_json_cancelled(file_menu: FileMenu) -> None:
    """Test cancelling JSON save."""
    with patch("tkinter.filedialog.asksaveasfilename", return_value=""):
        with patch("builtins.open", mock_open()) as mock_file:
            file_menu.save_json()

            # Verify file was not opened
            mock_file.assert_not_called()


def test_load_json_success(file_menu: FileMenu) -> None:
    """Test loading layout from JSON successfully."""
    # Setup mock JSON data
    mock_json_data = {
        "colors": {"Group1": "red", "Group2": "blue"},
        "components": [
            {"group": "Group1", "x": 10, "y": 20},
            {"group": "Group2", "x": 30, "y": 40},
            {"group": "Group2", "x": 50, "y": 60},
        ],
    }

    # Set required attributes on app
    file_menu.app.comp_width = 200
    file_menu.app.comp_height = 150

    # Mock file operations
    with (
        patch("tkinter.filedialog.askopenfilename", return_value="test_layout.json"),
        patch("pathlib.Path.open", mock_open(read_data=json.dumps(mock_json_data))),
        patch("app.menus.file_menu.Component") as mock_component_class,
        patch.object(file_menu.app, "clear_canvas"),
    ):
        mock_component = MagicMock()
        mock_component_class.return_value = mock_component

        file_menu.load_json()

        # Verify colors were set
        assert file_menu.app.colors == {"Group1": "red", "Group2": "blue"}

        # Verify components were created (3 total)
        assert mock_component_class.call_count == 3

        # Verify clear_canvas was called
        file_menu.app.clear_canvas.assert_called_once()


def test_load_json_cancelled(file_menu: FileMenu) -> None:
    """Test cancelling JSON load."""
    with patch("tkinter.filedialog.askopenfilename", return_value=""):
        file_menu.load_json()

        # Verify canvas was not cleared
        file_menu.app.clear_canvas.assert_not_called()


def test_load_json_missing_component_file(file_menu: FileMenu) -> None:
    """Test loading JSON with missing component file."""
    # Setup mock JSON data
    mock_json_data = {
        "colors": {"Group1": "red"},
        "components": [{"group": "Group1", "x": 10, "y": 20}],
    }

    # Mock file operations to raise FileNotFoundError
    with (
        patch("tkinter.filedialog.askopenfilename", return_value="test_layout.json"),
        patch("pathlib.Path.open", side_effect=FileNotFoundError("File not found")),
        patch("tkinter.messagebox.showerror") as mock_error,
    ):
        file_menu.app.comp_width = 100  # Set required attribute
        file_menu.app.comp_height = 100  # Set required attribute

        file_menu.load_json()

        # Verify error was shown
        mock_error.assert_called_once_with("Error", "File not found")


def test_check_component_overlap(file_menu: FileMenu) -> None:
    """Test checking for component overlap."""
    # Setup mock components with overlapping positions
    mock_comp1 = MagicMock()
    mock_comp1.x = 10
    mock_comp1.y = 10

    mock_comp2 = MagicMock()
    mock_comp2.x = 50  # Overlaps with comp1 (assuming comp_width=100)
    mock_comp2.y = 50  # Overlaps with comp1 (assuming comp_height=100)

    mock_comp3 = MagicMock()
    mock_comp3.x = 200  # No overlap
    mock_comp3.y = 200  # No overlap

    # Add components to groups
    file_menu.app.groups = {"Group1": [mock_comp1, mock_comp3], "Group2": [mock_comp2]}

    # Get overlapping components
    overlaps = file_menu.check_component_overlap()

    # Verify overlapping components were detected
    assert len(overlaps) == 2
    assert mock_comp1 in overlaps
    assert mock_comp2 in overlaps
    assert mock_comp3 not in overlaps


def test_generate_print_file_success(file_menu: FileMenu) -> None:
    """Test generating print file successfully."""
    # Setup mock data
    file_menu.app.component_file = "test.zip"
    file_menu.app.groups = {"Group1": [MagicMock()]}

    with (
        patch("tkinter.filedialog.asksaveasfilename", return_value="output.json"),
        patch("app.menus.file_menu.new_print_file") as mock_new_print_file,
        patch("app.menus.file_menu.Popup") as mock_popup,
    ):
        file_menu.generate_print_file()

        # Verify print file generation was called
        mock_new_print_file.assert_called_once()
        mock_popup.assert_called()
        mock_popup().destroy.assert_called_once()


def test_generate_print_file_cancelled(file_menu: FileMenu) -> None:
    """Test cancelling print file generation."""
    file_menu.app.component_file = "test.zip"

    with patch("tkinter.filedialog.asksaveasfilename", return_value=""):
        file_menu.generate_print_file()

        # No further actions should be taken
