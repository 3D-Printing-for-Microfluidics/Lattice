"""UI for 3D Print Dose Customization."""

import json
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, simpledialog

from rectangle import Rectangle


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
        self.create_ui()
        self.rectangles = []
        self.selected_rectangles = []
        self.groups = {}
        self.colors = {}

    def create_ui(self) -> None:
        """Create the base UI."""
        self.button_bar = tk.Frame(self.root)
        self.button_bar.pack(side=tk.TOP, fill=tk.X)
        self.create_buttons()

        self.dimensions_label = tk.Label(self.root, text="", bg="lightgray")
        self.dimensions_label.pack(side=tk.TOP, fill=tk.X)

        self.canvas = tk.Canvas(self.root, width=400, height=400, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def create_buttons(self) -> None:
        """Add buttons and group controls to UI."""
        buttons = [
            ("Load", self.load_rectangles),
            ("Save", self.save_rectangles),
            ("Add Rectangle", self.add_rectangle),
            ("Delete Rectangle(s)", self.delete_rectangle),
            ("New Group", self.new_group),
            ("Rename Group", self.rename_group),
            ("Change Group Color", self.set_group_color),
            ("Change Selected to Current Group", self.change_group),
        ]

        # Add group dropdown menu
        self.group_var = tk.StringVar()
        tk.Label(self.button_bar, text="Current Group:").pack(side=tk.LEFT, padx=1, pady=0)
        self.group_dropdown = tk.OptionMenu(self.button_bar, self.group_var, "")
        self.group_dropdown.pack(side=tk.LEFT, padx=1, pady=0)

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

        # Deselect all other rectangles
        for rect in self.selected_rectangles:
            rect.selected = False
            self.canvas.itemconfig(rect.rect, outline="", width=0)
        self.selected_rectangles.clear()

        # Create a new rectangle and select it
        x, y, width, height = 50, 50, 100, 100
        rectangle = Rectangle(self, x, y, width, height, group)
        rectangle.set_color(self.colors[group])
        rectangle.selected = True
        self.canvas.itemconfig(rectangle.rect, outline="red", width=3)
        self.rectangles.append(rectangle)
        self.selected_rectangles.append(rectangle)

        # Update label with dimensions and coordinates of the new rectangle
        self.update_label(rectangle)

    def delete_rectangle(self) -> None:
        """Delete the selected rectangles from the canvas."""
        for rect in self.selected_rectangles:
            rect.delete()
            self.rectangles.remove(rect)
        self.selected_rectangles.clear()

    def save_rectangles(self) -> None:
        """Save the rectangles to a JSON file."""
        data = [
            {"x": rect.x, "y": rect.y, "width": rect.width, "height": rect.height, "group": rect.group}
            for rect in self.rectangles
        ]

        # Prompt the user for a filename with a default name
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile="rectangles.json",
            filetypes=[("JSON files", "*.json")],
        )
        with Path(filename).open("w") as f:
            json.dump({"rectangles": data, "colors": self.colors}, f)

    def load_rectangles(self) -> None:
        """Load rectangles from a JSON file."""
        filename = filedialog.askopenfilename(
            defaultextension=".json",
            initialfile="rectangles.json",
            filetypes=[("JSON files", "*.json")],
        )

        try:
            with Path(filename).open() as f:
                data = json.load(f)
        except FileNotFoundError:
            simpledialog.messagebox.showerror("Error", "File not found.")
        except json.JSONDecodeError:
            simpledialog.messagebox.showerror("Error", "Invalid JSON file.")

        for rect_data in data["rectangles"]:
            rectangle = Rectangle(
                self,
                rect_data["x"],
                rect_data["y"],
                rect_data["width"],
                rect_data["height"],
                rect_data.get("group"),
            )
            if rect_data.get("group"):
                rectangle.set_color(self.colors[rect_data["group"]])
            self.rectangles.append(rectangle)
        self.colors = data.get("colors", {})
        self.update_group_dropdown()

    def update_label(self, rect: Rectangle) -> None:
        """Update the label with the dimensions and coordinates of the rectangle.

        Parameters
        ----------
        rect : Rectangle
            The rectangle whose information is to be displayed.

        """
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

        new_group_name = simpledialog.askstring("Rename Group", f"Enter a new name for '{current_group}':")
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

    def change_group(self) -> None:
        """Change the group of the selected rectangles to the current group."""
        group = self.group_var.get()

        if not group:
            simpledialog.messagebox.showerror("Error", "No group is selected.")
            return

        for rect in self.selected_rectangles:
            rect.set_group(group)
            self.update_label(rect)

    def update_group_dropdown(self) -> None:
        """Update the group dropdown menu."""
        menu = self.group_dropdown["menu"]
        menu.delete(0, "end")
        for group in self.groups:
            menu.add_command(label=group, command=lambda g=group: self.group_var.set(g))
        if self.groups:
            self.group_var.set(list(self.groups.keys())[-1])
