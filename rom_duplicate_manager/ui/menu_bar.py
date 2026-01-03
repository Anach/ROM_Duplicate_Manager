"""Menu bar management mixin for ROM Duplicate Manager.

This module contains all custom menu bar related methods using
custom Toplevel-based dropdown menus for full theme and behavior control.
"""

import platform
import tkinter as tk
from typing import Any, Callable, List, Optional, Tuple


def _get_menu_font() -> tuple:
    """Get the appropriate menu font for the current platform."""
    system = platform.system()
    if system == 'Windows':
        return ('Segoe UI', 9)
    elif system == 'Darwin':  # macOS
        return ('SF Pro Text', 13)  # macOS uses larger fonts
    else:  # Linux and others
        return ('Sans', 9)


class MenuBarMixin:
    """Mixin class providing custom menu bar functionality."""

    def _create_menu_bar(self) -> None:
        """Create a custom frame-based menu bar that supports full theming."""
        # Determine current theme colors - delegate to shared method
        is_dark = self.dark_mode_enabled.get()
        self._update_menu_colors(is_dark)

        # Create custom menu bar frame
        self.menu_bar_frame = tk.Frame(self, bg=self.menu_bg, relief='flat', bd=0)  # type: ignore
        self.menu_bar_frame.pack(side='top', fill='x')

        # Store menu buttons for theming
        self.menu_buttons: List[tk.Label] = []
        self.active_menu: Optional[tk.Label] = None
        self.menu_armed = False  # Track if we're in "hover-to-open" mode
        self.current_dropdown: Optional[tk.Toplevel] = None

        # Define menu structures: (label, menu_items_creator)
        self._create_menu_item("File", self._get_file_menu_items)
        self._create_menu_item("View", self._get_view_menu_items)
        self._create_menu_item("Tools", self._get_tools_menu_items)
        self._create_menu_item("Help", self._get_help_menu_items)

        # Bind keyboard shortcuts
        self.bind_all("<Control-o>", lambda e: self.browse_folder())
        self.bind_all("<Control-r>", lambda e: self.scan())

        # Close menus when pressing Escape
        self.bind_all("<Escape>", lambda e: self._fully_close_menu())

    def _update_menu_colors(self, is_dark: bool) -> None:
        """Update menu color scheme based on ttkbootstrap theme."""
        colors = self.style.colors

        self.menu_bg = colors.bg
        self.menu_fg = colors.fg
        self.dropdown_fg = colors.fg

        if is_dark:
            self.menu_hover_bg = colors.dark
            self.menu_active_bg = colors.secondary
            self.dropdown_bg = colors.inputbg
            self.dropdown_hover_bg = colors.secondary
        else:
            self.menu_hover_bg = colors.light
            self.menu_active_bg = colors.border
            self.dropdown_bg = 'white'
            self.dropdown_hover_bg = colors.light

    def _create_menu_item(self, label: str, items_creator: Callable) -> None:
        """Create a menu bar item button."""
        btn = tk.Label(
            self.menu_bar_frame,
            text=label,
            bg=self.menu_bg,
            fg=self.menu_fg,
            padx=10,
            pady=4,
            cursor='hand2'
        )
        btn.pack(side='left')

        # Store reference to menu items creator
        btn.items_creator = items_creator  # type: ignore
        btn.menu_label = label  # type: ignore

        # Bind events
        btn.bind("<Enter>", lambda e, b=btn: self._on_menu_hover(b, True))
        btn.bind("<Leave>", lambda e, b=btn: self._on_menu_hover(b, False))
        btn.bind("<Button-1>", lambda e, b=btn: self._toggle_menu(b))

        self.menu_buttons.append(btn)

    def _on_menu_hover(self, btn: tk.Label, entering: bool) -> None:
        """Handle menu button hover effects with Windows-style auto-switching."""
        if entering:
            # If we're in "armed" mode (a menu was opened), switch menus on hover
            if self.menu_armed and self.active_menu != btn:
                self._show_menu(btn)
            elif self.active_menu != btn:
                # Just highlight if not armed
                btn.configure(bg=self.menu_hover_bg)
        else:
            # Only remove highlight if this isn't the active menu
            if self.active_menu != btn:
                btn.configure(bg=self.menu_bg)

    def _toggle_menu(self, btn: tk.Label) -> None:
        """Toggle a dropdown menu."""
        if self.active_menu == btn:
            self._fully_close_menu()
        else:
            self._show_menu(btn)

    def _show_menu(self, btn: tk.Label) -> None:
        """Show a custom dropdown menu below the button."""
        # Close any existing dropdown first
        if self.current_dropdown:
            try:
                self.current_dropdown.destroy()
            except tk.TclError:
                pass
            self.current_dropdown = None

        # Reset previous active button
        if self.active_menu and self.active_menu != btn:
            self.active_menu.configure(bg=self.menu_bg)

        # Set new active menu
        self.active_menu = btn
        self.menu_armed = True
        btn.configure(bg=self.menu_active_bg)

        # Create dropdown Toplevel
        dropdown = tk.Toplevel(self)  # type: ignore
        dropdown.withdraw()  # Hide until positioned
        dropdown.overrideredirect(True)  # Remove window decorations
        dropdown.configure(bg=self.dropdown_bg)

        # Add a thin border frame
        border_frame = tk.Frame(dropdown, bg='#666666', padx=1, pady=1)
        border_frame.pack(fill='both', expand=True)

        inner_frame = tk.Frame(border_frame, bg=self.dropdown_bg)
        inner_frame.pack(fill='both', expand=True)

        # Get menu items and create labels
        items = btn.items_creator()  # type: ignore
        for item in items:
            if item is None:
                # Separator
                sep = tk.Frame(inner_frame, height=1, bg='#666666')
                sep.pack(fill='x', padx=5, pady=3)
            elif len(item) == 2 and isinstance(item[1], list):
                # Submenu: (label, submenu_items_list)
                label_text, submenu_items = item
                self._create_submenu_entry(inner_frame, label_text, submenu_items, dropdown)
            else:
                label_text, command, accelerator, var = item
                self._create_menu_entry(inner_frame, label_text, command, accelerator, var, dropdown)

        # Store reference
        self.current_dropdown = dropdown

        # Position and show
        x = btn.winfo_rootx()
        y = btn.winfo_rooty() + btn.winfo_height()
        dropdown.geometry(f"+{x}+{y}")

        # Keep dropdown on top without stealing focus from main window
        dropdown.wm_attributes("-topmost", True)
        dropdown.deiconify()

        # Bind to detect clicks outside the dropdown
        self.bind_all("<Button-1>", self._on_global_click)  # type: ignore

    def _create_menu_entry(
        self,
        parent: tk.Frame,
        label: str,
        command: Callable,
        accelerator: Optional[str],
        var: Optional[tk.BooleanVar],
        dropdown: tk.Toplevel
    ) -> None:
        """Create a single menu entry."""
        frame = tk.Frame(parent, bg=self.dropdown_bg)
        frame.pack(fill='x')

        # Checkbox indicator for checkbutton items
        if var is not None:
            check_text = "✓" if var.get() else "  "
            check_label = tk.Label(
                frame, text=check_text, bg=self.dropdown_bg, fg=self.dropdown_fg,
                font=_get_menu_font(), padx=5
            )
            check_label.pack(side='left')
            frame.check_label = check_label  # type: ignore
            frame.var = var  # type: ignore

        # Main label
        lbl = tk.Label(
            frame,
            text=label,
            bg=self.dropdown_bg,
            fg=self.dropdown_fg,
            padx=10 if var is None else 5,
            pady=4,
            anchor='w',
            font=_get_menu_font()
        )
        lbl.pack(side='left', fill='x', expand=True)

        # Accelerator
        if accelerator:
            acc_lbl = tk.Label(
                frame,
                text=accelerator,
                bg=self.dropdown_bg,
                fg='#888888',
                padx=15,
                pady=4,
                anchor='e',
                font=_get_menu_font()
            )
            acc_lbl.pack(side='right')
            frame.acc_label = acc_lbl  # type: ignore

        # Store command
        frame.command = command  # type: ignore

        # Bind hover effects to all widgets in frame
        def on_enter(e):
            frame.configure(bg=self.dropdown_hover_bg)
            for child in frame.winfo_children():
                child.configure(bg=self.dropdown_hover_bg)  # type: ignore

        def on_leave(e):
            frame.configure(bg=self.dropdown_bg)
            for child in frame.winfo_children():
                child.configure(bg=self.dropdown_bg)  # type: ignore

        def on_click(e):
            self._fully_close_menu()
            if var is not None:
                # Toggle the variable for checkbutton items
                var.set(not var.get())
            command()

        frame.bind("<Enter>", on_enter)
        frame.bind("<Leave>", on_leave)
        frame.bind("<Button-1>", on_click)
        for child in frame.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)
            child.bind("<Button-1>", on_click)

    def _create_submenu_entry(
        self,
        parent: tk.Frame,
        label: str,
        submenu_items: List,
        parent_dropdown: tk.Toplevel
    ) -> None:
        """Create a submenu entry with arrow indicator."""
        frame = tk.Frame(parent, bg=self.dropdown_bg)
        frame.pack(fill='x')

        # Main label
        lbl = tk.Label(
            frame,
            text=label,
            bg=self.dropdown_bg,
            fg=self.dropdown_fg,
            padx=10,
            pady=4,
            anchor='w',
            font=_get_menu_font()
        )
        lbl.pack(side='left', fill='x', expand=True)

        # Arrow indicator for submenu
        arrow_lbl = tk.Label(
            frame,
            text="►",
            bg=self.dropdown_bg,
            fg='#888888',
            padx=10,
            pady=4,
            anchor='e',
            font=_get_menu_font()
        )
        arrow_lbl.pack(side='right')

        # Store submenu reference
        frame.submenu_dropdown = None  # type: ignore
        frame.submenu_items = submenu_items  # type: ignore

        def on_enter(e):
            frame.configure(bg=self.dropdown_hover_bg)
            for child in frame.winfo_children():
                child.configure(bg=self.dropdown_hover_bg)  # type: ignore
            # Show submenu after short delay
            frame.after(150, lambda: self._show_submenu(frame, parent_dropdown))

        def on_leave(e):
            # Check if mouse moved to submenu
            frame.after(100, lambda: self._check_hide_submenu(frame, e))

        frame.bind("<Enter>", on_enter)
        frame.bind("<Leave>", on_leave)
        for child in frame.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)

    def _show_submenu(self, parent_frame: tk.Frame, parent_dropdown: tk.Toplevel) -> None:
        """Show a submenu to the right of the parent item."""
        # Close any existing submenu from other items
        if hasattr(self, 'current_submenu') and self.current_submenu:
            try:
                self.current_submenu.destroy()
            except tk.TclError:
                pass
            self.current_submenu = None

        submenu_items = parent_frame.submenu_items  # type: ignore

        # Create submenu Toplevel
        submenu = tk.Toplevel(self)  # type: ignore
        submenu.withdraw()
        submenu.overrideredirect(True)
        submenu.configure(bg=self.dropdown_bg)

        # Add border
        border_frame = tk.Frame(submenu, bg='#666666', padx=1, pady=1)
        border_frame.pack(fill='both', expand=True)

        inner_frame = tk.Frame(border_frame, bg=self.dropdown_bg)
        inner_frame.pack(fill='both', expand=True)

        # Create submenu items
        for item in submenu_items:
            if item is None:
                sep = tk.Frame(inner_frame, height=1, bg='#666666')
                sep.pack(fill='x', padx=5, pady=3)
            else:
                label_text, command, accelerator, var = item
                self._create_submenu_item_entry(inner_frame, label_text, command, accelerator, var, submenu)

        # Store reference
        parent_frame.submenu_dropdown = submenu  # type: ignore
        self.current_submenu = submenu

        # Position to the right of parent
        x = parent_dropdown.winfo_rootx() + parent_dropdown.winfo_width() - 2
        y = parent_frame.winfo_rooty()
        submenu.geometry(f"+{x}+{y}")
        submenu.wm_attributes("-topmost", True)
        submenu.deiconify()

    def _create_submenu_item_entry(
        self,
        parent: tk.Frame,
        label: str,
        command: Callable,
        accelerator: Optional[str],
        var: Optional[tk.BooleanVar],
        submenu: tk.Toplevel
    ) -> None:
        """Create a single submenu item entry with theme checkmark."""
        frame = tk.Frame(parent, bg=self.dropdown_bg)
        frame.pack(fill='x')

        # Check if this is a theme item - show checkmark if current
        theme_name = label.strip().lower()
        is_current = hasattr(self, 'current_theme') and self.current_theme == theme_name
        check_text = "✓" if is_current else "  "
        check_label = tk.Label(
            frame, text=check_text, bg=self.dropdown_bg, fg=self.dropdown_fg,
            font=_get_menu_font(), padx=5
        )
        check_label.pack(side='left')

        # Main label
        lbl = tk.Label(
            frame,
            text=label,
            bg=self.dropdown_bg,
            fg=self.dropdown_fg,
            padx=5,
            pady=4,
            anchor='w',
            font=_get_menu_font()
        )
        lbl.pack(side='left', fill='x', expand=True)

        def on_enter(e):
            frame.configure(bg=self.dropdown_hover_bg)
            for child in frame.winfo_children():
                child.configure(bg=self.dropdown_hover_bg)  # type: ignore

        def on_leave(e):
            frame.configure(bg=self.dropdown_bg)
            for child in frame.winfo_children():
                child.configure(bg=self.dropdown_bg)  # type: ignore

        def on_click(e):
            self._fully_close_menu()
            command()

        frame.bind("<Enter>", on_enter)
        frame.bind("<Leave>", on_leave)
        frame.bind("<Button-1>", on_click)
        for child in frame.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)
            child.bind("<Button-1>", on_click)

    def _check_hide_submenu(self, parent_frame: tk.Frame, event: tk.Event) -> None:
        """Check if submenu should be hidden when leaving parent item."""
        submenu = parent_frame.submenu_dropdown  # type: ignore
        if not submenu:
            return

        try:
            # Get mouse position
            mouse_x = self.winfo_pointerx()
            mouse_y = self.winfo_pointery()

            # Check if mouse is over submenu
            sx1 = submenu.winfo_rootx()
            sy1 = submenu.winfo_rooty()
            sx2 = sx1 + submenu.winfo_width()
            sy2 = sy1 + submenu.winfo_height()

            # Check if mouse is over parent frame
            px1 = parent_frame.winfo_rootx()
            py1 = parent_frame.winfo_rooty()
            px2 = px1 + parent_frame.winfo_width()
            py2 = py1 + parent_frame.winfo_height()

            in_submenu = sx1 <= mouse_x <= sx2 and sy1 <= mouse_y <= sy2
            in_parent = px1 <= mouse_x <= px2 and py1 <= mouse_y <= py2

            if not in_submenu and not in_parent:
                # Reset highlight
                parent_frame.configure(bg=self.dropdown_bg)
                for child in parent_frame.winfo_children():
                    child.configure(bg=self.dropdown_bg)  # type: ignore
                # Close submenu
                submenu.destroy()
                parent_frame.submenu_dropdown = None  # type: ignore
                if hasattr(self, 'current_submenu') and self.current_submenu == submenu:
                    self.current_submenu = None
        except tk.TclError:
            pass

    def _on_global_click(self, event: tk.Event) -> None:
        """Handle clicks anywhere to close menu if clicking outside."""
        if not self.current_dropdown:
            return

        # Check if click was on a menu button
        for btn in self.menu_buttons:
            if event.widget == btn:
                return  # Let the button's own handler deal with it

        # Check if click was inside the dropdown
        try:
            click_x = event.x_root
            click_y = event.y_root
            dx1 = self.current_dropdown.winfo_rootx()
            dy1 = self.current_dropdown.winfo_rooty()
            dx2 = dx1 + self.current_dropdown.winfo_width()
            dy2 = dy1 + self.current_dropdown.winfo_height()
            if dx1 <= click_x <= dx2 and dy1 <= click_y <= dy2:
                return  # Click was inside dropdown

            # Check if click was inside a submenu
            if hasattr(self, 'current_submenu') and self.current_submenu:
                sx1 = self.current_submenu.winfo_rootx()
                sy1 = self.current_submenu.winfo_rooty()
                sx2 = sx1 + self.current_submenu.winfo_width()
                sy2 = sy1 + self.current_submenu.winfo_height()
                if sx1 <= click_x <= sx2 and sy1 <= click_y <= sy2:
                    return  # Click was inside submenu
        except tk.TclError:
            pass

        # Click was outside - close menu
        self._fully_close_menu()

    def _fully_close_menu(self, event=None) -> None:
        """Completely close the menu system."""
        # Unbind global click handler
        try:
            self.unbind_all("<Button-1>")  # type: ignore
        except tk.TclError:
            pass

        # Close any submenu first
        if hasattr(self, 'current_submenu') and self.current_submenu:
            try:
                self.current_submenu.destroy()
            except tk.TclError:
                pass
            self.current_submenu = None

        if self.current_dropdown:
            try:
                self.current_dropdown.destroy()
            except tk.TclError:
                pass
            self.current_dropdown = None

        if self.active_menu:
            self.active_menu.configure(bg=self.menu_bg)
            self.active_menu = None

        self.menu_armed = False

    # Menu item definitions - return list of (label, command, accelerator, variable)
    # None means separator
    # For submenus: (label, submenu_items_list, None, None) where submenu_items_list is a list

    def _get_file_menu_items(self) -> List[Optional[Tuple[str, Callable, Optional[str], Optional[tk.BooleanVar]]]]:
        """Get File menu items."""
        return [
            ("Open Folder...", self.browse_folder, "Ctrl+O", None),
            None,  # Separator
            ("Exit", self.on_closing, None, None),
        ]

    def _get_view_menu_items(self) -> List:
        """Get View menu items including theme submenus."""
        # Build theme submenu items
        light_theme_items = [(t.title(), lambda t=t: self.switch_theme(t), None, None) for t in self.LIGHT_THEMES]
        dark_theme_items = [(t.title(), lambda t=t: self.switch_theme(t), None, None) for t in self.DARK_THEMES]

        return [
            ("Row Colors", self.toggle_row_colors, None, self.row_colors),
            None,  # Separator
            ("Light Themes", light_theme_items),  # Submenu
            ("Dark Themes", dark_theme_items),  # Submenu
        ]

    def _get_tools_menu_items(self) -> List[Optional[Tuple[str, Callable, Optional[str], Optional[tk.BooleanVar]]]]:
        """Get Tools menu items."""
        return [
            ("Rescan", self.scan, "Ctrl+R", None),
            None,  # Separator
            ("Check for Updates...", self.check_for_updates, None, None),
        ]

    def _get_help_menu_items(self) -> List[Optional[Tuple[str, Callable, Optional[str], Optional[tk.BooleanVar]]]]:
        """Get Help menu items."""
        return [
            ("About", self.show_about_dialog, None, None),
        ]
