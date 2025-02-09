"""App methods in the Arrange menu."""

import tkinter as tk
from tkinter import simpledialog
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app import App


class ArrangeMenu:
    """Create and handle the Arrange menu and its actions.

    Attributes
    ----------
    app : App
        The parent application instance.

    """

    def __init__(self, app: "App", menubar: tk.Menu) -> None:
        """Initialize the ArrangeMenu class and bind keyboard shortcuts.

        Parameters
        ----------
        app : App
            The application instance.
        menubar : tk.Menu
            The Tkinter menubar to which the Arrange menu is added.

        """
        self.app = app
        menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arrange", menu=menu)
        menu.add_command(label="Set X", command=self.set_x, accelerator="Ctrl+X")
        menu.add_command(label="Set Y", command=self.set_y, accelerator="Ctrl+Y")
        menu.add_separator()
        menu.add_command(label="Align Left", command=self.align_left, accelerator="Ctrl+L")
        menu.add_command(label="Align Right", command=self.align_right, accelerator="Ctrl+R")
        menu.add_command(label="Align Top", command=self.align_top, accelerator="Ctrl+T")
        menu.add_command(label="Align Bottom", command=self.align_bottom, accelerator="Ctrl+B")

        self.app.root.bind_all("<Control-x>", lambda _: self.set_x())
        self.app.root.bind_all("<Control-y>", lambda _: self.set_y())
        self.app.root.bind_all("<Control-l>", lambda _: self.align_left())
        self.app.root.bind_all("<Control-r>", lambda _: self.align_right())
        self.app.root.bind_all("<Control-t>", lambda _: self.align_top())
        self.app.root.bind_all("<Control-b>", lambda _: self.align_bottom())

    def align_left(self) -> None:
        """Align selected components to the left."""
        if not self.app.selection:
            return
        min_x = min(comp.x for comp in self.app.selection)
        for comp in self.app.selection:
            comp.set_position(min_x, comp.y)
        self.app.update_label(self.app.selection[0])

    def align_right(self) -> None:
        """Align selected components to the right."""
        if not self.app.selection:
            return
        max_x = max(comp.x + comp.width for comp in self.app.selection)
        for comp in self.app.selection:
            comp.set_position(max_x - comp.width, comp.y)
        self.app.update_label(self.app.selection[0])

    def align_top(self) -> None:
        """Align selected components to the top."""
        if not self.app.selection:
            return
        min_y = min(comp.y for comp in self.app.selection)
        for comp in self.app.selection:
            comp.set_position(comp.x, min_y)
        self.app.update_label(self.app.selection[0])

    def align_bottom(self) -> None:
        """Align selected components to the bottom."""
        if not self.app.selection:
            return
        max_y = max(comp.y + comp.height for comp in self.app.selection)
        for comp in self.app.selection:
            comp.set_position(comp.x, max_y - comp.height)
        self.app.update_label(self.app.selection[0])

    def set_x(self) -> None:
        """Set the X position for all selected components."""
        if not self.app.selection:
            return
        x = simpledialog.askinteger("Set X", "Enter the X position:")
        if x is not None:
            for comp in self.app.selection:
                comp.set_position(x, comp.y)
            self.app.update_label(self.app.selection[0])

    def set_y(self) -> None:
        """Set the Y position for all selected components."""
        if not self.app.selection:
            return
        y = simpledialog.askinteger("Set Y", "Enter the Y position:")
        if y is not None:
            for comp in self.app.selection:
                comp.set_position(comp.x, y)
            self.app.update_label(self.app.selection[0])
