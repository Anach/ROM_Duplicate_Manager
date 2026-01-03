"""UI Components for ROM Duplicate Manager."""

import tkinter as tk
from tkinter import ttk
from typing import Union, Any, Optional


class ToolTip:
    """Tooltip widget for providing contextual help on UI elements.

    Creates hover tooltips that appear after a delay and disappear when
    the mouse leaves the widget or when clicked.
    """

    def __init__(self, widget: tk.Widget, text: str) -> None:
        """Initialize tooltip for a widget.

        Args:
            widget: The tkinter widget to attach the tooltip to
            text: The tooltip text to display
        """
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None
        widget.bind("<Enter>", self.schedule_tip, add="+")
        widget.bind("<Leave>", self.hide_tip, add="+")
        widget.bind("<ButtonPress>", self.hide_tip, add="+")

    def schedule_tip(self, event: Optional[tk.Event] = None) -> None:
        """Schedule tooltip to show after delay."""
        self.hide_tip()
        if self.text:
            self.id = self.widget.after(500, self.show_tip)

    def show_tip(self, event: Optional[tk.Event] = None) -> None:
        """Display the tooltip window."""
        if not self.text:
            return
        try:
            if not self.widget.winfo_exists() or not self.widget.winfo_viewable():
                return
        except tk.TclError:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        tw.attributes("-topmost", True)
        label = tk.Label(tw, text=self.text, justify='left',
                       background="#ffffe0", foreground="black", relief='solid', borderwidth=1,
                       font=("tahoma", 8, "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event: Optional[tk.Event] = None) -> None:
        """Hide the tooltip window."""
        if self.id:
            try:
                self.widget.after_cancel(self.id)
            except tk.TclError:
                pass
            self.id = None
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except tk.TclError:
                pass
            self.tip_window = None


class AutoScrollbar(ttk.Scrollbar):
    """A scrollbar that automatically hides when not needed.

    Extends ttk.Scrollbar to provide auto-hiding functionality
    based on content size.
    """

    def set(self, first: Union[str, float], last: Union[str, float]) -> None:  # type: ignore[override]
        """Override set method to handle auto-hiding.

        Args:
            first: Lower bound of scrollbar position
            last: Upper bound of scrollbar position
        """
        if float(first) <= 0.0 and float(last) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        ttk.Scrollbar.set(self, first, last)


def create_tooltip(widget: tk.Widget, text: str) -> None:
    """Create or update a tooltip for a widget.

    Args:
        widget: The widget to attach the tooltip to
        text: The tooltip text to display
    """
    if hasattr(widget, 'tooltip'):
        widget.tooltip.text = text  # type: ignore[attr-defined]
    else:
        widget.tooltip = ToolTip(widget, text)  # type: ignore[attr-defined]

    # Ensure tooltips work on complex widgets like Combobox
    def bind_children(w: tk.Misc) -> None:
        for child in w.winfo_children():
            child.bind("<Enter>", widget.tooltip.schedule_tip, add="+")  # type: ignore[attr-defined]
            child.bind("<Leave>", widget.tooltip.hide_tip, add="+")  # type: ignore[attr-defined]
            bind_children(child)

    try:
        bind_children(widget)
    except tk.TclError:
        pass