"""App methods in the Group menu."""

import tkinter as tk
from tkinter import colorchooser, simpledialog
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app import App


class GroupMenu:
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
        self.app = app
        self.current_group = tk.StringVar()

        self.menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Group", menu=self.menu)
        self.menu.add_command(label="New Group", command=self.new_group, accelerator="Ctrl+G")
        self.menu.add_command(label="Delete Group", command=self.delete_group)
        self.menu.add_separator()
        self.menu.add_command(label="- Groups -", state=tk.DISABLED)
        # ...existing logic for populating groups can be placed here...
        self.menu.add_command(label="Rename Group", command=self.rename_group)
        self.menu.add_command(label="Change Group Color", command=self.set_group_color)
        self.menu.add_command(label="Change Selection to Current Group", command=self.change_group)

        # Bind shortcuts here
        self.app.root.bind_all("<Control-g>", lambda _: self.new_group())

    def update_dropdown(self) -> None:
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
        self.menu.add_command(label="Change Selection to Current Group", command=self.change_group)
        if self.app.groups:
            self.current_group.set(list(self.app.groups.keys())[-1])

    def new_group(self) -> None:
        """Create a new group."""
        group_name = simpledialog.askstring("Group Name", "Enter a name for the new group:")
        if not group_name:
            simpledialog.messagebox.showerror("Error", "Please enter a name for the group.")
            return
        if group_name in self.app.groups:
            simpledialog.messagebox.showerror("Error", "Group already exists.")
            return
        prev_group = self.current_group.get()
        self.current_group.set(group_name)
        self.set_group_color()
        if group_name not in self.app.colors:
            self.current_group.set(prev_group)
            simpledialog.messagebox.showerror("Error", "Please select a color for the new group.")
            return
        self.app.groups[group_name] = []
        self.update_dropdown()
        self.update_dropdown()

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
            self.update_dropdown()
            self.app.deselect_all()
            self.update_dropdown()

    def rename_group(self) -> None:
        """Rename the current group."""
        current_group = self.current_group.get()
        if not current_group:
            simpledialog.messagebox.showerror("Error", "No group is selected.")
            return
        new = simpledialog.askstring("Rename Group", f"Enter a new name for Group '{current_group}':")
        if new and new != current_group:
            self.app.groups[new] = self.app.groups.pop(current_group, [])
            self.app.colors[new] = self.app.colors.pop(current_group, "blue")
            self.update_dropdown()
            for comp in self.app.groups[new]:
                comp.set_group(new)
            self.app.update_label(None)
            self.update_dropdown()

    def set_group_color(self) -> None:
        """Set the color of the current group."""
        group = self.current_group.get()
        if not group:
            simpledialog.messagebox.showerror("Error", "No group is selected.")
            return
        color = colorchooser.askcolor()[1]
        if color:
            self.app.colors[group] = color
            for comp in self.app.groups.get(group, []):
                comp.set_color(color)
        self.update_dropdown()
        self.update_dropdown()

    def change_group(self) -> None:
        """Change the group of the selected components to the current group."""
        new_group = self.current_group.get()
        if not new_group:
            simpledialog.messagebox.showerror("Error", "No group is selected.")
            return

        for comp in self.app.selection:
            self.app.groups[comp.group].remove(comp)
            comp.set_group(new_group)
            self.app.groups[new_group].append(comp)
        self.app.update_label(self.app.selection[0])
        # no need to rebuild the entire menu here

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
