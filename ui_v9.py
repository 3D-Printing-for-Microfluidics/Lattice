import tkinter as tk
from tkinter import filedialog
import json


class Rectangle:
    def __init__(self, canvas, x, y, width, height):
        self.canvas = canvas
        self.rect = canvas.create_rectangle(
            x, y, x + width, y + height, fill="blue", tags="rect"
        )
        self.canvas.tag_bind(self.rect, "<Button-1>", self.on_click)
        self.canvas.tag_bind(self.rect, "<B1-Motion>", self.on_drag)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.start_x = None  # Initialize start_x
        self.start_y = None  # Initialize start_y
        self.selected = False  # Track whether the rectangle is selected

    def on_click(self, event):
        # Remove red outline from previously selected rectangle
        for rect in self.canvas.find_withtag("rect"):
            self.canvas.itemconfig(rect, outline="")
            for r in self.canvas.find_withtag("rect"):
                if self.canvas.gettags(r) == ("rect", "selected"):
                    self.canvas.itemconfig(r, tags="rect")

        # Set red outline for the selected rectangle
        self.canvas.itemconfig(self.rect, outline="red", width=2)
        self.canvas.itemconfig(self.rect, tags=("rect", "selected"))

        # Update label with dimensions and coordinates
        self.canvas.itemconfig(
            "dimensions",
            text=f"X: {self.x}, Y: {self.y}, Width: {self.width}, Height: {self.height}",
        )

        # Set start coordinates for dragging
        self.start_x = event.x
        self.start_y = event.y

    def on_drag(self, event):
        if (
            self.start_x is not None and self.start_y is not None
        ):  # Check if start coordinates are initialized
            dx = event.x - self.start_x
            dy = event.y - self.start_y
            self.canvas.move(self.rect, dx, dy)
            self.x += dx
            self.y += dy
            self.start_x = event.x
            self.start_y = event.y
            self.canvas.itemconfig(
                "dimensions",
                text=f"X: {self.x}, Y: {self.y}, Width: {self.width}, Height: {self.height}",
            )

    def delete(self):
        self.canvas.delete(self.rect)


class RectangleApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Rectangle App")

        self.canvas = tk.Canvas(master, width=1600, height=800, bg="white")
        self.canvas.pack()

        self.rectangles = []

        # Create label for dimensions and coordinates
        self.dimensions_label = tk.Label(master, text="test")
        self.dimensions_label.pack(fill=tk.X)

        self.add_button = tk.Button(
            master, text="Add Rectangle", command=self.add_rectangle
        )
        self.add_button.pack()

        self.delete_button = tk.Button(
            master, text="Delete Rectangle", command=self.delete_rectangle
        )
        self.delete_button.pack()

        self.save_button = tk.Button(master, text="Save", command=self.save_rectangles)
        self.save_button.pack()

        self.load_button = tk.Button(master, text="Load", command=self.load_rectangles)
        self.load_button.pack()

    def add_rectangle(self):
        # You can get dimensions from text input boxes here
        x, y, width, height = 50, 50, 100, 100
        rectangle = Rectangle(self.canvas, x, y, width, height)
        self.rectangles.append(rectangle)

    def delete_rectangle(self):
        for rect in self.canvas.find_withtag("rect"):
            if self.canvas.gettags(rect) == ("rect", "selected"):
                for r in self.rectangles:
                    if r.rect == rect:
                        r.delete()
                        self.rectangles.remove(r)
                        break

    def save_rectangles(self):
        data = []
        for rect in self.rectangles:
            data.append(
                {"x": rect.x, "y": rect.y, "width": rect.width, "height": rect.height}
            )

        # Prompt the user for a filename
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
                    )
                    self.rectangles.append(rectangle)
            except FileNotFoundError:
                print("File not found.")
            except json.JSONDecodeError:
                print("Invalid JSON file.")


def main():
    root = tk.Tk()
    app = RectangleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
