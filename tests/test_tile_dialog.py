"""Test suite for tile dialog module."""

import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from app.tile_dialog import TileDialog


@pytest.fixture
def mock_tk():
    """Mock tkinter components."""
    # Create mock parent
    mock_parent = MagicMock(spec=tk.Tk)

    # Create mock toplevel
    mock_toplevel = MagicMock(spec=tk.Toplevel)
    mock_toplevel.title = MagicMock()
    mock_toplevel.destroy = MagicMock()

    # Create mock entry
    mock_entry = MagicMock(spec=tk.Entry)
    mock_entry.grid = MagicMock()
    mock_entry.get = MagicMock()

    with (
        patch("tkinter.Toplevel", return_value=mock_toplevel),
        patch("tkinter.Label"),
        patch("tkinter.Entry", return_value=mock_entry),
        patch("tkinter.Button"),
        patch("tkinter.messagebox.showerror"),
    ):
        yield {"parent": mock_parent, "toplevel": mock_toplevel, "entry": mock_entry}


def test_tile_dialog_initialization(mock_tk: dict):
    """Test tile dialog initialization."""
    # Create dialog
    dialog = TileDialog(mock_tk["parent"])

    # Check that toplevel was created with parent
    tk.Toplevel.assert_called_once_with(mock_tk["parent"])

    # Check that title was set
    mock_tk["toplevel"].title.assert_called_once_with("Tile Rectangles")

    # Check that entries were created
    assert tk.Entry.call_count == 6

    # Check that labels were created
    assert tk.Label.call_count == 6

    # Check that buttons were created
    assert tk.Button.call_count == 2

    # Check initial result is None
    assert dialog.result is None


def test_tile_dialog_ok_valid_input(mock_tk: dict):
    """Test OK button with valid input."""
    # Create dialog
    dialog = TileDialog(mock_tk["parent"])

    # Set up mock entry to return valid integers
    mock_tk["entry"].get.side_effect = ["10", "20", "30", "40", "2", "3"]

    # Call OK method
    dialog.ok()

    # Check that result was set correctly
    assert dialog.result == (10, 20, 30, 40, 2, 3)

    # Check that toplevel was destroyed
    mock_tk["toplevel"].destroy.assert_called_once()


def test_tile_dialog_ok_invalid_input(mock_tk: dict):
    """Test OK button with invalid input."""
    # Create dialog
    dialog = TileDialog(mock_tk["parent"])

    # Set up mock entry to return invalid input
    mock_tk["entry"].get.side_effect = ["10", "not_a_number", "30", "40", "2", "3"]

    # Call OK method
    dialog.ok()

    # Check that error message was shown
    tk.messagebox.showerror.assert_called_once_with("Error", "Please enter valid integers.")

    # Check that result was not set
    assert dialog.result is None

    # Check that toplevel was not destroyed
    mock_tk["toplevel"].destroy.assert_not_called()


def test_tile_dialog_cancel(mock_tk: dict):
    """Test cancel button."""
    # Create dialog
    dialog = TileDialog(mock_tk["parent"])

    # Call cancel method
    dialog.cancel()

    # Check that toplevel was destroyed
    mock_tk["toplevel"].destroy.assert_called_once()

    # Check that result remains None
    assert dialog.result is None


def test_tile_dialog_all_fields_required(mock_tk: dict):
    """Test that all fields are required."""
    # Create dialog
    dialog = TileDialog(mock_tk["parent"])

    # Set up mock entry to return empty string for one field
    mock_tk["entry"].get.side_effect = ["10", "20", "", "40", "2", "3"]

    # Call OK method
    dialog.ok()

    # Check that error message was shown
    tk.messagebox.showerror.assert_called_once()

    # Check that result was not set
    assert dialog.result is None


def test_tile_dialog_negative_values(mock_tk: dict):
    """Test with negative values."""
    # Create dialog
    dialog = TileDialog(mock_tk["parent"])

    # Set up mock entry to return negative values
    mock_tk["entry"].get.side_effect = ["-10", "20", "30", "40", "2", "3"]

    # Call OK method
    dialog.ok()

    # Check that result was set with negative values
    assert dialog.result == (-10, 20, 30, 40, 2, 3)

    # Check that toplevel was destroyed
    mock_tk["toplevel"].destroy.assert_called_once()
