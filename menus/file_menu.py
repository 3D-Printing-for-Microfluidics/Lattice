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
    data = {
        "rectangles": [rect.to_dict() for group in app.groups.values() for rect in group],
        "colors": app.colors,
    }
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

    for group in app.groups.values():
        for rect in group:
            rect.delete()

    app.groups.clear()
    app.colors = data.get("colors", {})
    app.groups = {group: [] for group in app.colors}

    for r in data.get("rectangles", []):
        group = r["group"]
        rectangle = Rectangle(app, r["x"], r["y"], r["width"], r["height"], group)
        rectangle.set_color(app.colors[group])
        app.groups[group].append(rectangle)

    app.update_group_dropdown()
