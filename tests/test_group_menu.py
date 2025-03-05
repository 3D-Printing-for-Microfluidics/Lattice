"""Test suite for group menu module."""

import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from app.menus.group_menu import GroupMenu


@pytest.fixture
def mock_app() -> MagicMock:
    """Create a mock app for testing."""
    mock = MagicMock()
    mock.root = MagicMock(spec=tk.Tk)
    mock.canvas = MagicMock(spec=tk.Canvas)
    mock.colors = {"Group1": "red", "Group2": "blue"}
    mock.groups = {"Group1": [], "Group2": []}
    mock.selection = []
    return mock


@pytest.fixture
def group_menu(mock_app: MagicMock) -> GroupMenu:
    """Create a GroupMenu instance for testing."""
    with patch("tkinter.Menu"):
        with patch("tkinter.StringVar") as mock_string_var:
            mock_string_var_instance = MagicMock()
            mock_string_var_instance.get.return_value = ""
            mock_string_var.return_value = mock_string_var_instance
            mock_menubar = MagicMock()

            # Patch the build_menu method to avoid the error during initialization
            with patch.object(GroupMenu, "build_menu"):
                menu = GroupMenu(mock_app, mock_menubar)
                # Now we can safely set the current_group attribute
                menu.current_group = mock_string_var_instance

                # Replace the build_menu method with a MagicMock to allow assert_not_called
                menu.build_menu = MagicMock()

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
        patch("tkinter.PhotoImage", return_value=MagicMock()),
    ):
        # Create a root window for tests to avoid "Too early to create image" errors
        root = tk.Tk()
        yield
        root.destroy()


def test_create_menu(group_menu: GroupMenu) -> None:
    """Test menu creation."""
    mock_menubar = MagicMock()
    group_menu._create_menu(mock_menubar)

    # Verify menubar interactions
    mock_menubar.add_cascade.assert_called_once()


def test_bind_shortcuts(group_menu: GroupMenu) -> None:
    """Test shortcut binding."""
    # Reset the call count before testing
    group_menu.app.root.bind_all.reset_mock()

    group_menu._bind_shortcuts()

    # GroupMenu binds Ctrl+G and Ctrl+C shortcuts
    assert group_menu.app.root.bind_all.call_count == 2

    # Check that the correct keyboard shortcuts were bound
    # We can't directly compare lambda functions, so we check the call arguments
    call_args_list = group_menu.app.root.bind_all.call_args_list
    shortcuts = [call[0][0] for call in call_args_list]
    assert "<Control-g>" in shortcuts
    assert "<Control-c>" in shortcuts


def test_validate_group_name_valid(group_menu: GroupMenu) -> None:
    """Test validating a valid group name."""
    # Valid new name (must be a positive float according to the implementation)
    assert group_menu._validate_group_name("1.5") is True


def test_validate_group_name_empty(group_menu: GroupMenu) -> None:
    """Test validating an empty group name."""
    with patch("tkinter.messagebox.showerror") as mock_error:
        result = group_menu._validate_group_name("")

    assert result is False
    mock_error.assert_called_once()


def test_validate_group_name_existing(group_menu: GroupMenu) -> None:
    """Test validating an existing group name."""
    with patch("tkinter.messagebox.showerror") as mock_error:
        result = group_menu._validate_group_name("Group1")

    assert result is False
    mock_error.assert_called_once()


def test_check_group_selected_with_selection(group_menu: GroupMenu) -> None:
    """Test checking if a group is selected when one is."""
    group_menu.current_group.get.return_value = "Group1"

    result = group_menu._check_group_selected()

    assert result == "Group1"


def test_check_group_selected_without_selection(group_menu: GroupMenu) -> None:
    """Test checking if a group is selected when none is."""
    group_menu.current_group.get.return_value = ""

    with patch("tkinter.messagebox.showerror") as mock_error:
        result = group_menu._check_group_selected()

    assert result is None
    mock_error.assert_called_once()


def test_prompt_group_name_success() -> None:
    """Test prompting for a group name successfully."""
    with patch("tkinter.simpledialog.askstring", return_value="NewGroup"):
        result = GroupMenu._prompt_group_name("Test Title")

    assert result == "NewGroup"


def test_prompt_group_name_cancelled() -> None:
    """Test cancelling the group name prompt."""
    with patch("tkinter.simpledialog.askstring", return_value=None):
        result = GroupMenu._prompt_group_name("Test Title")

    assert result is None


