"""App methods in the Arrange menu."""

import tkinter as tk
from tkinter import simpledialog

from app.menus.menu import Menu


class ArrangeMenu(Menu):
    """Create and handle the Arrange menu and its actions."""

    def _create_menu(self, menubar: tk.Menu) -> None:
        """Create the arrange menu items.

        Parameters
        ----------
        menubar: tk.Menu
            The menubar to attach to.

        """
        menubar.add_cascade(label="Arrange", menu=self.menu)
        self.menu.add_command(label="Set X", command=self.set_x, accelerator="Ctrl+X")
        self.menu.add_command(label="Set Y", command=self.set_y, accelerator="Ctrl+Y")
        self.menu.add_separator()
        self.menu.add_command(label="Align Left", command=self.align_left, accelerator="Ctrl+←")
        self.menu.add_command(label="Align Right", command=self.align_right, accelerator="Ctrl+→")
        self.menu.add_command(label="Align Top", command=self.align_top, accelerator="Ctrl+↑")
        self.menu.add_command(label="Align Bottom", command=self.align_bottom, accelerator="Ctrl+↓")

    def _bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts."""
        self.app.root.bind_all("<Control-x>", lambda _: self.set_x())
        self.app.root.bind_all("<Control-y>", lambda _: self.set_y())
        self.app.root.bind_all("<Control-Left>", lambda _: self.align_left())
        self.app.root.bind_all("<Control-Right>", lambda _: self.align_right())
        self.app.root.bind_all("<Control-Up>", lambda _: self.align_top())
        self.app.root.bind_all("<Control-Down>", lambda _: self.align_bottom())

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
        max_x = max(comp.x + self.app.comp_width for comp in self.app.selection)
        for comp in self.app.selection:
            comp.set_position(max_x - self.app.comp_width, comp.y)
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
        max_y = max(comp.y + self.app.comp_height for comp in self.app.selection)
        for comp in self.app.selection:
            comp.set_position(comp.x, max_y - self.app.comp_height)
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
