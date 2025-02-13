"""UI for 3D Print Dose Customization.

TODO:
- Add load component to file menu?
- Add absolute vs. scale option for exposure scaling
- Only allow floats in group names
- Cutout tool for component selection?
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING

from constants import CANVAS_HEIGHT, CANVAS_WIDTH
from menus.arrange_menu import ArrangeMenu
from menus.file_menu import FileMenu
from menus.group_menu import GroupMenu
from menus.object_menu import ObjectMenu
from menus.view_menu import ViewMenu

if TYPE_CHECKING:
    from component import Component

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class App:
    """Main control and UI for dose customization.

    Attributes
    ----------
    root : tk.Tk
        The root window of the Tkinter application.
    comp_width : int
        The default width for newly created components.
    comp_height : int
        The default height for newly created components.
    selection : list[Component]
        The list of selected components.
    groups : dict[str, list[Component]]
        The dictionary of groups and their components.
    colors : dict[str, str]
        The dictionary of groups and their colors.
    color_boxes : dict[str, tk.PhotoImage]
        The dictionary of color box images.
    selection_rect : int | None
        The ID of the selection rectangle on the canvas.
    selection_start_x : float | None
        The X coordinate where a drag-selection started.
    selection_start_y : float | None
        The Y coordinate where a drag-selection started.
    dimensions_label : tk.Label
        Displays information about the selected component.
    canvas : tk.Canvas
        The canvas on which components are drawn.
    component_file : str
        The path to the zip file containing the component.

    """

    def __init__(self) -> None:
        """Initialize the App."""
        self.root = tk.Tk()
        self.root.title("3D Print Dose Customization")
        self.comp_width = 100
        self.comp_height = 100
        self.selection = []
        self.groups = {}
        self.colors = {}
        self.color_boxes = {}
        self.selection_rect = None
        self.selection_start_x = None
        self.selection_start_y = None
        self.component_file = self.select_component_file()
        self.zoom_factor = 1.0  # Add zoom factor attribute

        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        self.file_menu = FileMenu(self, menubar)
        self.view_menu = ViewMenu(self, menubar)  # Add view menu
        self.group_menu = GroupMenu(self, menubar)
        self.object_menu = ObjectMenu(self, menubar)
        self.arrange_menu = ArrangeMenu(self, menubar)
        self.create_label()
        self.create_canvas()
        self.root.mainloop()

    def create_label(self) -> None:
        """Create the dimensions label."""
        self.dimensions_label = tk.Label(self.root, text="", bg="lightgray")
        self.dimensions_label.pack(side=tk.TOP, fill=tk.X)

    def update_label(self, comp: Component | None) -> None:
        """Update the label with the dimensions and coordinates of the component.

        Parameters
        ----------
        comp : Component | None
            The component whose information is to be displayed or None if no component is selected.

        """
        if comp is None:
            self.dimensions_label.config(text="")
            return
        text = f"X: {comp.x}, Y: {comp.y}, Width: {comp.width}, Height: {comp.height}, Group: {comp.group}"
        self.dimensions_label.config(text=text)

    def create_canvas(self) -> None:
        """Create the canvas with scrollbars."""
        # Set the main window to start maximized
        self.root.state("zoomed")

        # Create a main frame to hold the canvas and the vertical scrollbar
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create a frame for the canvas and vertical scrollbar
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create the canvas with a fixed size and scroll region
        self.canvas = tk.Canvas(self.canvas_frame, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.NONE, expand=False)

        # Create scrollbars and attach them to the canvas
        self.v_scrollbar = tk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar = tk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.config(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)
        self.canvas.config(scrollregion=(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT))

        # Bind events to the canvas
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Prevent the canvas from resizing when the window is resized
        self.canvas_frame.pack_propagate(flag=False)
        self.canvas.pack_propagate(flag=False)

    def clear_canvas(self) -> None:
        """Clear all components from the canvas."""
        self.canvas.delete("all")

    def on_canvas_click(self, event: tk.Event) -> None:
        """Handle the click event on the canvas."""
        x = self.canvas.canvasx(event.x) / self.zoom_factor
        y = self.canvas.canvasy(event.y) / self.zoom_factor
        logger.debug("Click at (%d, %d)", x, y)

        if not self.canvas.find_withtag("current"):  # nothing was under cursor when clicked
            self.deselect_all()
            self.selection_start_x = x
            self.selection_start_y = y
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)
                self.selection_rect = None
        else:
            self.selection_start_x = None
            self.selection_start_y = None

    def on_canvas_drag(self, event: tk.Event) -> None:
        """Handle the drag event on the canvas."""
        if self.selection_start_x is not None and self.selection_start_y is not None:
            x = self.canvas.canvasx(event.x) / self.zoom_factor
            y = self.canvas.canvasy(event.y) / self.zoom_factor

            if self.selection_rect:
                self.canvas.delete(self.selection_rect)

            # Scale coordinates for display
            scaled_start_x = self.selection_start_x * self.zoom_factor
            scaled_start_y = self.selection_start_y * self.zoom_factor
            scaled_x = x * self.zoom_factor
            scaled_y = y * self.zoom_factor

            self.selection_rect = self.canvas.create_rectangle(
                scaled_start_x,
                scaled_start_y,
                scaled_x,
                scaled_y,
                outline="blue",
                dash=(2, 2),
            )

    def on_canvas_release(self, event: tk.Event) -> None:
        """Handle the release event on the canvas."""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        logger.debug("Release at (%d, %d)", x, y)
        if self.selection_rect:
            x1, y1, x2, y2 = self.canvas.coords(self.selection_rect)
            self.select_components_in_area(x1, y1, x2, y2)
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None

    def select_components_in_area(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Select all components within the specified area."""
        # Convert selection coordinates to unscaled coordinates
        x1 = x1 / self.zoom_factor
        y1 = y1 / self.zoom_factor
        x2 = x2 / self.zoom_factor
        y2 = y2 / self.zoom_factor

        for group in self.groups.values():
            for comp in group:
                if (
                    comp.x >= min(x1, x2)
                    and comp.x + comp.width <= max(x1, x2)
                    and comp.y >= min(y1, y2)
                    and comp.y + comp.height <= max(y1, y2)
                ):
                    comp.select()
        if self.selection:
            self.update_label(self.selection[0])

    def deselect_all(self) -> None:
        """Deselect all components."""
        for comp in self.selection[:]:  # operate on a copy of the list since it will be modified
            comp.deselect()
        self.update_label(None)

    @staticmethod
    def select_component_file() -> None:
        """Popup to select a component file."""
        messagebox.showinfo("Select Component", "Please select a component zip file to begin.")
        return filedialog.askopenfilename(title="Select component zip file.", filetypes=[("Zip", "*.zip")])


if __name__ == "__main__":
    App()
