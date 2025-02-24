"""Base class for application menus."""

import tkinter as tk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.app import App


class Menu:
    """Base class for menu functionality."""

    def __init__(self, app: "App", menubar: tk.Menu) -> None:
        """Initialize menu.

        Parameters
        ----------
        app : App
            Application instance.
        menubar : tk.Menu
            Main menu bar.

        """
        self.app = app
        self.menu = tk.Menu(menubar, tearoff=0)
        self._create_menu(menubar)
        self._bind_shortcuts()

    def _create_menu(self, menubar: tk.Menu) -> None:
        """Create menu items. Override in subclasses.

        Parameters
        ----------
        menubar: tk.Menu
            The menubar to attach to.

        """
        raise NotImplementedError

    def _bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts. Override in subclasses."""
