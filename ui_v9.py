import json
import tkinter as tk
from tkinter import colorchooser, filedialog, simpledialog


class Rectangle:
    def __init__(self, canvas, x, y, width, height, app, group=None):
        self.canvas = canvas
        self.app = app  # Reference to the RectangleApp instance
        self.rect = canvas.create_rectangle(x, y, x + width, y + height, fill="blue", tags="rect")
        self.canvas.tag_bind(self.rect, "<Button-1>", self.on_click)
        self.canvas.tag_bind(self.rect, "<B1-Motion>", self.on_drag)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.start_x = None
        self.start_y = None
        self.selected = False
        self.group = group

    def on_click(self, event):
        if not self.canvas.find_withtag("current"):
            return

        if event.state & 0x0001:  # Shift key is held
            if self.selected:
                self.selected = False
                self.canvas.itemconfig(self.rect, outline="", width=1)
                self.app.selected_rectangles.remove(self)
            else:
                self.selected = True
                self.canvas.itemconfig(self.rect, outline="red", width=3)
                self.app.selected_rectangles.append(self)
        else:
            # Deselect all other rectangles
            for rect in self.app.selected_rectangles:
                rect.selected = False
                self.canvas.itemconfig(rect.rect, outline="", width=1)
            self.app.selected_rectangles.clear()

            # Select the clicked rectangle
            self.selected = True
            self.canvas.itemconfig(self.rect, outline="red", width=3)
            self.app.selected_rectangles.append(self)

        # Update label with dimensions, coordinates, and group of the last clicked rectangle
        self.app.update_label(self)

        # Set start coordinates for dragging
        self.start_x = event.x
        self.start_y = event.y

    def on_drag(self, event):
        if self.start_x is not None and self.start_y is not None:
            dx = event.x - self.start_x
            dy = event.y - self.start_y
            for rect in self.app.selected_rectangles:
                self.canvas.move(rect.rect, dx, dy)
                rect.x += dx
                rect.y += dy
            self.start_x = event.x
            self.start_y = event.y
            self.app.update_label(self)

    def delete(self):
        self.canvas.delete(self.rect)

    def set_color(self, color):
        self.canvas.itemconfig(self.rect, fill=color)

    def set_group(self, group):
        self.group = group
        color = self.app.colors.get(group, "blue")
        self.set_color(color)


