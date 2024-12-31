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

        self.button_bar = tk.Frame(self.root)
        self.button_bar.pack(side=tk.TOP, fill=tk.X)
        self.create_buttons()

        self.dimensions_label = tk.Label(self.root, text="", bg="lightgray")
        self.dimensions_label.pack(side=tk.TOP, fill=tk.X)

        self.canvas = tk.Canvas(self.root, width=2000, height=1000, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind a left click event to the canvas
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def on_canvas_click(self, event: tk.Event) -> None:
        """Handle the click event on the canvas.

        Parameters
        ----------
        event : tk.Event
            The event object containing information about the click event.

        """
        logger.debug("Click at (%d, %d)", event.x, event.y)

        # If no rectangle was clicked
        if not self.canvas.find_withtag("current"):
            self.deselect_all()
            self.update_label(None)

    def create_menu_bar(self) -> None:
        """Create the menu bar."""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load", command=self.load_json)
        file_menu.add_command(label="Save", command=self.save_json)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        self.group_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Group", menu=self.group_menu)

        self.group_var = tk.StringVar()
        self.update_group_dropdown()

    def update_group_dropdown(self) -> None:
        """Update the group dropdown menu."""
        self.group_menu.delete(0, "end")

        self.group_menu.add_command(label="New Group", command=self.new_group)
        self.group_menu.add_separator()

        self.color_boxes.clear()
        self.group_menu.add_command(label="- Groups -", state=tk.DISABLED)
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

    def create_buttons(self) -> None:
        """Add buttons to UI."""
        buttons = [
            ("Add Rectangle", self.add_rectangle),
            ("Delete Rectangle(s)", self.delete_rectangle),
        ]

        # Add buttons
        for text, command in buttons:
            button = tk.Button(self.button_bar, text=text, command=command)
            button.pack(side=tk.LEFT, padx=1, pady=0)

    def add_rectangle(self) -> None:
        """Add a new rectangle to the canvas."""
        group = self.group_var.get()
        if not group:
            simpledialog.messagebox.showerror("Error", "No group is selected. Create or select a group to begin.")
            return

        # Create a new rectangle and select it
        x, y, width, height = 50, 50, 100, 100
        rectangle = Rectangle(self, x, y, width, height, group)
        rectangle.set_color(self.colors[group])
        self.rectangles.append(rectangle)
        self.deselect_all()
        rectangle.select()

        # Update label with dimensions and coordinates of the new rectangle
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

    def save_json(self) -> None:
        """Save the rectangles and colors to a JSON file."""
        data = {
            "rectangles": [
                {"x": rect.x, "y": rect.y, "width": rect.width, "height": rect.height, "group": rect.group}
                for rect in self.rectangles
            ],
            "colors": self.colors,
        }

        # Prompt the user for a filename with a default name
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
                self.groups[rect_data["group"]].append(rectangle)  # Add rectangle to group
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

            # Update rectangles belonging to the renamed group
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
