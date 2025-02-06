"""Component class for the App."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk

    from app import App

SHIFT_KEY = 0x0001


class Component:
    """A class used to represent a Component on the Tkinter Canvas.

    Attributes
    ----------
    app : App
        Reference to the App instance.
    comp : int
        The ID of the component on the canvas.
    x : int
        The x-coordinate of the component.
    y : int
        The y-coordinate of the component.
    width : int
        The width of the component.
    height : int
        The height of the component.
    start_x : int | None
        The starting x-coordinate for dragging.
    start_y : int | None
        The starting y-coordinate for dragging.
    selected : bool
        Whether the component is selected.
    group : str
        The group to which the component belongs.
    dragged : bool
        Whether the component was dragged.

    """

    def __init__(  # noqa: PLR0913
        self,
        app: App,
        x: int,
        y: int,
        width: int,
        height: int,
        group: str,
    ) -> None:
        """Initialize a component.

        Parameters
        ----------
        app : App
            The app in which the component is drawn.
        x : int
            The x-coordinate of the component.
        y : int
            The y-coordinate of the component.
        width : int
            The width of the component.
        height : int
            The height of the component.
        app : App
            Reference to the App instance.
        group : str
            The group to which the component belongs.

        """
        self.app = app
        self.comp = self.app.canvas.create_rectangle(
            x,
            y,
            x + width,
            y + height,
            fill="blue",
            tags="comp",
            outline="",
            width=0,
        )
        self.app.canvas.tag_bind(self.comp, "<Button-1>", self.on_click)
        self.app.canvas.tag_bind(self.comp, "<B1-Motion>", self.on_drag)
        self.app.canvas.tag_bind(self.comp, "<ButtonRelease-1>", self.on_release)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.start_x = None
        self.start_y = None
        self.group = group
        self.dragged = False

    def on_click(self, event: tk.Event) -> None:
        """Handle the click event on the component.

        Parameters
        ----------
        event : tk.Event
            The event object containing information about the click event.

        """
        if not self.app.canvas.find_withtag("current"):  # If no component was clicked
            return

        self.start_x = event.x
        self.start_y = event.y
        self.dragged = False

    def on_drag(self, event: tk.Event) -> None:
        """Handle the drag event on the component.

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
            for comp in self.app.selection:
                self.app.canvas.move(comp.comp, dx, dy)
                comp.x += dx
                comp.y += dy
            self.start_x = event.x
            self.start_y = event.y
            self.app.update_label(self)

    def on_release(self, event: tk.Event) -> None:
        """Handle the release event on the component.

        Parameters
        ----------
        event : tk.Event
            The event object containing information about the release event.

        """
        if not self.dragged:
            if event.state & SHIFT_KEY:  # If shift key was pressed while clicking
                self.toggle_selection()
            else:  # If a single component was clicked without the shift key
                self.app.deselect_all()
                self.select()
            self.app.update_label(self)

    def delete(self) -> None:
        """Delete the component from the canvas."""
        self.app.canvas.delete(self.comp)

    def set_color(self, color: str) -> None:
        """Set the color of the component.

        Parameters
        ----------
        color : str
            The color to set for the component.

        """
        self.app.canvas.itemconfig(self.comp, fill=color)

    def set_group(self, group: str) -> None:
        """Set the group of the component and update its color.

        Parameters
        ----------
        group : str
            The group to set for the component.

        """
        self.group = group
        color = self.app.colors[group]
        self.set_color(color)

    def select(self) -> None:
        """Select the component."""
        self.app.canvas.itemconfig(self.comp, outline="red", width=3)
        if self not in self.app.selection:
            self.app.selection.append(self)

    def deselect(self) -> None:
        """Deselect the component."""
        self.app.canvas.itemconfig(self.comp, outline="", width=0)
        if self in self.app.selection:
            self.app.selection.remove(self)

    def toggle_selection(self) -> None:
        """Toggle the selection state of the component."""
        if self in self.app.selection:
            self.deselect()
        else:
            self.select()

    def set_position(self, x: int, y: int) -> None:
        """Set the position of the component.

        Parameters
        ----------
        x : int
            The new x-coordinate of the component.
        y : int
            The new y-coordinate of the component.

        """
        dx = x - self.x
        dy = y - self.y
        self.app.canvas.move(self.comp, dx, dy)
        self.x = x
        self.y = y

    def to_dict(self) -> dict:
        """Convert the component to a dictionary.

        Returns
        -------
        dict
            A dictionary representation of the component.

        """
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "group": self.group,
        }
