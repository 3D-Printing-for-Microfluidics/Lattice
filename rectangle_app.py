"""UI for 3D Print Dose Customization."""

from __future__ import annotations

import json
import logging
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, simpledialog

from rectangle import Rectangle

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
        menu_bar.add_cascade(label="Rectangle", menu=rectangle_menu)
        rectangle_menu.add_command(label="Add Rectangle", command=self.add_rectangle, accelerator="Ctrl+A")
        rectangle_menu.add_command(label="Delete Rectangle(s)", command=self.delete_rectangle, accelerator="Ctrl+D")

        arrange_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Arrange", menu=arrange_menu)
        arrange_menu.add_command(label="Align Horizontal", command=self.align_horizontal)
        arrange_menu.add_command(label="Align Vertical", command=self.align_vertical)

    def bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts."""
        self.root.bind_all("<Control-a>", lambda event: self.add_rectangle())
        self.root.bind_all("<Control-d>", lambda event: self.delete_rectangle())
        self.root.bind_all("<Control-g>", lambda event: self.new_group())
        self.root.bind_all("<Control-o>", lambda event: self.load_json())
        self.root.bind_all("<Control-s>", lambda event: self.save_json())

    def create_label(self) -> None:
        """Create the dimensions label."""
        self.dimensions_label = tk.Label(self.root, text="", bg="lightgray")
        self.dimensions_label.pack(side=tk.TOP, fill=tk.X)

    def create_canvas(self) -> None:
        """Create the canvas."""
        self.canvas = tk.Canvas(self.root, width=2000, height=1000, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def on_canvas_click(self, event: tk.Event) -> None:
        """Handle the click event on the canvas."""
        logger.debug("Click at (%d, %d)", event.x, event.y)
        if not self.canvas.find_withtag("current"):
            self.deselect_all()
            self.update_label(None)

    def update_group_dropdown(self) -> None:
        """Update the group dropdown menu."""
        self.group_menu.delete(0, "end")
        self.group_menu.add_command(label="New Group", command=self.new_group, accelerator="Ctrl+G")
        self.group_menu.add_separator()
        self.group_menu.add_command(label="- Groups -", state=tk.DISABLED)

        self.color_boxes.clear()
        for group in self.groups:
            color = self.colors.get(group, "blue")
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

    def align_horizontal(self) -> None:
        """Align selected rectangles horizontally."""
        if not self.selected_rectangles:
            return
        min_y = min(rect.y for rect in self.selected_rectangles)
        for rect in self.selected_rectangles:
            rect.set_position(rect.x, min_y)
        self.update_label(self.selected_rectangles[0])

    def align_vertical(self) -> None:
        """Align selected rectangles vertically."""
        if not self.selected_rectangles:
            return
        min_x = min(rect.x for rect in self.selected_rectangles)
        for rect in self.selected_rectangles:
            rect.set_position(min_x, rect.y)
        self.update_label(self.selected_rectangles[0])

    def save_json(self) -> None:
        """Save the rectangles and colors to a JSON file."""
        data = {
            "rectangles": [
                {"x": rect.x, "y": rect.y, "width": rect.width, "height": rect.height, "group": rect.group}
                for rect in self.rectangles
            ],
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
        if not filename:
            simpledialog.messagebox.showerror("Error", "No file selected.")
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
                rect_data.get("group"),
            )
            if rect_data.get("group"):
                rectangle.set_color(self.colors.get(rect_data["group"], "blue"))
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
        self.groups[group_name] = []
        self.group_var.set(group_name)
        self.set_group_color()
        self.update_group_dropdown()

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
                    self.update_label(rect)

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
        group = self.group_var.get()
        if not group:
            simpledialog.messagebox.showerror("Error", "No group is selected.")
            return
        for rect in self.selected_rectangles:
            rect.set_group(group)
            self.update_label(rect)
