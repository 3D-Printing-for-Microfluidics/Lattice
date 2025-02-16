"""App methods in the File menu."""

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from component import Component
from gen_print_file import new_print_file
from image_ops import get_component_dimensions
from menus.menu import Menu
from popup import Popup


class FileMenu(Menu):
    """Create and handle the File menu and its actions."""

    def _create_menu(self, menubar: tk.Menu) -> None:
        """Create the file menu items.

        Parameters
        ----------
        menubar: tk.Menu
            The menubar to attach to.

        """
        menubar.add_cascade(label="File", menu=self.menu)
        self.menu.add_command(label="Load component", command=self.load_component, accelerator="Ctrl+C")
        self.menu.add_command(label="Open Layout", command=self.load_json, accelerator="Ctrl+O")
        self.menu.add_command(label="Save Layout", command=self.save_json, accelerator="Ctrl+S")
        self.menu.add_separator()
        self.menu.add_command(label="Generate print file", command=self.generate_print_file)
        self.menu.add_separator()
        self.menu.add_command(label="Exit", command=self.app.root.quit)

    def _bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts."""
        self.app.root.bind_all("<Control-c>", lambda _: self.load_component())
        self.app.root.bind_all("<Control-o>", lambda _: self.load_json())
        self.app.root.bind_all("<Control-s>", lambda _: self.save_json())

    def load_component(self) -> None:
        """Prompt user to select a component zip and store its dimensions."""
        file_path = filedialog.askopenfilename(title="Select component zip file", filetypes=[("Zip", "*.zip")])
        if not file_path:
            return
        try:
            width, height = get_component_dimensions(file_path)
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load component: {exc}")
        self.app.comp_width = width
        self.app.comp_height = height
        self.app.component_file = file_path
        self.app.redraw_canvas()
        messagebox.showinfo("Component loaded", f"Width={width}, Height={height}")

    def get_layout_data(self) -> dict:
        """Return groups, positions, and colors as a dictionary.

        Returns
        -------
        dict
            Contains colors and a flat list of components with their groups and positions.

        """
        return {
            "colors": self.app.colors,
            "components": [
                {
                    "group": comp.group,
                    "x": comp.x,
                    "y": comp.y,
                }
                for group in self.app.groups.values()
                for comp in group
            ],
        }

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
        """Load layout from a JSON file."""
        if self.app.comp_width is None or self.app.comp_height is None:
            messagebox.showwarning("No component loaded", "Please load a component first.")
            return

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
        except (FileNotFoundError, json.JSONDecodeError) as e:
            messagebox.showerror("Error", str(e))
            return

        self.app.clear_canvas()
        self.app.colors = data.get("colors", {})
        self.app.groups = {group: [] for group in self.app.colors}

        for comp_data in data.get("components", []):
            group = comp_data["group"]
            component = Component(self.app, x=comp_data["x"], y=comp_data["y"], group=group)
            component.set_color(self.app.colors[group])
            self.app.groups[group].append(component)

        self.app.group_menu.build_menu()

    def check_component_overlap(self) -> set[Component]:
        """Check if any components overlap.

        Returns
        -------
        set[Component]
            A set of all overlapping components, or empty set if no components overlap.

        """
        overlapping_components = set()

        # Get all components in a flat list
        all_components = [comp for group in self.app.groups.values() for comp in group]

        # Start with each component
        for i, c1 in enumerate(all_components):
            c1_left = c1.x
            c1_right = c1_left + self.app.comp_width
            c1_top = c1.y
            c1_bottom = c1_top + self.app.comp_height

            # Check against all remaining components (only check forward to avoid duplicate comparisons)
            for c2 in all_components[i + 1 :]:
                c2_left = c2.x
                c2_right = c2_left + self.app.comp_width
                c2_top = c2.y
                c2_bottom = c2_top + self.app.comp_height

                # For top-down coordinates (y increases downward in image coordinates):
                if c1_left < c2_right and c1_right > c2_left and c1_top < c2_bottom and c1_bottom > c2_top:
                    overlapping_components.add(c1)
                    overlapping_components.add(c2)

        return overlapping_components

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

        # Check for overlapping components
        overlapping_components = self.check_component_overlap()
        if overlapping_components:
            self.app.deselect_all()
            for component in overlapping_components:
                component.select()

            msg = f"Cannot generate print file.\n\n{len(overlapping_components)} components overlap."
            messagebox.showerror("Error", msg)
            return

        output_path = filedialog.asksaveasfilename(
            title="Save print file",
            defaultextension=".zip",
            filetypes=[("Zip", "*.zip"), ("All files", "*.*")],
        )
        if not output_path:
            return

        popup = Popup(self.app.root, message="Generating print file...")
        try:
            data = self.get_layout_data().get("components", [])
            new_print_file(Path(self.app.component_file), Path(output_path), data)
            messagebox.showinfo("Success", f"Print file saved to:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            popup.destroy()
