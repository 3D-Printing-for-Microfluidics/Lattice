"""App methods in the Group menu."""

import tkinter as tk
from tkinter import colorchooser, messagebox, simpledialog
from typing import TYPE_CHECKING

from src.menus.menu import Menu

if TYPE_CHECKING:
    from src.app import App


class GroupMenu(Menu):
    """Create and handle the Group menu and its actions.

    Attributes
    ----------
    app : App
        The parent application instance.
    current_group : tk.StringVar
        The current group selected in the menu.

    """

    def __init__(self, app: "App", menubar: tk.Menu) -> None:
        """Initialize the GroupMenu class.

        Parameters
        ----------
        app : App
            The application instance.
        menubar : tk.Menu
            The Tkinter menubar to which the Group menu is added.

        """
        super().__init__(app, menubar)
        self.current_group = tk.StringVar()

    def _create_menu(self, menubar: tk.Menu) -> None:
        """Create the group menu items."""
        menubar.add_cascade(label="Group", menu=self.menu)
        self.build_menu()

    def _bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts."""
        self.app.root.bind_all("<Control-g>", lambda _: self.new_group())
        self.app.root.bind_all("<Control-c>", lambda _: self.change_group())

    def _validate_group_name(self, name: str) -> bool:
        """Validate that a group name is a positive float and not a duplicate.

        Parameters
        ----------
        name : str
            The group name to validate.

        Returns
        -------
        bool
            True if name is valid, False otherwise.

        """
        try:
            value = float(name)
        except ValueError:
            messagebox.showerror("Invalid Group Name", "Group name must be a valid number.")
            return False
        if value <= 0:
            messagebox.showerror("Invalid Group Name", "Group name must be a positive number.")
            return False
        if name in self.app.groups:
            messagebox.showerror("Error", "A group with this name already exists.")
            return False
        return True

    def _check_group_selected(self) -> str | None:
        """Check if a group is selected and show error if not.

        Returns
        -------
        str | None
            The selected group name, or None if no group selected.

        """
        group = self.current_group.get()
        if not group:
            messagebox.showerror("Error", "No group is selected.")
            return None
        return group

    @staticmethod
    def _prompt_group_name(title: str) -> str:
        """Prompt the user for a new group name.

        Parameters
        ----------
        title: str
            The title of the popup window.

        Returns
        -------
        str
            The name entered by the user.

        """
        msg = "Enter a name for the group. This will be the exposure scale:"
        return simpledialog.askstring(title, msg)

    def build_menu(self) -> None:
        """Rebuild the group menu items, showing updated group/color entries."""
        self.menu.delete(0, "end")
        self.menu.add_command(label="New Group", command=self.new_group, accelerator="Ctrl+G")
        self.menu.add_command(label="Delete Group", command=self.delete_group)
        self.menu.add_separator()
        self.menu.add_command(label="- Groups -", state=tk.DISABLED)
        self.app.color_boxes.clear()
        for group in self.app.groups:
            color = self.app.colors[group]
            label = f"  {group}"
            color_box = self.create_color_box(color)
            self.app.color_boxes[group] = color_box
            self.menu.add_radiobutton(
                label=label,
                variable=self.current_group,
                value=group,
                indicatoron=1,
                compound=tk.LEFT,
                image=color_box,
            )
        self.menu.add_command(label="Rename Group", command=self.rename_group)
        self.menu.add_command(label="Change Group Color", command=self.set_group_color)
        self.menu.add_command(
            label="Change Selection to Current Group",
            command=self.change_group,
            accelerator="Ctrl+C",
        )
        if self.app.groups:
            self.current_group.set(list(self.app.groups.keys())[-1])

    def new_group(self) -> None:
        """Create a new group."""
        group_name = self._prompt_group_name("New Group")
        if not group_name:
            return
        if not self._validate_group_name(group_name):
            return
        prev_group = self.current_group.get()
        self.current_group.set(group_name)
        self.set_group_color()
        if group_name not in self.app.colors:
            self.current_group.set(prev_group)
            simpledialog.messagebox.showerror("Error", "Please select a color for the new group.")
            return
        self.app.groups[group_name] = []
        self.build_menu()

    def delete_group(self) -> None:
        """Delete the currently selected group and its components."""
        group = self.current_group.get()
        if not group:
            simpledialog.messagebox.showerror("Error", "No group is selected.")
            return

        del_msg = f"Are you sure you want to delete the group '{group}'?"
        del_msg += "\nThe group and all components in this group will be deleted."
        if simpledialog.messagebox.askyesno("Delete Group", del_msg):
            for comp in self.app.groups[group]:
                comp.delete()
            del self.app.groups[group]
            del self.app.colors[group]
            self.build_menu()
            self.app.deselect_all()
            self.build_menu()

    def rename_group(self) -> None:
        """Rename the currently selected group."""
        old_name = self._check_group_selected()
        if not old_name:
            return

        new_name = self._prompt_group_name("Rename Group")
        if not new_name or new_name == old_name:
            return

        if not self._validate_group_name(new_name):
            return

        self.app.groups[new_name] = self.app.groups.pop(old_name)
        self.app.colors[new_name] = self.app.colors.pop(old_name)
        for comp in self.app.groups[new_name]:
            comp.group = new_name
        self.build_menu()
        self.current_group.set(new_name)
        self.app.update_label(self.app.selection[0])

    def set_group_color(self) -> None:
        """Set the color of the current group."""
        group = self._check_group_selected()
        if not group:
            return
        color = colorchooser.askcolor()[1]
        if not color:
            return
        self.app.colors[group] = color
        for comp in self.app.groups.get(group, []):
            comp.set_color(color)
        self.build_menu()

    def change_group(self) -> None:
        """Change the group of the selected components to the current group."""
        new_group = self._check_group_selected()
        if not new_group:
            return

        for comp in self.app.selection:
            self.app.groups[comp.group].remove(comp)
            comp.set_group(new_group)
            self.app.groups[new_group].append(comp)
        self.app.update_label(self.app.selection[0])

    @staticmethod
    def create_color_box(color: str) -> tk.PhotoImage:
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
