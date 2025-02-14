"""App methods in the File menu."""

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
from typing import TYPE_CHECKING

from component import Component
from gen_print_file import new_print_file

if TYPE_CHECKING:
    from app import App


class FileMenu:
    """Create and handle the File menu and its actions.

    Attributes
    ----------
    app : App
        The parent application instance.

    """

    def __init__(self, app: "App", menubar: tk.Menu) -> None:
        """Initialize the FileMenu class.

        Parameters
        ----------
        app : App
            The application instance.
        menubar : tk.Menu
            The Tkinter menubar to which the File menu is added.

        """
        self.app = app
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Layout", command=self.load_json, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Layout", command=self.save_json, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Generate print file", command=self.generate_print_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.app.root.quit)

        # Bind shortcuts here
        self.app.root.bind_all("<Control-o>", lambda _: self.load_json())
        self.app.root.bind_all("<Control-s>", lambda _: self.save_json())

    def get_layout_data(self) -> dict:
        """Return the current groups and colors as a dictionary."""
        data = {}
        data["groups"] = {}
        data["colors"] = self.app.colors
        for group_name, objs in self.app.groups.items():
            data["groups"][group_name] = []
            for comp in objs:
                comp_dict = comp.to_dict()
                comp_dict.pop("group", None)
                data["groups"][group_name].append(comp_dict)
        return data

    def save_json(self) -> None:
        """Save the components and colors to a JSON file."""
        data = self.get_layout_data()
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile="layout.json",
            filetypes=[("JSON files", "*.json")],
        )
        if filename:
            with Path(filename).open("w") as f:
                json.dump(data, f, indent=4)

    def load_json(self) -> None:
        """Load components and colors from a JSON file."""
        filename = filedialog.askopenfilename(
            defaultextension=".json",
            initialfile="layout.json",
            filetypes=[("JSON files", "*.json")],
        )
        if not filename:
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

        self.app.clear_canvas()
        self.app.colors = data.get("colors", {})
        groups = data.get("groups", {})

        for group_name, group in groups.items():
            self.app.groups[group_name] = []
            for comp in group:
                component = Component(self.app, group=group_name, **comp)
                component.set_color(self.app.colors[group_name])
                self.app.groups[group_name].append(component)

        self.app.group_menu.update_dropdown()

    def generate_print_file(self) -> None:
        """Generate a new print file with scaled exposure settings and composite images."""
        # Check if a component has been loaded
        if not self.app.component_file:
            messagebox.showerror("Error", "Please load a component file first.")
            return

        # Check if the canvas is empty
        if not any(self.app.groups.values()):
            messagebox.showerror("Error", "Please add some components to the canvas first.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save print file",
            defaultextension=".zip",
            filetypes=[("Zip", "*.zip"), ("All files", "*.*")],
        )
        if not output_path:
            return

        try:
            data = self.get_layout_data().get("groups", {})
            new_print_file(Path(self.app.component_file), Path(output_path), data)
            messagebox.showinfo("Success", f"Print file saved to:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
