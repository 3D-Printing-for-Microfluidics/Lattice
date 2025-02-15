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

    def check_component_overlap(self) -> tuple[bool, str]:
        """Check if any components overlap.

        Returns
        -------
        tuple[bool, str]
            A tuple containing:
            - bool: True if there is overlap, False otherwise
            - str: Description of overlapping components if any, empty string otherwise

        """
        overlapping_components = set()

        # Get all components in a flat list
        all_components = [comp for group in self.app.groups.values() for comp in group]

        # Start with each component
        for i, c1 in enumerate(all_components):
            c1_left = c1.x
            c1_right = c1_left + c1.width
            c1_top = c1.y
            c1_bottom = c1_top + c1.height

            # Check against all remaining components (only check forward to avoid duplicate comparisons)
            for c2 in all_components[i + 1 :]:
                c2_left = c2.x
                c2_right = c2_left + c2.width
                c2_top = c2.y
                c2_bottom = c2_top + c2.height

                # For top-down coordinates (y increases downward):
                if c1_left < c2_right and c1_right > c2_left and c1_top < c2_bottom and c1_bottom > c2_top:
                    overlapping_components.add(c1)
                    overlapping_components.add(c2)

        if overlapping_components:
            self.app.deselect_all()
            for component in overlapping_components:
                component.select()

            msg = f"Error: {len(overlapping_components)} components overlap"
            return True, msg

        return False, ""

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

        has_overlap, overlap_msg = self.check_component_overlap()
        if has_overlap:
            messagebox.showerror("Error", f"Cannot generate print file.\n\n{overlap_msg}")
            return

        # Create mode selection dialog
        mode_dialog = tk.Toplevel(self.app.root)
        mode_dialog.title("Generation Mode")
        mode_dialog.geometry("300x150")
        mode_dialog.transient(self.app.root)
        mode_dialog.grab_set()

        # Center the dialog
        mode_dialog.geometry(
            "+%d+%d"
            % (
                self.app.root.winfo_rootx() + self.app.root.winfo_width() // 3,
                self.app.root.winfo_rooty() + self.app.root.winfo_height() // 3,
            ),
        )

        selected_mode = tk.StringVar(value="absolute")  # Default to absolute mode

        tk.Label(mode_dialog, text="Choose generation mode:", pady=10).pack()
        tk.Radiobutton(mode_dialog, text="Absolute", variable=selected_mode, value="absolute").pack(padx=20, anchor="w")
        tk.Radiobutton(mode_dialog, text="Scaling", variable=selected_mode, value="scaling").pack(padx=20, anchor="w")
        result = {"mode": None}

        def on_ok() -> None:
            result["mode"] = selected_mode.get()
            mode_dialog.destroy()

        def on_cancel() -> None:
            mode_dialog.destroy()

        tk.Button(mode_dialog, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=20, pady=20)
        tk.Button(mode_dialog, text="Cancel", command=on_cancel, width=10).pack(side=tk.RIGHT, padx=20, pady=20)

        mode_dialog.wait_window()  # Wait for dialog to close

        if result["mode"] is None:  # User clicked cancel
            return

        is_absolute = result["mode"] == "absolute"

        # Validate group names based on selected mode
        for group_name in self.app.groups:
            try:
                value = float(group_name)
                if value <= 0:
                    messagebox.showerror("Invalid Group Name", f"Group name '{group_name}' must be a positive number.")
                    return
            except ValueError:
                messagebox.showerror("Invalid Group Name", f"Group name '{group_name}' must be a valid number.")
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
            new_print_file(Path(self.app.component_file), Path(output_path), data, is_absolute=is_absolute)
            messagebox.showinfo("Success", f"Print file saved to:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
