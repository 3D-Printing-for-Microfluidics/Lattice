"""Simple popup to let user know something is happening."""

import tkinter as tk


class Popup:
    """A simple popup window with a message."""

    def __init__(self, parent: tk.Tk, message: str) -> None:
        """Initialize and open the popup.

        Parameters
        ----------
        parent: tk.Tk()
            Reference to parent window.
        message: str
            Message to display.

        """
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
