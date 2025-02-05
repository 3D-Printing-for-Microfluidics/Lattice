"""App methods in the File menu."""

import json
from pathlib import Path
from tkinter import filedialog, simpledialog
from typing import TYPE_CHECKING

from rectangle import Rectangle

if TYPE_CHECKING:
    from app import App


def save_json(app: "App") -> None:
    """Save the rectangles and colors to a JSON file."""
    data = {}
    data["groups"] = {}
    data["colors"] = app.colors

    for group_name, rects in app.groups.items():
        data["groups"][group_name] = []
        for rect in rects:
            part_info = rect.to_dict()
            part_info.pop("group", None)
            data["groups"][group_name].append(part_info)

    filename = filedialog.asksaveasfilename(
        defaultextension=".json",
        initialfile="rectangles.json",
        filetypes=[("JSON files", "*.json")],
    )
    if filename:
        with Path(filename).open("w") as f:
            json.dump(data, f, indent=4)


def load_json(app: "App") -> None:
    """Load rectangles and colors from a JSON file."""
    filename = filedialog.askopenfilename(
        defaultextension=".json",
        initialfile="rectangles.json",
        filetypes=[("JSON files", "*.json")],
    )
    if not filename:  # Dialog was closed without selecting a file
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

    app.clear_canvas()
    app.colors = data.get("colors", {})
    groups = data.get("groups", {})

    for group_name, group in groups.items():
        app.groups[group_name] = []
        for r in group:
            rectangle = Rectangle(app, group=group_name, **r)
            rectangle.set_color(app.colors[group_name])
            app.groups[group_name].append(rectangle)

    app.update_group_dropdown()
