"""UI for 3D Print Dose Customization."""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, simpledialog


class Rectangle:
    """A class used to represent a Rectangle on the Tkinter Canvas.

    Attributes
    ----------
    canvas : tk.Canvas
        The canvas on which the rectangle is drawn.
    app : RectangleApp
        Reference to the RectangleApp instance.
    rect : int
        The ID of the rectangle on the canvas.
    x : int
        The x-coordinate of the rectangle.
    y : int
        The y-coordinate of the rectangle.
    width : int
        The width of the rectangle.
    height : int
        The height of the rectangle.
    start_x : int | None
        The starting x-coordinate for dragging.
    start_y : int | None
        The starting y-coordinate for dragging.
    selected : bool
        Whether the rectangle is selected.
    group : str | None
        The group to which the rectangle belongs.

    """

    def __init__(
        self,
        app: RectangleApp,
        x: int,
        y: int,
        width: int,
        height: int,
        group: str | None = None,
    ) -> None:
        """Initialize a rectangle.

        Parameters
        ----------
        canvas : tk.Canvas
            The canvas on which the rectangle is drawn.
        x : int
            The x-coordinate of the rectangle.
        y : int
            The y-coordinate of the rectangle.
        width : int
            The width of the rectangle.
        height : int
            The height of the rectangle.
        app : RectangleApp
            Reference to the RectangleApp instance.
        group : str | None
            The group to which the rectangle belongs (default is None).

        """
        self.app = app
        self.canvas = app.canvas
        self.rect = self.canvas.create_rectangle(x, y, x + width, y + height, fill="blue", tags="rect")
        self.canvas.tag_bind(self.rect, "<Button-1>", self.on_click)
        self.canvas.tag_bind(self.rect, "<B1-Motion>", self.on_drag)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.start_x = None
        self.start_y = None
        self.selected = False
        self.group = group

    def on_click(self, event: tk.Event) -> None:
        """Handle the click event on the rectangle.

        Parameters
        ----------
        event : tk.Event
            The event object containing information about the click event.

        """
        if not self.canvas.find_withtag("current"):
            return

        if event.state & 0x0001:  # Shift key is held
            if self.selected:
                self.selected = False
                self.canvas.itemconfig(self.rect, outline="", width=1)
                self.app.selected_rectangles.remove(self)
            else:
                self.selected = True
                self.canvas.itemconfig(self.rect, outline="red", width=3)
                self.app.selected_rectangles.append(self)
        else:
            # Deselect all other rectangles
            for rect in self.app.selected_rectangles:
                rect.selected = False
                self.canvas.itemconfig(rect.rect, outline="", width=1)
            self.app.selected_rectangles.clear()

            # Select the clicked rectangle
            self.selected = True
            self.canvas.itemconfig(self.rect, outline="red", width=3)
            self.app.selected_rectangles.append(self)

        # Update label with dimensions, coordinates, and group of the last clicked rectangle
        self.app.update_label(self)

        # Set start coordinates for dragging
        self.start_x = event.x
        self.start_y = event.y

    def on_drag(self, event: tk.Event) -> None:
        """Handle the drag event on the rectangle.

        Parameters
        ----------
        event : tk.Event
            The event object containing information about the drag event.

        """
        if self.start_x is not None and self.start_y is not None:
            dx = event.x - self.start_x
            dy = event.y - self.start_y
            for rect in self.app.selected_rectangles:
                self.canvas.move(rect.rect, dx, dy)
                rect.x += dx
                rect.y += dy
            self.start_x = event.x
            self.start_y = event.y
            self.app.update_label(self)

    def delete(self) -> None:
        """Delete the rectangle from the canvas."""
        self.canvas.delete(self.rect)

    def set_color(self, color: str) -> None:
        """Set the color of the rectangle.

        Parameters
        ----------
        color : str
            The color to set for the rectangle.

        """
        self.canvas.itemconfig(self.rect, fill=color)

    def set_group(self, group: str) -> None:
        """Set the group of the rectangle and update its color.

        Parameters
        ----------
        group : str
            The group to set for the rectangle.

        """
        self.group = group
        color = self.app.colors.get(group, "blue")
        self.set_color(color)


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


def main() -> None:
    """Run the Tkinter application."""
    root = tk.Tk()
    RectangleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
