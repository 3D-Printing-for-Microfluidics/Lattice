"""UI for 3D Print Dose Customization."""

from __future__ import annotations

import json
import logging
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, simpledialog

from rectangle import Rectangle
from tile_dialog import TileDialog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RectangleApp:
    """A class used to represent the Rectangle Application with a Tkinter GUI.

    Attributes
    ----------
    root : tk.Tk
        The root window of the Tkinter application.
    button_bar : tk.Frame
        The frame containing the buttons.
    dimensions_label : tk.Label
        The label displaying the dimensions and coordinates of the selected rectangle.
    canvas : tk.Canvas
        The canvas on which rectangles are drawn.
    rectangles : list[Rectangle]
        The list of rectangles.
    selected_rectangles : list[Rectangle]
        The list of selected rectangles.
    groups : dict[str, list[Rectangle]]
        The dictionary of groups and their rectangles.
    colors : dict[str, str]
        The dictionary of groups and their colors.
    color_boxes : dict[str, tk.PhotoImage]
        The dictionary of color box images.
    selection_rect : int | None
        The ID of the selection rectangle on the canvas.

    """

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the RectangleApp.

        Parameters
        ----------
        root : tk.Tk
            The root window of the Tkinter application.

        """
        self.root = root
        self.root.title("3D Print Dose Customization")
        self.rectangles = []
        self.selected_rectangles = []
        self.groups = {}
        self.colors = {}
        self.color_boxes = {}
        self.selection_rect = None
        self.start_x = None
        self.start_y = None
        self.create_ui()

    def create_ui(self) -> None:
        """Create the base UI."""
        self.create_menu_bar()
        self.create_label()
        self.create_canvas()
        self.bind_shortcuts()

    def create_menu_bar(self) -> None:
        """Create the menu bar."""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.load_json, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_json, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        self.group_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Group", menu=self.group_menu)

        self.group_var = tk.StringVar()
        self.update_group_dropdown()

        rectangle_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Object", menu=rectangle_menu)
        rectangle_menu.add_command(label="Add", command=self.add_rectangle, accelerator="Ctrl+A")
        rectangle_menu.add_command(label="Delete", command=self.delete_rectangle, accelerator="Ctrl+D")
        rectangle_menu.add_separator()
        rectangle_menu.add_command(label="Tile Create", command=self.tile)

        arrange_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Arrange", menu=arrange_menu)
        arrange_menu.add_command(label="Set X", command=self.set_x, accelerator="Ctrl+X")
        arrange_menu.add_command(label="Set Y", command=self.set_y, accelerator="Ctrl+Y")
        arrange_menu.add_separator()
        arrange_menu.add_command(label="Align Left", command=self.align_left, accelerator="Ctrl+L")
        arrange_menu.add_command(label="Align Right", command=self.align_right, accelerator="Ctrl+R")
        arrange_menu.add_command(label="Align Top", command=self.align_top, accelerator="Ctrl+T")
        arrange_menu.add_command(label="Align Bottom", command=self.align_bottom, accelerator="Ctrl+B")

    def bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts."""
        self.root.bind_all("<Control-a>", lambda _: self.add_rectangle())
        self.root.bind_all("<Control-d>", lambda _: self.delete_rectangle())
        self.root.bind_all("<Control-g>", lambda _: self.new_group())
        self.root.bind_all("<Control-o>", lambda _: self.load_json())
        self.root.bind_all("<Control-s>", lambda _: self.save_json())
        self.root.bind_all("<Control-x>", lambda _: self.set_x())
        self.root.bind_all("<Control-y>", lambda _: self.set_y())
        self.root.bind_all("<Control-l>", lambda _: self.align_left())
        self.root.bind_all("<Control-r>", lambda _: self.align_right())
        self.root.bind_all("<Control-t>", lambda _: self.align_top())
        self.root.bind_all("<Control-b>", lambda _: self.align_bottom())

    def create_label(self) -> None:
        """Create the dimensions label."""
        self.dimensions_label = tk.Label(self.root, text="", bg="lightgray")
        self.dimensions_label.pack(side=tk.TOP, fill=tk.X)

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
        self.canvas = tk.Canvas(self.canvas_frame, width=2000, height=1000, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.NONE, expand=False)

        # Create scrollbars and attach them to the canvas
        self.v_scrollbar = tk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar = tk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.config(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)
        self.canvas.config(scrollregion=(0, 0, 2000, 1000))

        # Bind events to the canvas
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

    def on_canvas_click(self, event: tk.Event) -> None:
        """Handle the click event on the canvas."""
        logger.debug("Click at (%d, %d)", event.x, event.y)
        self.start_x = event.x
        self.start_y = event.y
        if not self.canvas.find_withtag("current"):
            self.deselect_all()
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)
                self.selection_rect = None
        else:
            self.start_x = None
            self.start_y = None

    def on_canvas_drag(self, event: tk.Event) -> None:
        """Handle the drag event on the canvas."""
        if self.start_x is not None and self.start_y is not None:
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)
            self.selection_rect = self.canvas.create_rectangle(
                self.start_x,
                self.start_y,
                event.x,
                event.y,
                outline="blue",
                dash=(2, 2),
            )

    def on_canvas_release(self, event: tk.Event) -> None:
        """Handle the release event on the canvas."""
        logger.debug("Release at (%d, %d)", event.x, event.y)
        if self.selection_rect:
            x1, y1, x2, y2 = self.canvas.coords(self.selection_rect)
            self.select_rectangles_in_area(x1, y1, x2, y2)
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None

    def select_rectangles_in_area(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Select all rectangles within the specified area."""
        for rect in self.rectangles:
            if (
                rect.x >= min(x1, x2)
                and rect.x + rect.width <= max(x1, x2)
                and rect.y >= min(y1, y2)
                and rect.y + rect.height <= max(y1, y2)
            ):
                rect.select()
        if self.selected_rectangles:
            self.update_label(self.selected_rectangles[0])

    def update_group_dropdown(self) -> None:
        """Update the group dropdown menu."""
        self.group_menu.delete(0, "end")
        self.group_menu.add_command(label="New Group", command=self.new_group, accelerator="Ctrl+G")
        self.group_menu.add_command(label="Delete Group", command=self.delete_group)
        self.group_menu.add_separator()
        self.group_menu.add_command(label="- Groups -", state=tk.DISABLED)

        self.color_boxes.clear()
        for group in self.groups:
            color = self.colors[group]
            label = f"  {group}"
            color_box = self.create_color_box(color)
            self.color_boxes[group] = color_box
            self.group_menu.add_radiobutton(
                label=label,
                variable=self.group_var,
                value=group,
                indicatoron=1,
                compound=tk.LEFT,
                image=color_box,
            )

        self.group_menu.add_command(label="Rename Group", command=self.rename_group)
        self.group_menu.add_command(label="Change Group Color", command=self.set_group_color)
        self.group_menu.add_command(label="Change Selection to Current Group", command=self.change_group)
        if self.groups:
            self.group_var.set(list(self.groups.keys())[-1])

    def create_color_box(self, color: str) -> tk.PhotoImage:
        """Create a small colored box for the group label.

        Parameters
        ----------
        color : str
            The color of the box.

        Returns
        -------
        tk.PhotoImage
            The image of the colored box.

        """
        size = 10
        image = tk.PhotoImage(width=size, height=size)
        image.put(color, to=(0, 0, size, size))
        return image

    def add_rectangle(self) -> None:
        """Add a new rectangle to the canvas."""
        group = self.group_var.get()
        if not group:
            simpledialog.messagebox.showerror("Error", "No group is selected. Create or select a group to begin.")
            return
        x, y, width, height = 50, 50, 100, 100
        rectangle = Rectangle(self, x, y, width, height, group)
        rectangle.set_color(self.colors[group])
        self.rectangles.append(rectangle)
        self.deselect_all()
        rectangle.select()
        self.update_label(rectangle)

    def delete_rectangle(self) -> None:
        """Delete the selected rectangles from the canvas."""
        for rect in self.selected_rectangles:
            rect.delete()
            self.rectangles.remove(rect)
        self.selected_rectangles.clear()

    def deselect_all(self) -> None:
        """Deselect all rectangles."""
        for rect in self.rectangles:
            rect.deselect()
        self.selected_rectangles.clear()
        self.update_label(None)

    def align_left(self) -> None:
        """Align selected rectangles to the left."""
        if not self.selected_rectangles:
            return
        min_x = min(rect.x for rect in self.selected_rectangles)
        for rect in self.selected_rectangles:
            rect.set_position(min_x, rect.y)
        self.update_label(self.selected_rectangles[0])

    def align_right(self) -> None:
        """Align selected rectangles to the right."""
        if not self.selected_rectangles:
            return
        max_x = max(rect.x + rect.width for rect in self.selected_rectangles)
        for rect in self.selected_rectangles:
            rect.set_position(max_x - rect.width, rect.y)
        self.update_label(self.selected_rectangles[0])

    def align_top(self) -> None:
        """Align selected rectangles to the top."""
        if not self.selected_rectangles:
            return
        min_y = min(rect.y for rect in self.selected_rectangles)
        for rect in self.selected_rectangles:
            rect.set_position(rect.x, min_y)
        self.update_label(self.selected_rectangles[0])

    def align_bottom(self) -> None:
        """Align selected rectangles to the bottom."""
        if not self.selected_rectangles:
            return
        max_y = max(rect.y + rect.height for rect in self.selected_rectangles)
        for rect in self.selected_rectangles:
            rect.set_position(rect.x, max_y - rect.height)
        self.update_label(self.selected_rectangles[0])

    def set_x(self) -> None:
        """Set the X position for all selected rectangles."""
        if not self.selected_rectangles:
            return
        x = simpledialog.askinteger("Set X", "Enter the X position:")
        if x is not None:
            for rect in self.selected_rectangles:
                rect.set_position(x, rect.y)
            self.update_label(self.selected_rectangles[0])

    def set_y(self) -> None:
        """Set the Y position for all selected rectangles."""
        if not self.selected_rectangles:
            return
        y = simpledialog.askinteger("Set Y", "Enter the Y position:")
        if y is not None:
            for rect in self.selected_rectangles:
                rect.set_position(rect.x, y)
            self.update_label(self.selected_rectangles[0])

    def tile(self) -> None:
        """Tile rectangles based on user input."""
        group = self.group_var.get()
        if not group:
            simpledialog.messagebox.showerror("Error", "No group is selected. Create or select a group to begin.")
            return

        dialog = TileDialog(self.root)
        self.root.wait_window(dialog.top)
        if dialog.result:
            x_start, y_start, x_spacing, y_spacing, num_x, num_y = dialog.result
            for i in range(num_x):
                for j in range(num_y):
                    x = x_start + i * x_spacing
                    y = y_start + j * y_spacing
                    rectangle = Rectangle(self, x, y, 100, 100, group)
                    rectangle.set_color(self.colors[group])
                    self.rectangles.append(rectangle)
            self.update_label(self.rectangles[-1])

    def save_json(self) -> None:
        """Save the rectangles and colors to a JSON file."""
        data = {
            "rectangles": [rect.to_dict() for rect in self.rectangles],
            "colors": self.colors,
        }
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile="rectangles.json",
            filetypes=[("JSON files", "*.json")],
        )
        if filename:
            with Path(filename).open("w") as f:
                json.dump(data, f)

    def load_json(self) -> None:
        """Load rectangles and colors from a JSON file."""
        filename = filedialog.askopenfilename(
            defaultextension=".json",
            initialfile="rectangles.json",
            filetypes=[("JSON files", "*.json")],
        )
        if not filename:  # Dialog was closed without selecting a file
            return
        try:
            with Path(filename).open() as f:
                data = json.load(f)
        except FileNotFoundError:
            simpledialog.messagebox.showerror("Error", "File not found.")
            return
        except json.JSONDecodeError:
            simpledialog.messagebox.showerror("Error", "Invalid JSON file.")
            return

        self.rectangles.clear()
        self.colors = data.get("colors", {})
        self.groups = {group: [] for group in self.colors}

        for rect_data in data.get("rectangles", []):
            rectangle = Rectangle(
                self,
                rect_data["x"],
                rect_data["y"],
                rect_data["width"],
                rect_data["height"],
                rect_data["group"],
            )
            rectangle.set_color(self.colors[rect_data["group"]])
            self.groups[rect_data["group"]].append(rectangle)
            self.rectangles.append(rectangle)

        self.update_group_dropdown()

    def update_label(self, rect: Rectangle | None) -> None:
        """Update the label with the dimensions and coordinates of the rectangle.

        Parameters
        ----------
        rect : Rectangle | None
            The rectangle whose information is to be displayed or None if no rectangle is selected.

        """
        if rect is None:
            self.dimensions_label.config(text="")
            return
        text = f"X: {rect.x}, Y: {rect.y}, Width: {rect.width}, Height: {rect.height}, Group: {rect.group}"
        self.dimensions_label.config(text=text)

    def new_group(self) -> None:
        """Create a new group."""
        group_name = simpledialog.askstring("Group Name", "Enter a name for the new group:")
        if not group_name:
            simpledialog.messagebox.showerror("Error", "Please enter a name for the group.")
            return
        if group_name in self.groups:
            simpledialog.messagebox.showerror("Error", "Group already exists.")
            return
        self.set_group_color()
        if group_name not in self.colors:
            simpledialog.messagebox.showerror("Error", "Please select a color for the new group.")
            return
        self.groups[group_name] = []
        self.group_var.set(group_name)
        self.update_group_dropdown()

    def delete_group(self) -> None:
        """Delete the currently selected group and its rectangles."""
        group = self.group_var.get()
        if not group:
            simpledialog.messagebox.showerror("Error", "No group is selected.")
            return

        del_msg = f"Are you sure you want to delete the group '{group}'?"
        del_msg += "\nThe group and all rectangles in this group will be deleted."
        if simpledialog.messagebox.askyesno("Delete Group", del_msg):
            for rect in self.groups[group]:
                self.rectangles.remove(rect)
                rect.delete()
            del self.groups[group]
            del self.colors[group]
            self.update_group_dropdown()
            self.deselect_all()

    def rename_group(self) -> None:
        """Rename the current group."""
        current_group = self.group_var.get()
        if not current_group:
            simpledialog.messagebox.showerror("Error", "No group is selected.")
            return
        new_group_name = simpledialog.askstring("Rename Group", f"Enter a new name for Group '{current_group}':")
        if new_group_name and new_group_name != current_group:
            self.groups[new_group_name] = self.groups.pop(current_group, [])
            self.colors[new_group_name] = self.colors.pop(current_group, "blue")
            self.update_group_dropdown()
            for rect in self.rectangles:
                if rect.group == current_group:
                    rect.set_group(new_group_name)
                    self.update_label(None)

    def set_group_color(self) -> None:
        """Set the color of the current group."""
        group = self.group_var.get()
        if not group:
            simpledialog.messagebox.showerror("Error", "No group is selected.")
            return
        color = colorchooser.askcolor()[1]
        if color:
            self.colors[group] = color
            for rect in self.rectangles:
                if rect.group == group:
                    rect.set_color(color)
        self.update_group_dropdown()

    def change_group(self) -> None:
        """Change the group of the selected rectangles to the current group."""
        new_group_name = self.group_var.get()
        if not new_group_name:
            simpledialog.messagebox.showerror("Error", "No group is selected.")
            return

        new_group = self.groups[new_group_name]
        for rect in self.selected_rectangles:
            current_group = self.groups[rect.group]
            current_group.remove(rect)
            new_group.append(rect)
            rect.set_group(new_group_name)
            self.update_label(rect)