class RectangleApp:
    def __init__(self, master):
        self.master = master
        self.master.title("3D Print Dose Customization")

        # Create a frame for the button bar
        self.button_bar = tk.Frame(master)
        self.button_bar.pack(side=tk.TOP, fill=tk.X)
        self.pad_x = 1
        self.pad_y = 0

        # Add buttons to the button bar

        self.load_button = tk.Button(self.button_bar, text="Load", command=self.load_rectangles)
        self.load_button.pack(side=tk.LEFT, padx=self.pad_x, pady=self.pad_y)

        self.save_button = tk.Button(self.button_bar, text="Save", command=self.save_rectangles)
        self.save_button.pack(side=tk.LEFT, padx=self.pad_x, pady=self.pad_y)

        self.add_button = tk.Button(self.button_bar, text="Add Rectangle", command=self.add_rectangle)
        self.add_button.pack(side=tk.LEFT, padx=self.pad_x, pady=self.pad_y)

        self.delete_button = tk.Button(self.button_bar, text="Delete Rectangle", command=self.delete_rectangle)
        self.delete_button.pack(side=tk.LEFT, padx=self.pad_x, pady=self.pad_y)

        # Group controls
        self.new_group_button = tk.Button(self.button_bar, text="New Group", command=self.new_group)
        self.new_group_button.pack(side=tk.LEFT, padx=self.pad_x + 10, pady=self.pad_y)

        self.group_label = tk.Label(self.button_bar, text="Current Group:")
        self.group_label.pack(side=tk.LEFT, padx=self.pad_x, pady=self.pad_y)

        self.group_var = tk.StringVar()
        self.group_dropdown = tk.OptionMenu(self.button_bar, self.group_var, "")
        self.group_dropdown.pack(side=tk.LEFT, padx=self.pad_x, pady=self.pad_y)

        self.set_color_button = tk.Button(self.button_bar, text="Set Group Color", command=self.set_group_color)
        self.set_color_button.pack(side=tk.LEFT, padx=self.pad_x, pady=self.pad_y)

        self.rename_group_button = tk.Button(self.button_bar, text="Rename Group", command=self.rename_group)
        self.rename_group_button.pack(side=tk.LEFT, padx=self.pad_x, pady=self.pad_y)

        self.change_group_button = tk.Button(
            self.button_bar,
            text="Change selected to this group",
            command=self.change_group,
        )
        self.change_group_button.pack(side=tk.LEFT, padx=self.pad_x, pady=self.pad_y)

        self.dimensions_label = tk.Label(master, text="", bg="lightgray")
        self.dimensions_label.pack(side=tk.TOP, fill=tk.X)

        self.canvas = tk.Canvas(master, width=400, height=400, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.rectangles = []
        self.selected_rectangles = []
        self.groups = {}
        self.colors = {}

    def add_rectangle(self):
        # Deselect all other rectangles
        for rect in self.selected_rectangles:
            rect.selected = False
            self.canvas.itemconfig(rect.rect, outline="", width=0)
        self.selected_rectangles.clear()

        # Create a new rectangle and select it
        x, y, width, height = 50, 50, 100, 100
        group = self.group_var.get() if self.group_var.get() else None
        rectangle = Rectangle(self.canvas, x, y, width, height, self, group)
        if group:
            rectangle.set_color(self.colors[group])
        rectangle.selected = True
        self.canvas.itemconfig(rectangle.rect, outline="red", width=3)
        self.rectangles.append(rectangle)
        self.selected_rectangles.append(rectangle)

        # Update label with dimensions and coordinates of the new rectangle
        self.update_label(rectangle)

    def delete_rectangle(self):
        for rect in self.selected_rectangles:
            rect.delete()
            self.rectangles.remove(rect)
        self.selected_rectangles.clear()

    def save_rectangles(self):
        data = [
            {"x": rect.x, "y": rect.y, "width": rect.width, "height": rect.height, "group": rect.group}
            for rect in self.rectangles
        ]

        # Prompt the user for a filename with a default name
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile="rectangles.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if filename:
            with open(filename, "w") as f:
                json.dump({"rectangles": data, "colors": self.colors}, f)

    def load_rectangles(self):
        filename = filedialog.askopenfilename(
            defaultextension=".json",
            initialfile="rectangles.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if filename:
            try:
                with open(filename, "r") as f:
                    data = json.load(f)
                    for rect_data in data["rectangles"]:
                        rectangle = Rectangle(
                            self.canvas,
                            rect_data["x"],
                            rect_data["y"],
                            rect_data["width"],
                            rect_data["height"],
                            self,
                            rect_data.get("group"),
                        )
                        if rect_data.get("group"):
                            rectangle.set_color(self.colors[rect_data["group"]])
                        self.rectangles.append(rectangle)
                    self.colors = data.get("colors", {})
                    self.update_group_dropdown()
            except FileNotFoundError:
                print("File not found.")
            except json.JSONDecodeError:
                print("Invalid JSON file.")

    def update_label(self, rect):
        group_text = f", Group: {rect.group}" if rect.group else ""
        dim_text = f"X: {rect.x}, Y: {rect.y}, Width: {rect.width}, Height: {rect.height}"
        self.dimensions_label.config(text=(dim_text + group_text))

    def new_group(self):
        group_name = simpledialog.askstring("Group Name", "Enter a name for the new group:")
        if group_name and group_name not in self.groups:
            self.groups[group_name] = []
            self.colors[group_name] = "blue"  # Default color
            self.update_group_dropdown()

    def rename_group(self):
        current_group = self.group_var.get()
        if current_group:
            new_group_name = simpledialog.askstring("Rename Group", f"Enter a new name for '{current_group}':")
            if new_group_name and new_group_name != current_group:
                self.groups[new_group_name] = self.groups.pop(current_group, [])
                self.colors[new_group_name] = self.colors.pop(current_group, "blue")
                self.update_group_dropdown()

                # Update rectangles belonging to the renamed group
                for rect in self.rectangles:
                    if rect.group == current_group:
                        rect.set_group(new_group_name)
                        self.update_label(rect)

    def set_group_color(self):
        group = self.group_var.get()
        if group:
            color = colorchooser.askcolor()[1]
            if color:
                self.colors[group] = color
                for rect in self.rectangles:
                    if rect.group == group:
                        rect.set_color(color)

    def change_group(self):
        group = self.group_var.get()
        if group:
            for rect in self.selected_rectangles:
                rect.set_group(group)
                self.update_label(rect)

    def update_group_dropdown(self):
        menu = self.group_dropdown["menu"]
        menu.delete(0, "end")
        for group in self.groups:
            menu.add_command(label=group, command=tk._setit(self.group_var, group))
        if self.groups:
            self.group_var.set(list(self.groups.keys())[0])


def main():
    root = tk.Tk()
    app = RectangleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
