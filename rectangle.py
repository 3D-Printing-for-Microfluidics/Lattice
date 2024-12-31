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
    canvas : tk.Canvas
        The canvas on which the rectangle is drawn.
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
    group : str | None
        The group to which the rectangle belongs.

    """

    def __init__(  # noqa: PLR0913
        self,
        app: RectangleApp,
        x: int,
        y: int,
        width: int,
        height: int,
        group: str | None = None,
    ) -> None:
        """Initialize a rectangle.

        Parameters
        ----------
        canvas : tk.Canvas
            The canvas on which the rectangle is drawn.
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
        group : str | None
            The group to which the rectangle belongs (default is None).

        """
        self.app = app
        self.canvas = app.canvas
        self.rect = self.canvas.create_rectangle(
            x,
            y,
            x + width,
            y + height,
            fill="blue",
            tags="rect",
            outline="",
            width=0,
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
        self.group = group

    def on_click(self, event: tk.Event) -> None:
        """Handle the click event on the rectangle.

        Parameters
        ----------
        event : tk.Event
            The event object containing information about the click event.

        """
        if not self.canvas.find_withtag("current"):  # If no rectangle was clicked
            return

        if event.state & SHIFT_KEY:  # If shift key was pressed while clicking
            self.toggle_selection()
        else:  # If a single rectangle was clicked without the shift key
            self.app.deselect_all()
            self.select()

        self.app.update_label(self)
        self.start_x = event.x
        self.start_y = event.y

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
            for rect in self.app.selected_rectangles:
                self.canvas.move(rect.rect, dx, dy)
                rect.x += dx
                rect.y += dy
            self.start_x = event.x
            self.start_y = event.y
            self.app.update_label(self)

    def delete(self) -> None:
        """Delete the rectangle from the canvas."""
        self.canvas.delete(self.rect)

    def set_color(self, color: str) -> None:
        """Set the color of the rectangle.

        Parameters
        ----------
        color : str
            The color to set for the rectangle.

        """
        self.canvas.itemconfig(self.rect, fill=color)

    def set_group(self, group: str) -> None:
        """Set the group of the rectangle and update its color.

        Parameters
        ----------
        group : str
            The group to set for the rectangle.

        """
        self.group = group
        color = self.app.colors.get(group, "blue")
        self.set_color(color)

    def select(self) -> None:
        """Select the rectangle."""
        self.selected = True
        self.canvas.itemconfig(self.rect, outline="red", width=3)
        self.app.selected_rectangles.append(self)

    def deselect(self) -> None:
        """Deselect the rectangle."""
        self.selected = False
        self.canvas.itemconfig(self.rect, outline="", width=0)
        if self in self.app.selected_rectangles:
            self.app.selected_rectangles.remove(self)

    def toggle_selection(self) -> None:
        """Toggle the selection state of the rectangle."""
        if self.selected:
            self.deselect()
        else:
            self.select()
