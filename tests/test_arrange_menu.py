"""Test suite for arrange menu module."""

import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from app.menus.arrange_menu import ArrangeMenu
from app.menus.menu import Menu


@pytest.fixture
def mock_app():
    """Create a mock app for testing."""
    mock_app = MagicMock()
    mock_app.root = MagicMock(spec=tk.Tk)
    mock_app.root.bind_all = MagicMock()
    mock_app.selection = []
    mock_app.comp_width = 100
    mock_app.comp_height = 100
    mock_app.update_label = MagicMock()

    # Create a mock menubar
    mock_app.menubar = MagicMock(spec=tk.Menu)

    return mock_app


@pytest.fixture
def arrange_menu(mock_app: MagicMock):
    """Create an ArrangeMenu instance for testing."""
    # Patch the Menu.__init__ method to avoid creating a real tk.Menu
    with patch.object(Menu, "__init__", return_value=None):
        menu = ArrangeMenu(mock_app)

        # Manually set the attributes that would normally be set in __init__
        menu.app = mock_app
        menu.menu = MagicMock(spec=tk.Menu)
        menu.menu.add_command = MagicMock()
        menu.menu.add_separator = MagicMock()

        return menu


def test_create_menu(arrange_menu: ArrangeMenu) -> None:
    """Test menu creation."""
    mock_menubar = MagicMock(spec=tk.Menu)
    mock_menubar.add_cascade = MagicMock()

    arrange_menu._create_menu(mock_menubar)  # noqa: SLF001

    # Check that cascade was added
    mock_menubar.add_cascade.assert_called_once_with(label="Arrange", menu=arrange_menu.menu)

    # Check that menu items were added
    assert arrange_menu.menu.add_command.call_count == 6
    assert arrange_menu.menu.add_separator.call_count == 1


def test_bind_shortcuts(arrange_menu: ArrangeMenu, mock_app: MagicMock) -> None:
    """Test shortcut binding."""
    arrange_menu._bind_shortcuts()  # noqa: SLF001

    # Check that all shortcuts were bound
    assert mock_app.root.bind_all.call_count == 6

    # Check specific bindings by checking the sequence (first argument)
    # We can't directly compare lambda functions, so we check the call arguments
    call_args_list = [call[0][0] for call in mock_app.root.bind_all.call_args_list]
    assert "<Control-x>" in call_args_list
    assert "<Control-y>" in call_args_list
    assert "<Control-Left>" in call_args_list
    assert "<Control-Right>" in call_args_list
    assert "<Control-Up>" in call_args_list
    assert "<Control-Down>" in call_args_list


def test_align_left_no_selection(arrange_menu: ArrangeMenu, mock_app: MagicMock) -> None:
    """Test align left with no selection."""
    mock_app.selection = []
    arrange_menu.align_left()

    # Check that no updates were made
    mock_app.update_label.assert_not_called()


def test_align_left_with_selection(arrange_menu: ArrangeMenu, mock_app: MagicMock) -> None:
    """Test align left with selection."""
    # Create mock components
    comp1 = MagicMock()
    comp1.x = 100
    comp1.y = 50
    comp1.set_position = MagicMock()

    comp2 = MagicMock()
    comp2.x = 200
    comp2.y = 150
    comp2.set_position = MagicMock()

    mock_app.selection = [comp1, comp2]

    # Call align left
    arrange_menu.align_left()

    # Check that components were aligned to the leftmost position
    comp1.set_position.assert_called_once_with(100, 50)
    comp2.set_position.assert_called_once_with(100, 150)

    # Check that label was updated
    mock_app.update_label.assert_called_once_with(comp1)


def test_align_right_with_selection(arrange_menu: ArrangeMenu, mock_app: MagicMock) -> None:
    """Test align right with selection."""
    # Create mock components
    comp1 = MagicMock()
    comp1.x = 100
    comp1.y = 50
    comp1.set_position = MagicMock()

    comp2 = MagicMock()
    comp2.x = 200
    comp2.y = 150
    comp2.set_position = MagicMock()

    mock_app.selection = [comp1, comp2]

    # Call align right
    arrange_menu.align_right()

    # Check that components were aligned to the rightmost position
    # Max right edge is 200 + 100 = 300, so positions should be 200 for both
    comp1.set_position.assert_called_once_with(200, 50)
    comp2.set_position.assert_called_once_with(200, 150)

    # Check that label was updated
    mock_app.update_label.assert_called_once_with(comp1)


