"""Theme management mixin for ROM Duplicate Manager.

This module contains all theme-related methods including dark/light mode
switching using ttkbootstrap themes.
"""

import tkinter as tk
import tkinter.font as tkfont
from typing import Any


class ThemeMixin:
    """Mixin class providing theme management functionality using ttkbootstrap."""

    def switch_theme(self, theme_name: str) -> None:
        """Switch to a specific ttkbootstrap theme.

        Args:
            theme_name: Name of the ttkbootstrap theme to apply
        """
        if theme_name not in self.ALL_THEMES:
            return

        self.current_theme = theme_name
        self.style.theme_use(theme_name)

        # Update dark_mode_enabled based on theme type
        is_dark = theme_name in self.DARK_THEMES
        self.dark_mode_enabled.set(is_dark)

        # Update all theme-dependent elements
        self._update_theme_colors()
        self._apply_legacy_widget_theme()
        self.update_tag_colors()
        self.apply_display_settings()
        self._update_menu_theme()
        self.save_settings()

    def toggle_dark_mode(self) -> None:
        """Toggle between dark and light themes and save the preference."""
        # Find a matching theme in the opposite category
        if self.dark_mode_enabled.get():
            # Switching to dark - use current dark theme or default
            if self.current_theme not in self.DARK_THEMES:
                self.switch_theme(self.DARK_THEMES[0])
        else:
            # Switching to light - use current light theme or default
            if self.current_theme not in self.LIGHT_THEMES:
                self.switch_theme(self.LIGHT_THEMES[0])

    def _update_theme_colors(self) -> None:
        """Update color variables from the current ttkbootstrap theme."""
        colors = self.style.colors

        # Get semantic colors from ttkbootstrap theme
        self.primary = colors.primary
        self.success = colors.success
        self.info = colors.info
        self.warning = colors.warning
        self.danger = colors.danger

        # Get background/foreground colors
        self.dark_bg = colors.bg
        self.dark_fg = colors.fg
        self.light_bg = colors.bg
        self.selection_bg = colors.info
        self.selection_fg = colors.selectfg

    def apply_dark_mode(self) -> None:
        """Apply dark theme styling (uses current theme, just updates widgets)."""
        self._update_theme_colors()
        self._apply_legacy_widget_theme()
        self.update_tag_colors()
        self.apply_display_settings()
        self._update_menu_theme()

    def apply_light_mode(self) -> None:
        """Apply light theme styling (uses current theme, just updates widgets)."""
        self._update_theme_colors()
        self._apply_legacy_widget_theme()
        self.update_tag_colors()
        self.apply_display_settings()
        self._update_menu_theme()

    def _apply_legacy_widget_theme(self) -> None:
        """Apply theme to legacy tk widgets (Entry, Button, Checkbutton, etc.)."""
        colors = self.style.colors
        is_dark = self.dark_mode_enabled.get()

        for widget in self.winfo_children():
            self._apply_legacy_widget_theme_recursive(widget, colors, is_dark)

    def _apply_legacy_widget_theme_recursive(self, widget: tk.Misc, colors: Any, is_dark: bool) -> None:
        """Recursively apply theme styling to legacy widgets."""
        widget_type = widget.winfo_class()
        w: Any = widget

        try:
            if widget_type in ('Frame', 'Labelframe'):
                w.configure(bg=colors.bg)
            elif widget_type == 'Label':
                w.configure(bg=colors.bg, fg=colors.fg)
            elif widget_type == 'Button':
                w.configure(
                    bg=colors.secondary if is_dark else colors.light,
                    fg=colors.fg,
                    activebackground=colors.info,
                    activeforeground=colors.selectfg,
                    highlightbackground=colors.bg
                )
            elif widget_type == 'Entry':
                w.configure(
                    bg=colors.inputbg,
                    fg=colors.inputfg,
                    insertbackground=colors.fg,
                    selectbackground=colors.selectbg,
                    selectforeground=colors.selectfg,
                    highlightbackground=colors.bg,
                    highlightcolor=colors.primary
                )
            elif widget_type == 'Checkbutton':
                w.configure(
                    bg=colors.bg,
                    fg=colors.fg,
                    activebackground=colors.bg,
                    activeforeground=colors.fg,
                    selectcolor=colors.inputbg,
                    highlightbackground=colors.bg
                )
        except tk.TclError:
            pass  # Some widgets may not support all properties

        for child in widget.winfo_children():
            self._apply_legacy_widget_theme_recursive(child, colors, is_dark)

    def _update_menu_theme(self) -> None:
        """Update menu bar theme colors based on current theme."""
        if not hasattr(self, 'menu_bar_frame'):
            return

        # Update color variables using the shared method from MenuBarMixin
        is_dark = self.dark_mode_enabled.get()
        if hasattr(self, '_update_menu_colors'):
            self._update_menu_colors(is_dark)

        # Apply to menu bar frame
        self.menu_bar_frame.configure(bg=self.menu_bg)

        # Apply to all menu buttons
        if hasattr(self, 'menu_buttons'):
            for btn in self.menu_buttons:
                if not hasattr(self, 'active_menu') or btn != self.active_menu:
                    btn.configure(bg=self.menu_bg, fg=self.menu_fg)

        # Close any open dropdown (it will reopen with new colors if needed)
        if hasattr(self, '_fully_close_menu'):
            self._fully_close_menu()

    def update_tag_colors(self) -> None:
        """Update treeview tag colors based on current theme."""
        is_dark = self.dark_mode_enabled.get()
        colors = self.style.colors

        # Create strikethrough font for items marked for deletion
        default_font = tkfont.nametofont('TkDefaultFont')
        strikethrough_font = tkfont.Font(
            family=default_font.cget('family'),
            size=default_font.cget('size'),
            overstrike=True
        )

        # Use semantic colors from ttkbootstrap
        # filtered tag configured first so it takes priority when combined with other tags
        self.tree.tag_configure('filtered', background=colors.warning, foreground='black')
        self.tree.tag_configure('to_remove', background=colors.danger, foreground='white', font=strikethrough_font)
        self.tree.tag_configure('base', background=colors.success, foreground='white')

        if is_dark:
            self.tree.tag_configure('group', background=colors.dark, foreground=colors.fg)
        else:
            self.tree.tag_configure('group', background=colors.light, foreground=colors.fg)

    def toggle_row_colors(self) -> None:
        """Toggle alternating row colors and save preference."""
        self.apply_display_settings()
        self.save_settings()

    def apply_display_settings(self) -> None:
        """Apply current display settings (row colors, themes, etc.)."""
        if self.row_colors.get():
            colors = self.style.colors
            is_dark = self.dark_mode_enabled.get()

            if is_dark:
                # Dark mode alternating colors - slightly different shades
                self.tree.tag_configure('oddrow', background=colors.bg)
                self.tree.tag_configure('evenrow', background=colors.dark)
            else:
                # Light mode alternating colors
                self.tree.tag_configure('oddrow', background='white')
                self.tree.tag_configure('evenrow', background=colors.light)

            self.refresh_row_colors()
        else:
            # Remove row coloring
            self.tree.tag_configure('oddrow', background='')
            self.tree.tag_configure('evenrow', background='')

    def refresh_row_colors(self) -> None:
        """Refresh alternating row colors for all visible items."""
        if not self.row_colors.get():
            return

        row_index = 0
        for item in self.tree.get_children():
            # Apply alternating colors
            tag = 'evenrow' if row_index % 2 == 0 else 'oddrow'

            # Get existing tags and add row color
            current_tags = list(self.tree.item(item, 'tags'))
            # Remove old row tags
            current_tags = [t for t in current_tags if t not in ('oddrow', 'evenrow')]
            current_tags.append(tag)
            self.tree.item(item, tags=current_tags)

            row_index += 1

            # Process children (file items in groups)
            for child in self.tree.get_children(item):
                tag = 'evenrow' if row_index % 2 == 0 else 'oddrow'
                child_tags = list(self.tree.item(child, 'tags'))
                child_tags = [t for t in child_tags if t not in ('oddrow', 'evenrow')]
                child_tags.append(tag)
                self.tree.item(child, tags=child_tags)
                row_index += 1
