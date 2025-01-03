"""App methods in the Group menu."""

from tkinter import colorchooser, simpledialog
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app import App


def new_group(app: "App") -> None:
    """Create a new group."""
    group_name = simpledialog.askstring("Group Name", "Enter a name for the new group:")
    if not group_name:
        simpledialog.messagebox.showerror("Error", "Please enter a name for the group.")
        return
    if group_name in app.groups:
        simpledialog.messagebox.showerror("Error", "Group already exists.")
        return
    prev_group = app.group_var.get()
    app.group_var.set(group_name)
    app.set_group_color()
    if group_name not in app.colors:
        app.group_var.set(prev_group)
        simpledialog.messagebox.showerror("Error", "Please select a color for the new group.")
        return
    app.groups[group_name] = []
    app.update_group_dropdown()


def delete_group(app: "App") -> None:
    """Delete the currently selected group and its rectangles."""
    group = app.group_var.get()
    if not group:
        simpledialog.messagebox.showerror("Error", "No group is selected.")
        return

    del_msg = f"Are you sure you want to delete the group '{group}'?"
    del_msg += "\nThe group and all rectangles in this group will be deleted."
    if simpledialog.messagebox.askyesno("Delete Group", del_msg):
        for rect in app.groups[group]:
            rect.delete()
        del app.groups[group]
        del app.colors[group]
        app.update_group_dropdown()
        app.deselect_all()


def rename_group(app: "App") -> None:
    """Rename the current group."""
    current_group = app.group_var.get()
    if not current_group:
        simpledialog.messagebox.showerror("Error", "No group is selected.")
        return
    new_group = simpledialog.askstring("Rename Group", f"Enter a new name for Group '{current_group}':")
    if new_group and new_group != current_group:
        app.groups[new_group] = app.groups.pop(current_group, [])
        app.colors[new_group] = app.colors.pop(current_group, "blue")
        app.update_group_dropdown()
        for rect in app.groups[new_group]:
            rect.set_group(new_group)
        app.update_label(None)


def set_group_color(app: "App") -> None:
    """Set the color of the current group."""
    group = app.group_var.get()
    if not group:
        simpledialog.messagebox.showerror("Error", "No group is selected.")
        return
    color = colorchooser.askcolor()[1]
    if color:
        app.colors[group] = color
        for rect in app.groups.get(group, []):
            rect.set_color(color)
    app.update_group_dropdown()


def change_group(app: "App") -> None:
    """Change the group of the selected rectangles to the current group."""
    new_group = app.group_var.get()
    if not new_group:
        simpledialog.messagebox.showerror("Error", "No group is selected.")
        return

    for rect in app.selected_rectangles:
        app.groups[rect.group].remove(rect)
        rect.set_group(new_group)
        app.groups[new_group].append(rect)
    app.update_label(app.selected_rectangles[0])
