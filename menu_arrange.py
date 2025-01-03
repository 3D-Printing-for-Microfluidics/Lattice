"""App methods in the Arrange menu."""

from tkinter import simpledialog
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app import App


def align_left(app: "App") -> None:
    """Align selected rectangles to the left."""
    if not app.selected_rectangles:
        return
    min_x = min(rect.x for rect in app.selected_rectangles)
    for rect in app.selected_rectangles:
        rect.set_position(min_x, rect.y)
    app.update_label(app.selected_rectangles[0])


def align_right(app: "App") -> None:
    """Align selected rectangles to the right."""
    if not app.selected_rectangles:
        return
    max_x = max(rect.x + rect.width for rect in app.selected_rectangles)
    for rect in app.selected_rectangles:
        rect.set_position(max_x - rect.width, rect.y)
    app.update_label(app.selected_rectangles[0])


def align_top(app: "App") -> None:
    """Align selected rectangles to the top."""
    if not app.selected_rectangles:
        return
    min_y = min(rect.y for rect in app.selected_rectangles)
    for rect in app.selected_rectangles:
        rect.set_position(rect.x, min_y)
    app.update_label(app.selected_rectangles[0])


def align_bottom(app: "App") -> None:
    """Align selected rectangles to the bottom."""
    if not app.selected_rectangles:
        return
    max_y = max(rect.y + rect.height for rect in app.selected_rectangles)
    for rect in app.selected_rectangles:
        rect.set_position(rect.x, max_y - rect.height)
    app.update_label(app.selected_rectangles[0])


def set_x(app: "App") -> None:
    """Set the X position for all selected rectangles."""
    if not app.selected_rectangles:
        return
    x = simpledialog.askinteger("Set X", "Enter the X position:")
    if x is not None:
        for rect in app.selected_rectangles:
            rect.set_position(x, rect.y)
        app.update_label(app.selected_rectangles[0])


def set_y(app: "App") -> None:
    """Set the Y position for all selected rectangles."""
    if not app.selected_rectangles:
        return
    y = simpledialog.askinteger("Set Y", "Enter the Y position:")
    if y is not None:
        for rect in app.selected_rectangles:
            rect.set_position(rect.x, y)
        app.update_label(app.selected_rectangles[0])
