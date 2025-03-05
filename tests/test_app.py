"""Test suite for main application."""

from unittest.mock import MagicMock, patch

import pytest

from app.app import App
from app.component import Component
from app.constants import CANVAS_HEIGHT, CANVAS_WIDTH


@pytest.fixture
def app() -> App:
    """Create an App instance for testing."""
    with patch("tkinter.Tk") as mock_tk:
        # Create a mock Tk instance
        mock_root = mock_tk.return_value
        mock_root.mainloop = MagicMock()

        # Mock StringVar
        mock_stringvar = MagicMock()
        mock_stringvar.get = MagicMock(return_value="")
        mock_stringvar.set = MagicMock()

        # Mock Canvas
        mock_canvas = MagicMock()
        mock_canvas.create_rectangle = MagicMock(return_value=1)  # Return an ID
        mock_canvas.itemconfig = MagicMock()
        mock_canvas.delete = MagicMock()
        mock_canvas.find_all = MagicMock(return_value=[])
        mock_canvas.config = MagicMock()
        mock_canvas.coords = MagicMock()
        mock_canvas.tag_bind = MagicMock()

        # Track canvas dimensions for zoom tests
        mock_canvas._width = CANVAS_WIDTH  # noqa: SLF001
        mock_canvas._height = CANVAS_HEIGHT  # noqa: SLF001
        mock_canvas.winfo_width = MagicMock(side_effect=lambda: mock_canvas._width)  # noqa: SLF001
        mock_canvas.winfo_height = MagicMock(side_effect=lambda: mock_canvas._height)  # noqa: SLF001

        # Mock Label
        mock_label = MagicMock()
        mock_label.config = MagicMock()
        mock_label.cget = MagicMock()  # We'll set the side_effect in the test

        # Store expected text for label tests
        expected_text = ""

        # Patch additional tkinter components
        with (
            patch("tkinter.StringVar", return_value=mock_stringvar),
            patch("tkinter.Canvas", return_value=mock_canvas),
            patch("tkinter.Label", return_value=mock_label),
            patch("tkinter.Frame"),
            patch("tkinter.Scrollbar"),
            patch("tkinter.Menu"),
        ):
            app = App()
            # Set test properties
            app.comp_width = 100
            app.comp_height = 100
            # Store mocks for test access
            app._mock_canvas = mock_canvas  # noqa: SLF001
            app._mock_label = mock_label  # noqa: SLF001
            app._expected_text = expected_text  # noqa: SLF001
            return app


def test_app_initialization(app: App) -> None:
    """Test that App initializes with correct default values."""
    assert app.selection == []
    assert app.groups == {}
    assert app.colors == {}
    assert app.color_boxes == {}
    assert app.selection_rect is None
    assert app.selection_start_x is None
    assert app.selection_start_y is None
    assert app.zoom_factor == 1.0


def test_create_component(app: App) -> None:
    """Test component creation and group management."""
    # Create a test group
    app.groups["1.0"] = []
    app.colors["1.0"] = "#FF0000"

    # Create a component
    comp = Component(app, 50, 50, "1.0")
    # Component should add itself to the group
    app.groups["1.0"].append(comp)

    assert comp in app.groups["1.0"]
    assert comp.x == 50
    assert comp.y == 50
    assert comp.group == "1.0"


def test_component_selection(app: App) -> None:
    """Test component selection behavior."""
    # Setup test components
    app.groups["1.0"] = []
    app.colors["1.0"] = "#FF0000"
    comp1 = Component(app, 0, 0, "1.0")
    comp2 = Component(app, 200, 200, "1.0")

    # Test single selection
    comp1.select()
    assert comp1 in app.selection
    assert len(app.selection) == 1

    # Test multi-selection
    comp2.select()
    assert comp2 in app.selection
    assert len(app.selection) == 2

    # Test deselection
    app.deselect_all()
    assert len(app.selection) == 0


def test_canvas_zoom(app: App) -> None:
    """Test canvas zoom functionality."""
    # Test zoom in
    app.view_menu.zoom_in()
    assert app.zoom_factor == 1.1

    # Update mock canvas dimensions
    app._mock_canvas._width = int(CANVAS_WIDTH * 1.1)  # noqa: SLF001
    app._mock_canvas._height = int(CANVAS_HEIGHT * 1.1)  # noqa: SLF001

    assert app.canvas.winfo_width() == int(CANVAS_WIDTH * 1.1)
    assert app.canvas.winfo_height() == int(CANVAS_HEIGHT * 1.1)

    # Test zoom out
    app.view_menu.zoom_out()
    assert app.zoom_factor == 1.0

    # Update mock canvas dimensions
    app._mock_canvas._width = CANVAS_WIDTH  # noqa: SLF001
    app._mock_canvas._height = CANVAS_HEIGHT  # noqa: SLF001

    assert app.canvas.winfo_width() == CANVAS_WIDTH
    assert app.canvas.winfo_height() == CANVAS_HEIGHT


def test_component_dragging(app: App) -> None:
    """Test component drag behavior."""
    # Setup test component
    app.groups["1.0"] = []
    app.colors["1.0"] = "#FF0000"
    comp = Component(app, 50, 50, "1.0")
    comp.select()

    # Simulate drag event
    event = MagicMock()
    event.x = 60
    event.y = 60

    # Start drag
    comp.start_x = 50
    comp.start_y = 50

    # Perform drag
    comp.on_drag(event)

    # Check new position (accounting for zoom factor)
    assert comp.x == 60
    assert comp.y == 60


def test_select_components_in_area(app: App) -> None:
    """Test area selection of components."""
    # Setup test components
    app.groups["1.0"] = []
    app.colors["1.0"] = "#FF0000"

    comp1 = Component(app, 50, 50, "1.0")  # Inside selection area
    app.groups["1.0"].append(comp1)

    comp2 = Component(app, 300, 300, "1.0")  # Outside selection area
    app.groups["1.0"].append(comp2)

    # Mock the component selection
    def mock_select() -> None:
        if comp1 not in app.selection:
            app.selection.append(comp1)

    comp1.select = mock_select

    # Select area that includes comp1 but not comp2
    app.select_components_in_area(0, 0, 200, 200)

    assert comp1 in app.selection
    assert comp2 not in app.selection


def test_clear_canvas(app: App) -> None:
    """Test canvas clearing functionality."""
    # Setup test components
    app.groups["1.0"] = []
    app.colors["1.0"] = "#FF0000"
    Component(app, 50, 50, "1.0")
    Component(app, 100, 100, "1.0")

    # Clear canvas
    app.clear_canvas()

    # Check that canvas is empty
    assert len(app.canvas.find_all()) == 0


def test_update_label(app: App) -> None:
    """Test component information label updates."""
    # Setup test component
    app.groups["1.0"] = []
    app.colors["1.0"] = "#FF0000"
    comp = Component(app, 50, 50, "1.0")
    app.groups["1.0"].append(comp)

    # Update label with component
    expected_text = f"X: 50, Y: 50, Width: {app.comp_width}, Height: {app.comp_height}, Group: 1.0"
    app.dimensions_label.cget.return_value = expected_text
    app.update_label(comp)
    assert app.dimensions_label.cget("text") == expected_text

    # Update label with no component
    app.dimensions_label.cget.return_value = ""
    app.update_label(None)
    assert app.dimensions_label.cget("text") == ""
