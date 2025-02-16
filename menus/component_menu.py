"""App methods in the Object menu."""

import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import TYPE_CHECKING

from component import Component
from tile_dialog import TileDialog

if TYPE_CHECKING:
    from app import App


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
        menu.add_command(label="Add", command=self.add_component, accelerator="Insert")
        menu.add_command(label="Delete", command=self.delete_component, accelerator="Delete")
        menu.add_separator()
        menu.add_command(label="Tile create", command=self.tile)
        menu.add_separator()
        menu.add_command(label="Component cutout tool", command=self.run_cutout_tool)

        # Bind shortcuts here
        self.app.root.bind_all("<Insert>", lambda _: self.add_component())
        self.app.root.bind_all("<Delete>", lambda _: self.delete_component())

    def _check_can_create_component(self) -> str | None:
        """Check if components can be created.

        Returns
        -------
        str | None
            The group name if checks pass, None otherwise.
        """
        if self.app.comp_width is None or self.app.comp_height is None:
            messagebox.showwarning("No component loaded", "Please load a component first.")
            return None

        group = self.app.group_menu.current_group.get()
        if not group:
            simpledialog.messagebox.showerror("Error", "No group is selected. Create or select a group to begin.")
            return None

        return group

    def add_component(self) -> None:
        """Add a new component to the canvas."""
        group = self._check_can_create_component()
        if not group:
            return
        x, y = 50, 50
        comp = Component(self.app, x, y, group)
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
        group = self._check_can_create_component()
        if not group:
            return

        dialog = TileDialog(self.app.root)
        self.app.root.wait_window(dialog.top)
        if dialog.result:
            x_start, y_start, x_spacing, y_spacing, num_x, num_y = dialog.result
            for i in range(num_x):
                for j in range(num_y):
                    x = x_start + i * (self.app.comp_width + x_spacing)
                    y = y_start + j * (self.app.comp_height + y_spacing)
                    comp = Component(self.app, x, y, group)
                    comp.set_color(self.app.colors[group])
                    self.app.groups[group].append(comp)
            self.app.update_label(self.app.groups[group][-1])

    def run_cutout_tool(self) -> None:
        """Launch the component cutout tool."""
        import component_selector

        component_selector.ComponentSelector(parent=self.app.root)
