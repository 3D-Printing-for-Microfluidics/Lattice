"""Test suite for popup module."""

import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from app.popup import Popup


@pytest.fixture
def mock_tk():
    """Mock tkinter components."""
    # Create mock parent
    mock_parent = MagicMock(spec=tk.Tk)
    mock_parent.winfo_screenwidth.return_value = 1920
    mock_parent.winfo_screenheight.return_value = 1080
    mock_parent.update = MagicMock()

    # Create mock toplevel
    mock_toplevel = MagicMock(spec=tk.Toplevel)
    mock_toplevel.title = MagicMock()
    mock_toplevel.geometry = MagicMock()
    mock_toplevel.transient = MagicMock()
    mock_toplevel.grab_set = MagicMock()
    mock_toplevel.destroy = MagicMock()

    with (
        patch("tkinter.Toplevel", return_value=mock_toplevel),
        patch("tkinter.Label"),
    ):
        yield {"parent": mock_parent, "toplevel": mock_toplevel}


def test_popup_initialization(mock_tk: dict):
    """Test popup initialization and positioning."""
    # Create popup with test message
    Popup(mock_tk["parent"], "Test Message")

    # Check that toplevel was created with parent
    tk.Toplevel.assert_called_once_with(mock_tk["parent"])

    # Check that title was set
    mock_tk["toplevel"].title.assert_called_once_with("Processing")

    # Check that geometry was set (centered on screen)
    mock_tk["toplevel"].geometry.assert_called_once()
    geometry_arg = mock_tk["toplevel"].geometry.call_args[0][0]
    assert geometry_arg.startswith("200x50+")

    # Check that window is transient
    mock_tk["toplevel"].transient.assert_called_once_with(mock_tk["parent"])

    # Check that grab_set was called
    mock_tk["toplevel"].grab_set.assert_called_once()

    # Check that parent update was called
    mock_tk["parent"].update.assert_called_once()

    # Check that Label was created with message
    tk.Label.assert_called_once()
    label_args = tk.Label.call_args
    assert label_args[0][0] == mock_tk["toplevel"]
    assert label_args[1]["text"] == "Test Message"


def test_popup_destroy(mock_tk: dict):
    """Test popup destruction."""
    # Create popup
    popup = Popup(mock_tk["parent"], "Test Message")

    # Call destroy
    popup.destroy()

    # Check that toplevel destroy was called
    mock_tk["toplevel"].destroy.assert_called_once()


def test_popup_centering_calculation(mock_tk: dict):
    """Test the centering calculation for the popup."""
    # Create popup
    _ = Popup(mock_tk["parent"], "Test Message")

    # Calculate expected position
    w, h = 200, 50
    ws = 1920  # Mock screen width
    hs = 1080  # Mock screen height
    expected_x = int((ws / 2) - (w / 2))
    expected_y = int((hs / 2) - (h / 2))
    expected_geometry = f"200x50+{expected_x}+{expected_y}"

    # Check that geometry was set correctly
    mock_tk["toplevel"].geometry.assert_called_once_with(expected_geometry)


def test_popup_with_different_message(mock_tk: dict):
    """Test popup with a different message."""
    # Create popup with a different message
    _ = Popup(mock_tk["parent"], "Processing, please wait...")
