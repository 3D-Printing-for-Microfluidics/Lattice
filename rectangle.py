"""Rectangle class for the RectangleApp."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk

    from rectangle_app import RectangleApp

SHIFT_KEY = 0x0001


class Rectangle:
    """A class used to represent a Rectangle on the Tkinter Canvas.

    Attributes
    ----------
    app : RectangleApp
        Reference to the RectangleApp instance.
    rect : int
        The ID of the rectangle on the canvas.
    x : int
        The x-coordinate of the rectangle.
    y : int
        The y-coordinate of the rectangle.
    width : int
        The width of the rectangle.
    height : int
        The height of the rectangle.
    start_x : int | None
        The starting x-coordinate for dragging.
    start_y : int | None
        The starting y-coordinate for dragging.
    selected : bool
        Whether the rectangle is selected.
    group : str
        The group to which the rectangle belongs.
    dragged : bool
        Whether the rectangle was dragged.

    """

    def __init__(  # noqa: PLR0913
        self,
        app: RectangleApp,
        x: int,
        y: int,
        width: int,
        height: int,
        group: str,
    ) -> None:
        """Initialize a rectangle.

        Parameters
        ----------
        app : RectangleApp
            The app in which the rectangle is drawn.
        x : int
            The x-coordinate of the rectangle.
        y : int
            The y-coordinate of the rectangle.
        width : int
            The width of the rectangle.
        height : int
            The height of the rectangle.
        app : RectangleApp
            Reference to the RectangleApp instance.
        group : str
            The group to which the rectangle belongs.

        """
        self.app = app
        self.rect = self.app.canvas.create_rectangle(
            x,
            y,
            x + width,
            y + height,
            fill="blue",
            tags="rect",
            outline="",
            width=0,
        )
        self.app.canvas.tag_bind(self.rect, "<Button-1>", self.on_click)
        self.app.canvas.tag_bind(self.rect, "<B1-Motion>", self.on_drag)
        self.app.canvas.tag_bind(self.rect, "<ButtonRelease-1>", self.on_release)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.start_x = None
        self.start_y = None
        self.group = group
        self.dragged = False

    def on_click(self, event: tk.Event) -> None:
        """Handle the click event on the rectangle.

        Parameters
        ----------
        event : tk.Event
            The event object containing information about the click event.

        """
        if not self.app.canvas.find_withtag("current"):  # If no rectangle was clicked
            return

        self.start_x = event.x
        self.start_y = event.y
        self.dragged = False

    def on_drag(self, event: tk.Event) -> None:
        """Handle the drag event on the rectangle.

        Parameters
        ----------
        event : tk.Event
            The event object containing information about the drag event.

        """
        if self.start_x is not None and self.start_y is not None:
            dx = event.x - self.start_x
            dy = event.y - self.start_y
            if dx != 0 or dy != 0:
                self.dragged = True
            for rect in self.app.selected_rectangles:
                self.app.canvas.move(rect.rect, dx, dy)
                rect.x += dx
                rect.y += dy
            self.start_x = event.x
            self.start_y = event.y
            self.app.update_label(self)

    def on_release(self, event: tk.Event) -> None:
        """Handle the release event on the rectangle.

        Parameters
        ----------
        event : tk.Event
            The event object containing information about the release event.

        """
        if not self.dragged:
            if event.state & SHIFT_KEY:  # If shift key was pressed while clicking
                self.toggle_selection()
            else:  # If a single rectangle was clicked without the shift key
                self.app.deselect_all()
                self.select()
            self.app.update_label(self)

    def delete(self) -> None:
        """Delete the rectangle from the canvas."""
        self.app.canvas.delete(self.rect)

    def set_color(self, color: str) -> None:
        """Set the color of the rectangle.

        Parameters
        ----------
        color : str
            The color to set for the rectangle.

        """
        self.app.canvas.itemconfig(self.rect, fill=color)

    def set_group(self, group: str) -> None:
        """Set the group of the rectangle and update its color.

        Parameters
        ----------
        group : str
            The group to set for the rectangle.

        """
        self.group = group
        color = self.app.colors[group]
        self.set_color(color)

    def select(self) -> None:
        """Select the rectangle."""
        self.app.canvas.itemconfig(self.rect, outline="red", width=3)
        if self not in self.app.selected_rectangles:
            self.app.selected_rectangles.append(self)

    def deselect(self) -> None:
        """Deselect the rectangle."""
        self.app.canvas.itemconfig(self.rect, outline="", width=0)
        if self in self.app.selected_rectangles:
            self.app.selected_rectangles.remove(self)

    def toggle_selection(self) -> None:
        """Toggle the selection state of the rectangle."""
        if self in self.app.selected_rectangles:
            self.deselect()
        else:
            self.select()

    def set_position(self, x: int, y: int) -> None:
        """Set the position of the rectangle.

        Parameters
        ----------
        x : int
            The new x-coordinate of the rectangle.
        y : int
            The new y-coordinate of the rectangle.

        """
        dx = x - self.x
        dy = y - self.y
        self.app.canvas.move(self.rect, dx, dy)
        self.x = x
        self.y = y

    def to_dict(self) -> dict:
        """Convert the rectangle to a dictionary.

        Returns
        -------
        dict
            A dictionary representation of the rectangle.

        """
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "group": self.group,
        }