def test_build_menu(group_menu: GroupMenu) -> None:
    """Test building the group menu."""
    # Setup existing groups
    group_menu.app.groups = {"Group1": [], "Group2": []}
    group_menu.app.colors = {"Group1": "red", "Group2": "blue"}

    # We need to create a new mock for the menu since it's replaced in the fixture
    menu_mock = MagicMock()
    group_menu.menu = menu_mock

    with patch.object(GroupMenu, "create_color_box", return_value=MagicMock()):
        # Call the actual build_menu method (not the mocked one)
        GroupMenu.build_menu(group_menu)

        # Verify menu was cleared and rebuilt
        menu_mock.delete.assert_called_once_with(0, "end")

        # Verify standard menu items were added
        assert menu_mock.add_command.call_count >= 3

        # Verify separator was added
        assert menu_mock.add_separator.call_count >= 1

        # Verify group entries were added (one for each group)
        assert menu_mock.add_radiobutton.call_count >= 2


def test_new_group_success(group_menu: GroupMenu) -> None:
    """Test creating a new group successfully."""
    with (
        patch.object(GroupMenu, "_prompt_group_name", return_value="3.5"),
        patch.object(GroupMenu, "_validate_group_name", return_value=True),
        patch("tkinter.colorchooser.askcolor", return_value=((255, 0, 0), "#ff0000")),
    ):
        # Mock the set_group_color method to add the color to app.colors
        def mock_set_color():
            group_menu.app.colors["3.5"] = "#ff0000"

        group_menu.set_group_color = MagicMock(side_effect=mock_set_color)

        group_menu.new_group()

        # Verify new group was added
        assert "3.5" in group_menu.app.groups
        assert group_menu.app.colors["3.5"] == "#ff0000"

        # Verify menu was rebuilt
        group_menu.build_menu.assert_called_once()


def test_new_group_invalid_name(group_menu: GroupMenu) -> None:
    """Test creating a group with an invalid name."""
    with (
        patch.object(GroupMenu, "_prompt_group_name", return_value="Group1"),
        patch.object(GroupMenu, "_validate_group_name", return_value=False),
    ):
        group_menu.new_group()

        # Verify no changes were made
        assert "Group1" in group_menu.app.groups  # Already existed
        assert len(group_menu.app.groups) == 2  # No new groups added
        group_menu.build_menu.assert_not_called()


def test_new_group_cancelled_color(group_menu: GroupMenu) -> None:
    """Test cancelling color selection when creating a new group."""
    with (
        patch.object(GroupMenu, "_prompt_group_name", return_value="3.5"),
        patch.object(GroupMenu, "_validate_group_name", return_value=True),
        patch("tkinter.colorchooser.askcolor", return_value=(None, None)),
        patch("tkinter.simpledialog.messagebox.showerror"),
    ):
        # Reset the build_menu mock
        group_menu.build_menu.reset_mock()

        group_menu.new_group()

        # Verify no group was added
        assert "3.5" not in group_menu.app.groups
        group_menu.build_menu.assert_not_called()


def test_delete_group_success(group_menu: GroupMenu) -> None:
    """Test deleting a group successfully."""
    # Setup mock components
    mock_comp = MagicMock()
    group_menu.app.groups = {"Group1": [mock_comp], "Group2": []}
    group_menu.current_group.get.return_value = "Group1"

    with (
        patch("tkinter.messagebox.askyesno", return_value=True),
        patch.object(GroupMenu, "build_menu"),
        patch.object(GroupMenu, "_check_group_selected", return_value="Group1"),
    ):
        group_menu.delete_group()

        # Verify group was deleted
        assert "Group1" not in group_menu.app.groups

        # Verify components were deleted
        mock_comp.delete.assert_called_once()

        # Verify menu was rebuilt
        assert group_menu.build_menu.called


def test_delete_group_cancelled(group_menu: GroupMenu) -> None:
    """Test cancelling group deletion."""
    group_menu.app.groups = {"Group1": [], "Group2": []}
    group_menu.current_group.get.return_value = "Group1"

    with (
        patch("tkinter.messagebox.askyesno", return_value=False),
        patch.object(GroupMenu, "_check_group_selected", return_value="Group1"),
    ):
        # Reset the build_menu mock
        group_menu.build_menu.reset_mock()

        group_menu.delete_group()

        # Verify group was not deleted
        assert "Group1" in group_menu.app.groups
        group_menu.build_menu.assert_not_called()


