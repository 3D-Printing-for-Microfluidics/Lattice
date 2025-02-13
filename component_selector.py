"""Cutout tool for selecting one component from a print file."""

import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import ImageTk

from image_ops import export_cropped_slices, find_white_regions, merge_slices


class ProcessingPopup:
    """A simple popup window showing a processing message."""

    def __init__(self, parent: tk.Tk, message: str = "Processing images...") -> None:
        """Initialize and open the popup."""
        self.popup = tk.Toplevel(parent)
        self.popup.title("Processing")
        # Center the popup on screen
        w, h = 200, 50
        ws = parent.winfo_screenwidth()
        hs = parent.winfo_screenheight()
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        self.popup.geometry(f"{w}x{h}+{int(x)}+{int(y)}")
        tk.Label(self.popup, text=message, padx=20, pady=10).pack()
        self.popup.transient(parent)
        self.popup.grab_set()
        parent.update()

    def destroy(self) -> None:
        """Close the popup."""
        self.popup.destroy()


class ComponentSelector:
    """A UI for segmenting print files into their components by selcting and cropping slice images."""

    def __init__(self, parent: tk.Widget | None = None) -> None:
        """Initialize the ComponentSelector with an optional parent.

        Parameters
        ----------
        parent: tk.Widget | None
            The parent tk instance, if any.

        """
        if parent is None:
            parent = tk._default_root
        self.root = tk.Toplevel(parent)
        self.root.title("Component Selector")
        self.root.state("zoomed")

        self.input_zip = self._get_input_zip()
        if not self.input_zip:
            self.root.destroy()
            return

        # Initialize UI state
        self.highlight_rect = None
        self.selected_region_index = None
        self.selected_bbox = None
        self.preview_img = None
        self.preview_canvas_img = None

        # Load and process image with popup
        popup = ProcessingPopup(self.root)
        try:
            self.original_img = merge_slices(self.input_zip)
            self.regions_data = find_white_regions(self.original_img)
        finally:
            popup.destroy()

        # Set initial zoom
        screen_width = self.root.winfo_screenwidth() * 0.8
        screen_height = self.root.winfo_screenheight() * 0.8
        self.zoom_factor = min(screen_width / self.original_img.width, screen_height / self.original_img.height)

        self._create_widgets()
        self.redraw_image()
        self.root.mainloop()

    def _get_input_zip(self) -> str | None:
        """Prompt for input zip file."""
        msg = "Select the input print file (.zip)"
        messagebox.showinfo("Component Selector", msg)
        return filedialog.askopenfilename(
            title=msg,
            filetypes=[("Zip", "*.zip"), ("All Files", "*.*")],
        )

    def _create_widgets(self) -> None:
        """Create all UI widgets."""
        # Create the region details label
        self.region_details_label = tk.Label(self.root, text="Click a region to select it", bg="lightgray")
        self.region_details_label.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Create button frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        tk.Button(button_frame, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Export", command=self.export_cropped_images).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=self.root.destroy).pack(side=tk.LEFT, padx=5)

        # Create canvas with scrollbars
        preview_frame = tk.Frame(self.root)
        preview_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.scroll_y = tk.Scrollbar(preview_frame, orient=tk.VERTICAL)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scroll_x = tk.Scrollbar(preview_frame, orient=tk.HORIZONTAL)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.preview_canvas = tk.Canvas(
            preview_frame,
            width=self.original_img.width,
            height=self.original_img.height,
            xscrollcommand=self.scroll_x.set,
            yscrollcommand=self.scroll_y.set,
        )
        self.preview_canvas.pack(anchor="center", expand=True)

        # Configure scrollbars
        self.scroll_x.config(command=self.preview_canvas.xview)
        self.scroll_y.config(command=self.preview_canvas.yview)

        # Create initial preview image
        self.preview_img = ImageTk.PhotoImage(self.original_img)
        self.preview_canvas_img = self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=self.preview_img)

        # Bind events
        self.preview_canvas.bind("<Button-1>", self.on_canvas_click)

    def update_selection_box(self) -> None:
        """Update the red selection box based on current zoom level."""
        if self.selected_bbox is None:
            return
        if self.highlight_rect:
            self.preview_canvas.delete(self.highlight_rect)
        x_min, y_min, x_max, y_max = self.selected_bbox
        scaled_x_min = x_min * self.zoom_factor
        scaled_y_min = y_min * self.zoom_factor
        scaled_x_max = x_max * self.zoom_factor
        scaled_y_max = y_max * self.zoom_factor
        self.highlight_rect = self.preview_canvas.create_rectangle(
            scaled_x_min,
            scaled_y_min,
            scaled_x_max + 1,
            scaled_y_max + 1,
            outline="red",
            width=2,
        )

    def redraw_image(self) -> None:
        """Redraw the image at current zoom level."""
        new_width = int(self.original_img.width * self.zoom_factor)
        new_height = int(self.original_img.height * self.zoom_factor)
        resized_img = self.original_img.resize((new_width, new_height))
        self.preview_img = ImageTk.PhotoImage(resized_img)
        self.preview_canvas.itemconfig(self.preview_canvas_img, image=self.preview_img)
        self.preview_canvas.config(scrollregion=(0, 0, new_width, new_height))
        self.update_selection_box()  # Redraw selection box at new zoom level

    def zoom_in(self) -> None:
        """Increase zoom by 10%."""
        self.zoom_factor += 0.1
        self.redraw_image()

    def zoom_out(self) -> None:
        """Decrease zoom by 10%."""
        self.zoom_factor = max(0.1, self.zoom_factor - 0.1)
        self.redraw_image()

    def show_region_details(self, idx: int) -> None:
        """Update UI to show details of selected region."""
        self.selected_region_index = idx
        x_min, y_min, x_max, y_max = self.regions_data[idx]
        self.selected_bbox = (x_min, y_min, x_max, y_max)
        self.update_selection_box()
        self.region_details_label.config(text=f"Selected Region {idx+1} : bbox={self.regions_data[idx]}")

    def on_canvas_click(self, event: tk.Event) -> None:
        """Handle mouse clicks on the canvas."""
        # Convert mouse coords from screen/canvas space to original image coords
        canvas_x = self.preview_canvas.canvasx(event.x)
        canvas_y = self.preview_canvas.canvasy(event.y)
        img_x = canvas_x / self.zoom_factor
        img_y = canvas_y / self.zoom_factor

        # find the region that was clicked
        for idx, (x_min, y_min, x_max, y_max) in enumerate(self.regions_data):
            if (x_min <= img_x <= x_max) and (y_min <= img_y <= y_max):
                self.show_region_details(idx)
                return

    def export_cropped_images(self) -> None:
        """Export the selected region from all slices."""
        if self.selected_bbox is None:
            messagebox.showerror("No Region Selected", "Please select a region first.")
            return

        out_zip = filedialog.asksaveasfilename(
            title="Save cropped print file",
            defaultextension=".zip",
            filetypes=[("Zip", "*.zip"), ("All Files", "*.*")],
        )
        if not out_zip:
            return
        popup = ProcessingPopup(self.root, "Exporting images...")
        try:
            export_cropped_slices(self.input_zip, out_zip, self.selected_bbox)
        finally:
            popup.destroy()
        messagebox.showinfo("Export Complete", f"Cropped print file saved to:\n{out_zip}")


if __name__ == "__main__":
    ComponentSelector()