def test_align_top_with_selection(arrange_menu: ArrangeMenu, mock_app: MagicMock) -> None:
    """Test align top with selection."""
    # Create mock components
    comp1 = MagicMock()
    comp1.x = 100
    comp1.y = 50
    comp1.set_position = MagicMock()

    comp2 = MagicMock()
    comp2.x = 200
    comp2.y = 150
    comp2.set_position = MagicMock()

    mock_app.selection = [comp1, comp2]

    # Call align top
    arrange_menu.align_top()

    # Check that components were aligned to the topmost position
    comp1.set_position.assert_called_once_with(100, 50)
    comp2.set_position.assert_called_once_with(200, 50)

    # Check that label was updated
    mock_app.update_label.assert_called_once_with(comp1)


def test_align_bottom_with_selection(arrange_menu: ArrangeMenu, mock_app: MagicMock) -> None:
    """Test align bottom with selection."""
    # Create mock components
    comp1 = MagicMock()
    comp1.x = 100
    comp1.y = 50
    comp1.set_position = MagicMock()

    comp2 = MagicMock()
    comp2.x = 200
    comp2.y = 150
    comp2.set_position = MagicMock()

    mock_app.selection = [comp1, comp2]

    # Call align bottom
    arrange_menu.align_bottom()

    # Check that components were aligned to the bottommost position
    # Max bottom edge is 150 + 100 = 250, so positions should be 150 for comp1 and 150 for comp2
    comp1.set_position.assert_called_once_with(100, 150)
    comp2.set_position.assert_called_once_with(200, 150)

    # Check that label was updated
    mock_app.update_label.assert_called_once_with(comp1)


def test_set_x_no_selection(arrange_menu: ArrangeMenu, mock_app: MagicMock) -> None:
    """Test set x with no selection."""
    mock_app.selection = []
    arrange_menu.set_x()

    # Check that no dialog was shown
    # No need to assert anything as the function should just return


@patch("tkinter.simpledialog.askinteger", return_value=300)
def test_set_x_with_selection(mock_askinteger: MagicMock, arrange_menu: ArrangeMenu, mock_app: MagicMock) -> None:
    """Test set x with selection."""
    # Create mock components
    comp1 = MagicMock()
    comp1.x = 100
    comp1.y = 50
    comp1.set_position = MagicMock()

    comp2 = MagicMock()
    comp2.x = 200
    comp2.y = 150
    comp2.set_position = MagicMock()

    mock_app.selection = [comp1, comp2]

    # Call set x
    arrange_menu.set_x()

    # Check that dialog was shown
    mock_askinteger.assert_called_once_with("Set X", "Enter the X position:")

    # Check that components were positioned at the new X
    comp1.set_position.assert_called_once_with(300, 50)
    comp2.set_position.assert_called_once_with(300, 150)

    # Check that label was updated
    mock_app.update_label.assert_called_once_with(comp1)


@patch("tkinter.simpledialog.askinteger", return_value=None)
def test_set_x_dialog_cancelled(mock_askinteger: MagicMock, arrange_menu: ArrangeMenu, mock_app: MagicMock) -> None:
    """Test set x dialog cancelled."""
    # Create mock components
    comp1 = MagicMock()
    comp1.set_position = MagicMock()

    mock_app.selection = [comp1]

    # Call set x
    arrange_menu.set_x()

    # Check that dialog was shown
    mock_askinteger.assert_called_once()

    # Check that no positions were changed
    comp1.set_position.assert_not_called()

    # Check that label was not updated
    mock_app.update_label.assert_not_called()


@patch("tkinter.simpledialog.askinteger", return_value=200)
def test_set_y_with_selection(mock_askinteger: MagicMock, arrange_menu: ArrangeMenu, mock_app: MagicMock) -> None:
    """Test set y with selection."""
    # Create mock components
    comp1 = MagicMock()
    comp1.x = 100
    comp1.y = 50
    comp1.set_position = MagicMock()

    comp2 = MagicMock()
    comp2.x = 200
    comp2.y = 150
    comp2.set_position = MagicMock()

    mock_app.selection = [comp1, comp2]

    # Call set y
    arrange_menu.set_y()

    # Check that dialog was shown
    mock_askinteger.assert_called_once_with("Set Y", "Enter the Y position:")

    # Check that components were positioned at the new Y
    comp1.set_position.assert_called_once_with(100, 200)
    comp2.set_position.assert_called_once_with(200, 200)

    # Check that label was updated
    mock_app.update_label.assert_called_once_with(comp1)
