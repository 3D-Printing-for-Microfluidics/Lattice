import tkinter as tk
from tkinter import filedialog
import json


class Rectangle:
    def __init__(self, canvas, x, y, width, height, app):
        self.canvas = canvas
        self.app = app  # Reference to the RectangleApp instance
        self.rect = canvas.create_rectangle(
            x, y, x + width, y + height, fill="blue", tags="rect"
        )
        self.canvas.tag_bind(self.rect, "<Button-1>", self.on_click)
        self.canvas.tag_bind(self.rect, "<B1-Motion>", self.on_drag)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.start_x = None
        self.start_y = None
        self.selected = False

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

        # Update label with dimensions and coordinates of the last clicked rectangle
        self.app.update_label(self.x, self.y, self.width, self.height)

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
            self.app.update_label(self.x, self.y, self.width, self.height)

    def delete(self):
        self.canvas.delete(self.rect)


class RectangleApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Rectangle App")

        # Create a frame for the buttons
        self.button_frame = tk.Frame(master)
        self.button_frame.pack(side=tk.TOP, fill=tk.X)

        # Add buttons to the button frame
        self.add_button = tk.Button(
            self.button_frame, text="Add Rectangle", command=self.add_rectangle
        )
        self.add_button.pack(side=tk.LEFT)

        self.delete_button = tk.Button(
            self.button_frame, text="Delete Rectangle", command=self.delete_rectangle
        )
        self.delete_button.pack(side=tk.LEFT)

        self.save_button = tk.Button(
            self.button_frame, text="Save", command=self.save_rectangles
        )
        self.save_button.pack(side=tk.LEFT)

        self.load_button = tk.Button(
            self.button_frame, text="Load", command=self.load_rectangles
        )
        self.load_button.pack(side=tk.LEFT)

        self.dimensions_label = tk.Label(master, text="", bg="lightgray")
        self.dimensions_label.pack(side=tk.TOP, fill=tk.X)

        self.canvas = tk.Canvas(master, width=1200, height=800, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.rectangles = []
        self.selected_rectangles = []

    def add_rectangle(self):
        # Deselect all other rectangles
        for rect in self.selected_rectangles:
            rect.selected = False
            self.canvas.itemconfig(rect.rect, outline="", width=1)
        self.selected_rectangles.clear()

        # Create a new rectangle and select it
        x, y, width, height = 50, 50, 100, 100
        rectangle = Rectangle(self.canvas, x, y, width, height, self)
        rectangle.selected = True
        self.canvas.itemconfig(rectangle.rect, outline="red", width=3)
        self.rectangles.append(rectangle)
        self.selected_rectangles.append(rectangle)

        # Update label with dimensions and coordinates of the new rectangle
        self.update_label(rectangle.x, rectangle.y, rectangle.width, rectangle.height)

    def delete_rectangle(self):
        for rect in self.selected_rectangles:
            rect.delete()
            self.rectangles.remove(rect)
        self.selected_rectangles.clear()

    def save_rectangles(self):
        data = []
        for rect in self.rectangles:
            data.append(
                {"x": rect.x, "y": rect.y, "width": rect.width, "height": rect.height}
            )

        # Prompt the user for a filename with a default name
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile="rectangles.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if filename:
            with open(filename, "w") as f:
                json.dump(data, f)

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
                for rect_data in data:
                    rectangle = Rectangle(
                        self.canvas,
                        rect_data["x"],
                        rect_data["y"],
                        rect_data["width"],
                        rect_data["height"],
                        self,
                    )
                    self.rectangles.append(rectangle)
            except FileNotFoundError:
                print("File not found.")
            except json.JSONDecodeError:
                print("Invalid JSON file.")

    def update_label(self, x, y, width, height):
        self.dimensions_label.config(
            text=f"X: {x}, Y: {y}, Width: {width}, Height: {height}"
        )


def main():
    root = tk.Tk()
    app = RectangleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