def test_rename_group_success(group_menu: GroupMenu) -> None:
    """Test renaming a group successfully."""
    # Setup mock components
    mock_comp = MagicMock()
    mock_comp.group = "Group1"
    group_menu.app.groups = {"Group1": [mock_comp], "Group2": []}
    group_menu.app.colors = {"Group1": "red", "Group2": "blue"}

    # Setup mock selection
    mock_selection = MagicMock()
    group_menu.app.selection = [mock_selection]

    with (
        patch.object(GroupMenu, "_check_group_selected", return_value="Group1"),
        patch.object(GroupMenu, "_prompt_group_name", return_value="3.5"),
        patch.object(GroupMenu, "_validate_group_name", return_value=True),
    ):
        group_menu.rename_group()

        # Verify group was renamed
        assert "Group1" not in group_menu.app.groups
        assert "3.5" in group_menu.app.groups
        assert mock_comp in group_menu.app.groups["3.5"]
        assert mock_comp.group == "3.5"

        # Verify color was transferred
        assert "Group1" not in group_menu.app.colors
        assert "3.5" in group_menu.app.colors
        assert group_menu.app.colors["3.5"] == "red"

        # Verify menu was rebuilt
        group_menu.build_menu.assert_called_once()

        # Verify current group was set
        group_menu.current_group.set.assert_called_with("3.5")

        # Verify label was updated
        group_menu.app.update_label.assert_called_once_with(group_menu.app.selection[0])


def test_rename_group_invalid_name(group_menu: GroupMenu) -> None:
    """Test renaming a group with an invalid name."""
    group_menu.app.groups = {"Group1": [], "Group2": []}

    with (
        patch.object(GroupMenu, "_check_group_selected", return_value="Group1"),
        patch.object(GroupMenu, "_prompt_group_name", return_value="Group2"),
        patch.object(GroupMenu, "_validate_group_name", return_value=False),
    ):
        # Reset the build_menu mock
        group_menu.build_menu.reset_mock()

        group_menu.rename_group()

        # Verify no changes were made
        assert "Group1" in group_menu.app.groups
        assert "Group2" in group_menu.app.groups
        assert len(group_menu.app.groups) == 2
        group_menu.build_menu.assert_not_called()


def test_set_group_color(group_menu: GroupMenu) -> None:
    """Test setting a group color."""
    group_menu.app.groups = {"Group1": [], "Group2": []}
    group_menu.app.colors = {"Group1": "red", "Group2": "blue"}

    with (
        patch.object(GroupMenu, "_check_group_selected", return_value="Group1"),
        patch("tkinter.colorchooser.askcolor", return_value=((0, 255, 0), "#00ff00")),
        patch.object(GroupMenu, "build_menu"),
    ):
        group_menu.set_group_color()

        # Verify color was updated
        assert group_menu.app.colors["Group1"] == "#00ff00"

        # Verify menu was rebuilt
        assert group_menu.build_menu.called


def test_set_group_color_cancelled(group_menu: GroupMenu) -> None:
    """Test cancelling group color selection."""
    group_menu.app.groups = {"Group1": [], "Group2": []}
    group_menu.app.colors = {"Group1": "red", "Group2": "blue"}

    with (
        patch.object(GroupMenu, "_check_group_selected", return_value="Group1"),
        patch("tkinter.colorchooser.askcolor", return_value=(None, None)),
    ):
        # Reset the build_menu mock
        group_menu.build_menu.reset_mock()

        group_menu.set_group_color()

        # Verify color was not updated
        assert group_menu.app.colors["Group1"] == "red"
        group_menu.build_menu.assert_not_called()


def test_change_group(group_menu: GroupMenu) -> None:
    """Test changing the current group."""
    # Setup mock components
    mock_comp1 = MagicMock()
    mock_comp1.group = "Group1"
    mock_comp2 = MagicMock()
    mock_comp2.group = "Group1"

    group_menu.app.selection = [mock_comp1, mock_comp2]
    group_menu.app.groups = {"Group1": [mock_comp1, mock_comp2], "Group2": []}
    group_menu.current_group.get.return_value = "Group2"

    with patch.object(GroupMenu, "_check_group_selected", return_value="Group2"):
        group_menu.change_group()

        # Verify components were moved to new group
        assert mock_comp1 not in group_menu.app.groups["Group1"]
        assert mock_comp2 not in group_menu.app.groups["Group1"]
        assert mock_comp1 in group_menu.app.groups["Group2"]
        assert mock_comp2 in group_menu.app.groups["Group2"]

        # Verify component groups were updated
        mock_comp1.set_group.assert_called_once_with("Group2")
        mock_comp2.set_group.assert_called_once_with("Group2")

        # Verify label was updated
        group_menu.app.update_label.assert_called_once_with(mock_comp1)


def test_create_color_box() -> None:
    """Test creating a color box."""
    with patch("tkinter.PhotoImage") as mock_photo_image:
        mock_instance = MagicMock()
        mock_photo_image.return_value = mock_instance

        result = GroupMenu.create_color_box("#ff0000")

        # Verify PhotoImage was created
        assert mock_photo_image.called
        assert result == mock_instance
