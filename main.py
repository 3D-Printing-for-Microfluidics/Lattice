"""UI for 3D Print Dose Customization."""

from __future__ import annotations

import tkinter as tk

from rectangle_app import RectangleApp


def main() -> None:
    """Run the Tkinter application."""
    root = tk.Tk()
    RectangleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
