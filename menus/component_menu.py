"""App methods in the Object menu."""

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from typing import TYPE_CHECKING

from component import Component
from image_ops import load_component_dimensions

if TYPE_CHECKING:
    from app import App


class TileDialog:
    """A dialog to get tile parameters from the user."""

    def __init__(self, parent: tk.Tk) -> None:
        """Initialize the TileDialog.

        Parameters
        ----------
        parent : tk.Tk
            The parent window of the dialog.

        """
        self.top = tk.Toplevel(parent)
        self.top.title("Tile Rectangles")

        tk.Label(self.top, text="X Start:").grid(row=0, column=0)
        self.x_start = tk.Entry(self.top)
        self.x_start.grid(row=0, column=1)

        tk.Label(self.top, text="Y Start:").grid(row=1, column=0)
        self.y_start = tk.Entry(self.top)
        self.y_start.grid(row=1, column=1)

        tk.Label(self.top, text="X Spacing:").grid(row=2, column=0)
        self.x_spacing = tk.Entry(self.top)
        self.x_spacing.grid(row=2, column=1)

        tk.Label(self.top, text="Y Spacing:").grid(row=3, column=0)
        self.y_spacing = tk.Entry(self.top)
        self.y_spacing.grid(row=3, column=1)

        tk.Label(self.top, text="Number of X:").grid(row=4, column=0)
        self.num_x = tk.Entry(self.top)
        self.num_x.grid(row=4, column=1)

        tk.Label(self.top, text="Number of Y:").grid(row=5, column=0)
        self.num_y = tk.Entry(self.top)
        self.num_y.grid(row=5, column=1)

        tk.Button(self.top, text="OK", command=self.ok).grid(row=6, column=0)
        tk.Button(self.top, text="Cancel", command=self.cancel).grid(row=6, column=1)

        self.result = None

    def ok(self) -> None:
        """Handle the OK button click."""
        try:
            x_start = int(self.x_start.get())
            y_start = int(self.y_start.get())
            x_spacing = int(self.x_spacing.get())
            y_spacing = int(self.y_spacing.get())
            num_x = int(self.num_x.get())
            num_y = int(self.num_y.get())
            self.result = (x_start, y_start, x_spacing, y_spacing, num_x, num_y)
        except ValueError:
            messagebox.showerror("Error", "Please enter valid integers.")
            return
        self.top.destroy()

    def cancel(self) -> None:
        """Handle the Cancel button click."""
        self.top.destroy()


class ComponentMenu:
    """Create and handle the Component (Object) menu and its actions.

    Attributes
    ----------
    app : App
        The parent application instance.

    """

    def __init__(self, app: "App", menubar: tk.Menu) -> None:
        """Initialize the ComponentMenu class.

        Parameters
        ----------
        app : App
            The application instance.
        menubar : tk.Menu
            The Tkinter menubar to which the Component menu is added.

        """
        self.app = app
        menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Component", menu=menu)

        menu.add_command(label="Load component", command=self.load_component)
        menu.add_command(label="Component cutout tool", command=self.run_cutout_tool)
        menu.add_separator()
        menu.add_command(label="Add", command=self.add_component, accelerator="Insert")
        menu.add_command(label="Delete", command=self.delete_component, accelerator="Delete")
        menu.add_separator()
        menu.add_command(label="Tile create", command=self.tile)

        # Bind shortcuts here
        self.app.root.bind_all("<Insert>", lambda _: self.add_component())
        self.app.root.bind_all("<Delete>", lambda _: self.delete_component())

    def load_component(self) -> None:
        """Prompt user to select a component zip and store its dimensions."""
        file_path = filedialog.askopenfilename(title="Select component zip file", filetypes=[("Zip", "*.zip")])
        if not file_path:
            return
        try:
            width, height = load_component_dimensions(file_path)
            self.app.comp_width = width
            self.app.comp_height = height
            self.app.component_file = file_path
            messagebox.showinfo("Component loaded", f"Width={width}, Height={height}")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load component: {exc}")

    def add_component(self) -> None:
        """Add a new component to the canvas."""
        if self.app.comp_width is None or self.app.comp_height is None:
            messagebox.showwarning("No component laded", "Please load a component first.")
            return
        group = self.app.group_menu.current_group.get()
        if not group:
            simpledialog.messagebox.showerror("Error", "No group is selected. Create or select a group to begin.")
            return
        x, y = 50, 50
        comp = Component(self.app, x, y, self.app.comp_width, self.app.comp_height, group)
        comp.set_color(self.app.colors[group])
        self.app.groups[group].append(comp)
        self.app.deselect_all()
        comp.select()
        self.app.update_label(comp)

    def delete_component(self) -> None:
        """Delete the selected components from the canvas."""
        for comp in self.app.selection:
            self.app.groups[comp.group].remove(comp)
            comp.delete()
        self.app.selection.clear()

    def tile(self) -> None:
        """Tile components based on user input."""
        group = self.app.group_menu.current_group.get()
        if not group:
            simpledialog.messagebox.showerror("Error", "No group is selected. Create or select a group to begin.")
            return

        dialog = TileDialog(self.app.root)
        self.app.root.wait_window(dialog.top)
        if dialog.result:
            x_start, y_start, x_spacing, y_spacing, num_x, num_y = dialog.result
            for i in range(num_x):
                for j in range(num_y):
                    x = x_start + i * x_spacing
                    y = y_start + j * y_spacing
                    comp = Component(self.app, x, y, self.app.comp_width, self.app.comp_height, group)
                    comp.set_color(self.app.colors[group])
                    self.app.groups[group].append(comp)
            self.app.update_label(self.app.groups[group][-1])

    def run_cutout_tool(self) -> None:
        """Launch the component cutout tool."""
        import component_selector

        component_selector.ComponentSelector(parent=self.app.root)
