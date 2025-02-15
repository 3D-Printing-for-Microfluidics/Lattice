"""App methods in the View menu."""

import tkinter as tk
from typing import TYPE_CHECKING

from constants import CANVAS_HEIGHT, CANVAS_WIDTH

if TYPE_CHECKING:
    from app import App


class ViewMenu:
    """Create and handle the View menu and its actions."""

    def __init__(self, app: "App", menubar: tk.Menu) -> None:
        """Initialize the ViewMenu class.

        Parameters
        ----------
        app : App
            The application instance.
        menubar : tk.Menu
            The Tkinter menubar to which the View menu is added.

        """
        self.app = app
        menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=menu)
        menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl+=")
        menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")

        # Bind shortcuts
        self.app.root.bind_all("<Control-equal>", lambda _: self.zoom_in())
        self.app.root.bind_all("<Control-minus>", lambda _: self.zoom_out())

    def zoom_in(self) -> None:
        """Increase zoom by 10%."""
        self.app.zoom_factor = getattr(self.app, "zoom_factor", 1.0) + 0.1
        self.redraw_canvas()

    def zoom_out(self) -> None:
        """Decrease zoom by 10%."""
        self.app.zoom_factor = max(0.1, getattr(self.app, "zoom_factor", 1.0) - 0.1)
        self.redraw_canvas()

    def redraw_canvas(self) -> None:
        """Update the canvas and its contents based on current zoom level."""
        new_width = int(CANVAS_WIDTH * self.app.zoom_factor)
        new_height = int(CANVAS_HEIGHT * self.app.zoom_factor)
        self.app.canvas.config(width=new_width, height=new_height)
        self.app.canvas.config(scrollregion=(0, 0, new_width, new_height))

        # Adjust all components' positions and sizes
        for group in self.app.groups.values():
            for comp in group:
                comp.redraw_for_zoom()
