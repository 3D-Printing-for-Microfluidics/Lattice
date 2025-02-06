"""App methods in the Arrange menu."""

from tkinter import simpledialog
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app import App


def align_left(app: "App") -> None:
    """Align selected components to the left."""
    if not app.selection:
        return
    min_x = min(comp.x for comp in app.selection)
    for comp in app.selection:
        comp.set_position(min_x, comp.y)
    app.update_label(app.selection[0])


def align_right(app: "App") -> None:
    """Align selected components to the right."""
    if not app.selection:
        return
    max_x = max(comp.x + comp.width for comp in app.selection)
    for comp in app.selection:
        comp.set_position(max_x - comp.width, comp.y)
    app.update_label(app.selection[0])


def align_top(app: "App") -> None:
    """Align selected components to the top."""
    if not app.selection:
        return
    min_y = min(comp.y for comp in app.selection)
    for comp in app.selection:
        comp.set_position(comp.x, min_y)
    app.update_label(app.selection[0])


def align_bottom(app: "App") -> None:
    """Align selected components to the bottom."""
    if not app.selection:
        return
    max_y = max(comp.y + comp.height for comp in app.selection)
    for comp in app.selection:
        comp.set_position(comp.x, max_y - comp.height)
    app.update_label(app.selection[0])


def set_x(app: "App") -> None:
    """Set the X position for all selected components."""
    if not app.selection:
        return
    x = simpledialog.askinteger("Set X", "Enter the X position:")
    if x is not None:
        for comp in app.selection:
            comp.set_position(x, comp.y)
        app.update_label(app.selection[0])


def set_y(app: "App") -> None:
    """Set the Y position for all selected components."""
    if not app.selection:
        return
    y = simpledialog.askinteger("Set Y", "Enter the Y position:")
    if y is not None:
        for comp in app.selection:
            comp.set_position(comp.x, y)
        app.update_label(app.selection[0])
