"""App methods in the View menu."""

import tkinter as tk

from app.menus.menu import Menu


class ViewMenu(Menu):
    """Create and handle the View menu and its actions."""

    def _create_menu(self, menubar: tk.Menu) -> None:
        """Create the view menu items."""
        menubar.add_cascade(label="View", menu=self.menu)
        self.menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl+=")
        self.menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")

    def _bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts."""
        self.app.root.bind_all("<Control-equal>", lambda _: self.zoom_in())
        self.app.root.bind_all("<Control-minus>", lambda _: self.zoom_out())

    def zoom_in(self) -> None:
        """Increase zoom by 10%."""
        self.app.zoom_factor = getattr(self.app, "zoom_factor", 1.0) + 0.1
        self.app.redraw_canvas()

    def zoom_out(self) -> None:
        """Decrease zoom by 10%."""
        self.app.zoom_factor = max(0.1, getattr(self.app, "zoom_factor", 1.0) - 0.1)
        self.app.redraw_canvas()
