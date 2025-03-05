"""Test suite for component menu module."""

import tkinter as tk
from unittest.mock import ANY, MagicMock, patch

import pytest

from app.menus.component_menu import ComponentMenu


@pytest.fixture
def mock_app() -> MagicMock:
    """Create a mock app for testing."""
    mock = MagicMock()
    mock.root = MagicMock(spec=tk.Tk)
    mock.comp_width = 100
    mock.comp_height = 100
    mock.colors = {"Group1": "red", "Group2": "blue"}
    mock.groups = {"Group1": [], "Group2": []}
    mock.selection = []
    mock.group_menu.current_group.get.return_value = "Group1"
    return mock


@pytest.fixture
def component_menu(mock_app: MagicMock) -> ComponentMenu:
    """Create a ComponentMenu instance for testing."""
    with patch("tkinter.Menu"):
        mock_menubar = MagicMock()
        menu = ComponentMenu(mock_app, mock_menubar)
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


def test_create_menu(component_menu: ComponentMenu) -> None:
    """Test menu creation."""
    mock_menubar = MagicMock()
    component_menu._create_menu(mock_menubar)

    # Verify menubar interactions
    mock_menubar.add_cascade.assert_called_once()

    # Verify menu commands were added
    assert component_menu.menu.add_command.call_count >= 4
    assert component_menu.menu.add_separator.call_count >= 2


def test_bind_shortcuts(component_menu: ComponentMenu) -> None:
    """Test shortcut binding."""
    component_menu._bind_shortcuts()

    # Verify bindings were created
    component_menu.app.root.bind_all.assert_any_call("<Insert>", ANY)
    component_menu.app.root.bind_all.assert_any_call("<Delete>", ANY)


def test_check_can_create_component_success(component_menu: ComponentMenu) -> None:
    """Test component creation check when conditions are met."""
    result = component_menu._check_can_create_component()
    assert result == "Group1"


def test_check_can_create_component_no_dimensions(component_menu: ComponentMenu) -> None:
    """Test component creation check when dimensions are missing."""
    component_menu.app.comp_width = None
    component_menu.app.comp_height = None

    with patch("tkinter.messagebox.showwarning") as mock_warning:
        result = component_menu._check_can_create_component()

    assert result is None
    mock_warning.assert_called_once()


def test_check_can_create_component_no_group(component_menu: ComponentMenu) -> None:
    """Test component creation check when no group is selected."""
    component_menu.app.group_menu.current_group.get.return_value = ""

    with patch("tkinter.simpledialog.messagebox.showerror") as mock_error:
        result = component_menu._check_can_create_component()

    assert result is None
    mock_error.assert_called_once()


def test_add_component(component_menu: ComponentMenu) -> None:
    """Test adding a component."""
    # Mock _check_can_create_component to return a valid group
    component_menu._check_can_create_component = MagicMock(return_value="Group1")

    # Mock the app's methods that are called
    component_menu.app.deselect_all = MagicMock()
    component_menu.app.update_label = MagicMock()
    component_menu.app.groups = {"Group1": []}
    component_menu.app.colors = {"Group1": "red"}

    with patch("app.menus.component_menu.Component") as mock_component_class:
        mock_component = MagicMock()
        mock_component_class.return_value = mock_component

        component_menu.add_component()

        # Verify component was created with correct parameters
        mock_component_class.assert_called_once_with(component_menu.app, 50, 50, "Group1")

        # Verify component was added to the group
        assert mock_component in component_menu.app.groups["Group1"]

        # Verify component was selected and label updated
        mock_component.select.assert_called_once()
        component_menu.app.update_label.assert_called_once_with(mock_component)


def test_delete_component(component_menu: ComponentMenu) -> None:
    """Test deleting components."""
    # Setup mock components
    mock_comp1 = MagicMock()
    mock_comp1.group = "Group1"
    mock_comp2 = MagicMock()
    mock_comp2.group = "Group1"

    component_menu.app.selection = [mock_comp1, mock_comp2]
    component_menu.app.groups["Group1"] = [mock_comp1, mock_comp2]

    component_menu.delete_component()

    # Verify components were removed and deleted
    assert len(component_menu.app.groups["Group1"]) == 0
    mock_comp1.delete.assert_called_once()
    mock_comp2.delete.assert_called_once()
    assert len(component_menu.app.selection) == 0


def test_tile_success(component_menu: ComponentMenu) -> None:
    """Test tiling components successfully."""
    # Mock _check_can_create_component to return a valid group
    component_menu._check_can_create_component = MagicMock(return_value="Group1")

    # Mock the app's attributes
    component_menu.app.comp_width = 100
    component_menu.app.comp_height = 80
    component_menu.app.groups = {"Group1": []}
    component_menu.app.colors = {"Group1": "red"}
    component_menu.app.update_label = MagicMock()

    # Mock TileDialog result
    mock_dialog = MagicMock()
    mock_dialog.result = (10, 10, 5, 5, 2, 2)  # x_start, y_start, x_spacing, y_spacing, num_x, num_y
    mock_dialog.top = MagicMock()

    with patch("app.menus.component_menu.TileDialog", return_value=mock_dialog):
        with patch("app.menus.component_menu.Component") as mock_component_class:
            mock_component = MagicMock()
            mock_component_class.return_value = mock_component

            component_menu.tile()

            # Should create 2x2=4 components
            assert mock_component_class.call_count == 4

            # Verify components were added to the group
            assert len(component_menu.app.groups["Group1"]) == 4

            # Verify update_label was called with the last component
            component_menu.app.update_label.assert_called_once_with(mock_component)


def test_tile_cancelled(component_menu: ComponentMenu) -> None:
    """Test tiling when dialog is cancelled."""
    # Mock TileDialog with no result (cancelled)
    mock_dialog = MagicMock()
    mock_dialog.result = None
    mock_dialog.top = MagicMock()

    with patch("app.menus.component_menu.TileDialog", return_value=mock_dialog):
        with patch("app.menus.component_menu.Component") as mock_component_class:
            component_menu.tile()

            # Should not create any components
            mock_component_class.assert_not_called()


def test_run_cutout_tool(component_menu: ComponentMenu) -> None:
    """Test launching the component cutout tool."""
    with patch("app.menus.component_menu.ComponentSelector") as mock_selector:
        component_menu.run_cutout_tool()
        mock_selector.assert_called_once_with(parent=component_menu.app.root)
