"""App methods in the File menu."""

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, simpledialog
from typing import TYPE_CHECKING

from component import Component

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
        file_menu.add_command(label="Open", command=self.load_json, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_json, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.app.root.quit)

        # Bind shortcuts here
        self.app.root.bind_all("<Control-o>", lambda _: self.load_json())
        self.app.root.bind_all("<Control-s>", lambda _: self.save_json())

    def save_json(self) -> None:
        """Save the components and colors to a JSON file."""
        data = {}
        data["groups"] = {}
        data["colors"] = self.app.colors

        for group_name, objs in self.app.groups.items():
            data["groups"][group_name] = []
            for comp in objs:
                comp_dict = comp.to_dict()
                comp_dict.pop("group", None)
                data["groups"][group_name].append(comp_dict)

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile="components.json",
            filetypes=[("JSON files", "*.json")],
        )
        if filename:
            with Path(filename).open("w") as f:
                json.dump(data, f, indent=4)

    def load_json(self) -> None:
        """Load components and colors from a JSON file."""
        filename = filedialog.askopenfilename(
            defaultextension=".json",
            initialfile="components.json",
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
