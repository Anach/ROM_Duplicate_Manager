"""File list management mixin for ROM Duplicate Manager.

This module contains all file tree/list view management methods.
"""

import os
import subprocess
import tkinter as tk
from tkinter import messagebox, font as tkfont
from tkinter import ttk
import ttkbootstrap as ttk_bs
import fnmatch
import re
from typing import List, Optional, Any
from send2trash import send2trash


class FileListMixin:
    """Mixin class providing file list tree management functionality."""

    def populate_tree(self) -> None:
        """Populate the tree view with duplicate and unique file groups.

        Clears the existing tree and rebuilds it with current scan results,
        applying smart selection if enabled and setting up proper visual styling.
        """
        self.tree.delete(*self.tree.get_children())

        # Add duplicate groups
        for base_name in sorted(self.duplicates.keys()):
            files = self.duplicates[base_name]
            parent_id = self.tree.insert('', 'end', text=base_name, open=True, tags=('duplicate_group',))
            base_file = self.get_base_file(files)
            sorted_files = sorted(files, key=self.get_file_priority)

            for f in sorted_files:
                child_id = self.tree.insert(parent_id, 'end', text=os.path.basename(f), values=(f,))
                if self.smart_select.get():
                    if f == base_file:
                        self.tree.item(child_id, tags=('base',))
                    else:
                        self.tree.item(child_id, tags=('to_remove',))

        # Add unique file groups
        for base_name in sorted(self.non_duplicates.keys()):
            files = self.non_duplicates[base_name]
            parent_id = self.tree.insert('', 'end', text=base_name, open=False, tags=('unique_group',))
            for f in files:
                self.tree.insert(parent_id, 'end', text=os.path.basename(f), values=(f,))

        self.update_tag_colors()
        self.refresh_row_colors()
        self.apply_filter()

        # Reset sort to default (Filename ascending) on each scan
        self.sort_column = '#0'
        self.sort_reverse = False
        self.user_sorted = False
        self.sort_tree('#0', False, user_initiated=False)

    def toggle_item_status(self, item: str) -> None:
        """Toggle the status of a tree item between keep/delete states.

        Cycles between unmarked -> to_remove -> base (keep) states while
        preserving row coloring and filter tags.

        Args:
            item: Tree item ID to toggle
        """
        if not item:
            return
        parent = self.tree.parent(item)
        if not parent:
            return

        tags = list(self.tree.item(item, 'tags'))
        row_tag = next((t for t in tags if t in ('oddrow', 'evenrow')), None)
        filtered_tag = 'filtered' if 'filtered' in tags else None

        # Toggle status logic
        if 'base' in tags:
            tags = ['to_remove', 'manual']
        elif 'to_remove' in tags:
            tags = ['base', 'manual']
        else:
            # Default unmarked files to deletion
            tags = ['to_remove', 'manual']

        # Preserve display tags
        if row_tag:
            tags.append(row_tag)
        if filtered_tag:
            tags.append(filtered_tag)

        self.tree.item(item, tags=tuple(tags))
        self.update_status_label()

    def on_tree_double_click(self, event: tk.Event) -> str:
        """Handle double-click to toggle item status.

        Args:
            event: Tkinter mouse event

        Returns:
            "break" to prevent further event propagation
        """
        item = self.tree.identify_row(event.y)
        self.toggle_item_status(item)
        return "break"

    def on_space_press(self, event: tk.Event) -> str:
        """Handle spacebar press to toggle status of all selected items.

        Args:
            event: Tkinter keyboard event

        Returns:
            "break" to prevent further event propagation
        """
        selected = self.tree.selection()
        for item in selected:
            self.toggle_item_status(item)
        return "break"

    def show_context_menu(self, event: tk.Event) -> None:
        """Display the right-click context menu for file items.

        Automatically selects the right-clicked item and applies current theme
        to the context menu appearance.

        Args:
            event: Tkinter mouse event
        """
        item = self.tree.identify_row(event.y)
        if item:
            # Select the item if not already selected
            if item not in self.tree.selection():
                self.tree.selection_set(item)

            # Only show menu for file items (items with parents)
            if self.tree.parent(item):
                # Apply current theme to menu
                is_dark = self.dark_mode_enabled.get()
                bg = self.dark_bg if is_dark else 'white'
                fg = self.dark_fg if is_dark else 'black'
                self.context_menu.configure(
                    bg=bg, fg=fg,
                    activebackground=self.selection_bg,
                    activeforeground='white'
                )
                self.context_menu.post(event.x_root, event.y_root)

    def open_file_location(self) -> None:
        """Open the file location of the selected item in Windows Explorer."""
        selected = self.tree.selection()
        if not selected:
            return

        path = self.tree.item(selected[0], 'values')[0]
        path = os.path.normpath(path)
        if os.path.exists(path):
            try:
                subprocess.run(['explorer', '/select,', path], check=False)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file location: {e}")

    def open_file(self) -> None:
        """Open the selected file with its default application."""
        selected = self.tree.selection()
        if not selected:
            return

        path = self.tree.item(selected[0], 'values')[0]
        path = os.path.normpath(path)
        if os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")

    def toggle_selected_status(self) -> None:
        """Toggle keep/delete status of all currently selected items."""
        selected = self.tree.selection()
        for item in selected:
            self.toggle_item_status(item)
        self.update_tag_colors()

    def mark_selected_keep(self) -> None:
        """Mark all selected file items to be kept (not deleted)."""
        for item in self.tree.selection():
            if not self.tree.parent(item):
                continue

            tags = list(self.tree.item(item, 'tags'))
            tags = [t for t in tags if t not in ('base', 'to_remove')]
            tags.extend(['base', 'manual'])
            self.tree.item(item, tags=tuple(tags))

        self.update_tag_colors()
        self.update_status_label()

    def mark_selected_delete(self) -> None:
        """Mark all selected file items for deletion."""
        for item in self.tree.selection():
            if not self.tree.parent(item):
                continue

            tags = list(self.tree.item(item, 'tags'))
            tags = [t for t in tags if t not in ('base', 'to_remove')]
            tags.extend(['to_remove', 'manual'])
            self.tree.item(item, tags=tuple(tags))

        self.update_tag_colors()
        self.update_status_label()

    def on_filter_change(self, *args) -> None:
        """Handle filter text or search options change.

        Args:
            *args: Variable arguments from tkinter trace callback
        """
        self.apply_filter()

    def on_regex_toggle(self) -> None:
        """Handle regex checkbox toggle with visual feedback.

        Changes the filter entry style to indicate regex mode
        and reapplies the current filter with the new mode.
        """
        # For ttk.Entry, we use a custom style to change background
        if self.use_regex.get():
            # Create a regex-mode style with a subtle tint
            # Use light blue tint for light themes, muted blue for dark themes
            is_dark = self.dark_mode_enabled.get()
            if is_dark:
                regex_bg = '#2a3f5f'  # Muted dark blue for dark themes
            else:
                regex_bg = '#e8f0fe'  # Light blue tint for light themes
            self.style.configure('Regex.TEntry', fieldbackground=regex_bg)
            self.filter_entry.configure(style='Regex.TEntry')
        else:
            # Reset to default entry style
            self.filter_entry.configure(style='TEntry')

        self.apply_filter()
        self.save_settings()

    def clear_filter(self) -> None:
        """Clear the current filter text and reset the view."""
        self.filter_text.set('')
        self.apply_filter()

    def check_match(self, pattern: str, filename: str, filepath: Optional[str] = None) -> bool:
        """Check if a pattern matches against filename or filepath.

        Supports both wildcard patterns and regular expressions based on current settings.

        Args:
            pattern: The search pattern to match against
            filename: The filename to check
            filepath: Optional full file path to check (if search_in_path enabled)

        Returns:
            True if the pattern matches, False otherwise
        """
        if not pattern:
            return False

        # Determine what text to match against
        if self.search_in_path.get() and filepath:
            text_to_match = filepath.replace(" - Copy", "")
        else:
            text_to_match = filename.replace(" - Copy", "")

        if self.use_regex.get():
            try:
                return re.search(pattern, text_to_match, re.IGNORECASE) is not None
            except re.error:
                return False
        else:
            # Support wildcards * and ? in non-regex mode
            if '*' in pattern or '?' in pattern:
                return fnmatch.fnmatch(text_to_match.lower(), pattern.lower())
            else:
                return pattern.lower() in text_to_match.lower()

    def mark_filtered_keep(self) -> None:
        """Mark all files matching the current filter to be kept.

        Applies the 'base' (keep) tag to all files that match the current filter pattern.
        """
        text = self.filter_text.get()
        if not text:
            return

        for parent in self.tree.get_children():
            for child in self.tree.get_children(parent):
                filename = self.tree.item(child, 'text')
                filepath = self.tree.item(child, 'values')[0] if self.tree.item(child, 'values') else None

                if self.check_match(text, filename, filepath):
                    tags = list(self.tree.item(child, 'tags'))
                    tags = [t for t in tags if t not in ('base', 'to_remove')]
                    tags.extend(['base', 'manual'])
                    self.tree.item(child, tags=tuple(tags))

        self.update_tag_colors()
        self.update_status_label()

    def mark_filtered_delete(self) -> None:
        """Mark all files matching the current filter for deletion.

        Applies the 'to_remove' (delete) tag to all files that match the current filter pattern.
        """
        text = self.filter_text.get()
        if not text:
            return

        for parent in self.tree.get_children():
            for child in self.tree.get_children(parent):
                filename = self.tree.item(child, 'text')
                filepath = self.tree.item(child, 'values')[0] if self.tree.item(child, 'values') else None

                if self.check_match(text, filename, filepath):
                    tags = list(self.tree.item(child, 'tags'))
                    tags = [t for t in tags if t not in ('base', 'to_remove')]
                    tags.extend(['to_remove', 'manual'])
                    self.tree.item(child, tags=tuple(tags))

        self.update_tag_colors()
        self.update_status_label()

    def reset_marks(self) -> None:
        """Reset all manual keep/delete marks and reapply smart selection if enabled."""
        for parent in self.tree.get_children():
            for child in self.tree.get_children(parent):
                tags = list(self.tree.item(child, 'tags'))
                tags = [t for t in tags if t not in ('base', 'to_remove', 'manual')]
                self.tree.item(child, tags=tuple(tags))

        if self.smart_select.get():
            self.apply_base_suggestions()
        else:
            self.update_tag_colors()
        self.update_status_label()

    def apply_filter(self) -> None:
        """Apply the current filter to the tree view.

        Shows/hides tree items based on the current filter pattern and
        updates visual indicators for matching items.
        """
        text = self.filter_text.get()
        is_empty = not text

        for parent in self.tree.get_children():
            has_matching_child = False

            for child in self.tree.get_children(parent):
                filename = self.tree.item(child, 'text')
                filepath = self.tree.item(child, 'values')[0] if self.tree.item(child, 'values') else None
                matches_filter = self.check_match(text, filename, filepath)

                if matches_filter or is_empty:
                    has_matching_child = True

                # Update filtered tag - put filtered first so it overrides other tags
                current_tags = list(self.tree.item(child, 'tags'))
                if 'filtered' in current_tags:
                    current_tags.remove('filtered')
                if matches_filter:
                    current_tags.insert(0, 'filtered')
                self.tree.item(child, tags=tuple(current_tags))

            # Expand/collapse parent based on matches
            if not is_empty and not has_matching_child:
                self.tree.item(parent, open=False)
            else:
                self.tree.item(parent, open=True)

        self.update_tag_colors()

    def sort_tree(self, col: str, reverse: bool, user_initiated: bool = True) -> None:
        """Sort treeview content when a column header is clicked.

        Sorts both parent groups and children within each group,
        maintaining the hierarchical structure while enabling easy organization.
        Duplicate groups are always shown at the top, followed by unique groups.
        Marked items (to_remove/base) are always kept at the top within each group.

        Args:
            col: Column identifier to sort by ('#0' for filename, 'path' for full path)
            reverse: Whether to sort in reverse order
            user_initiated: Whether this sort was triggered by user clicking a column header
        """
        def get_sort_text(item_id):
            """Get the text value for sorting an item."""
            if col == '#0':
                return self.tree.item(item_id, 'text').lower()
            else:
                return self.tree.set(item_id, col).lower()

        def get_child_sort_key(item_id):
            """Get sort key for child items - marked items always first."""
            tags = self.tree.item(item_id, 'tags')
            # Marked items (to_remove or base) get priority 0, unmarked get 1
            is_marked = 'to_remove' in tags or 'base' in tags
            priority = 0 if is_marked else 1
            text = get_sort_text(item_id)
            return (priority, text)

        # Get all top-level items (groups) and separate by type
        duplicate_groups = []
        unique_groups = []
        for k in self.tree.get_children(''):
            tags = self.tree.item(k, 'tags')
            text = self.tree.item(k, 'text')
            if 'duplicate_group' in tags:
                duplicate_groups.append((text, k))
            else:
                unique_groups.append((text, k))

        # Sort each section alphabetically by name
        duplicate_groups.sort(key=lambda t: t[0].lower(), reverse=reverse)
        unique_groups.sort(key=lambda t: t[0].lower(), reverse=reverse)

        # Combine: duplicates first, then uniques
        all_groups = duplicate_groups + unique_groups

        # Rearrange groups in the tree
        for index, (val, k) in enumerate(all_groups):
            self.tree.move(k, '', index)

            # Sort children within each group
            children = list(self.tree.get_children(k))

            # Sort by priority first (marked=0, unmarked=1), then by text
            # When reverse is True, we want text reversed but marked items still on top
            if reverse:
                # Separate marked and unmarked items
                marked = [c for c in children if 'to_remove' in self.tree.item(c, 'tags') or 'base' in self.tree.item(c, 'tags')]
                unmarked = [c for c in children if c not in marked]

                # Sort each subgroup by text in reverse order
                marked.sort(key=get_sort_text, reverse=True)
                unmarked.sort(key=get_sort_text, reverse=True)

                children = marked + unmarked
            else:
                # Normal sort: marked first, then alphabetically
                children.sort(key=get_child_sort_key)

            for c_index, c_id in enumerate(children):
                self.tree.move(c_id, k, c_index)

        # Update sort state
        self.sort_column = col
        self.sort_reverse = reverse
        if user_initiated:
            self.user_sorted = True  # Mark that user has explicitly sorted

        # Update headings with sort indicators
        indicator_up = ' ▲'
        indicator_down = ' ▼'

        # Reset both headings first (remove indicators)
        self.tree.heading('#0', text='Filename', anchor='w', command=lambda: self.sort_tree('#0', False))
        self.tree.heading('path', text='Full Path', anchor='w', command=lambda: self.sort_tree('path', False))

        # Add indicator to the sorted column
        if col == '#0':
            indicator = indicator_up if not reverse else indicator_down
            self.tree.heading('#0', text=f'Filename{indicator}', anchor='w', command=lambda: self.sort_tree('#0', not reverse))
        else:
            indicator = indicator_up if not reverse else indicator_down
            self.tree.heading('path', text=f'Full Path{indicator}', anchor='w', command=lambda: self.sort_tree('path', not reverse))

        self.refresh_row_colors()

    def delete_selected(self) -> None:
        """Delete selected or marked files with progress indication.

        Handles deletion of both regular files and orphaned images with user confirmation,
        progress indication, and proper cleanup of the UI afterward.
        """
        selected = self.tree.selection()
        file_items = [item for item in selected if self.tree.parent(item)]
        if not file_items:
            # If nothing selected, use all marked items
            for item in self.tree.tag_has('to_remove'):
                file_items.append(item)

        orphaned_images = []
        if self.scan_images.get():
            # Calculate which images will become orphaned after deletion
            all_files = []
            for paths in self.duplicates.values():
                all_files.extend(paths)
            for paths in self.non_duplicates.values():
                all_files.extend(paths)

            files_to_delete_paths = set()
            for item in file_items:
                values = self.tree.item(item, 'values')
                if values:
                    files_to_delete_paths.add(values[0])

            keep_filenames = set()
            for path in all_files:
                if path not in files_to_delete_paths:
                    keep_filenames.add(os.path.splitext(os.path.basename(path))[0].lower())

            orphaned_images = self.get_orphaned_images(keep_filenames)

        if not file_items and not orphaned_images:
            messagebox.showinfo("Info", "No files selected or marked for removal")
            return

        # Confirm deletion with user
        total_to_delete = len(file_items) + len(orphaned_images)
        is_perm = self.permanent_delete.get()

        if not self._confirm_deletion(file_items, orphaned_images, is_perm):
            return

        # Execute deletion with progress indication
        deleted_count = self._execute_deletion(file_items, orphaned_images, is_perm)

        # Clean up UI and show results
        self.refresh_row_colors()
        messagebox.showinfo("Done", f"Deleted {deleted_count} item(s)")
        self.scan()

    def _confirm_deletion(self, file_items: List[str], orphaned_images: List[str], is_perm: bool) -> bool:
        """Show confirmation dialog for file deletion.

        Args:
            file_items: List of file tree items to delete
            orphaned_images: List of orphaned image paths
            is_perm: Whether deletion is permanent

        Returns:
            True if user confirmed, False otherwise
        """
        total_to_delete = len(file_items) + len(orphaned_images)

        if is_perm:
            msg = (f"WARNING: You are about to PERMANENTLY delete {total_to_delete} item(s).\n\n"
                  "This cannot be undone! Proceed?")
            return messagebox.askyesno("Confirm Permanent Delete", msg, icon='warning')
        else:
            if file_items and orphaned_images:
                msg = (f"You are about to move {len(file_items)} marked file(s) AND "
                      f"{len(orphaned_images)} orphaned image(s) to the recycle bin")
            elif file_items:
                msg = f"You are about to move {len(file_items)} marked file(s) to the recycle bin"
            else:
                msg = f"You are about to move {len(orphaned_images)} orphaned image(s) to the recycle bin"
            return messagebox.askokcancel("Confirm Delete", msg)

    def _execute_deletion(self, file_items: List[str], orphaned_images: List[str], is_perm: bool) -> int:
        """Execute file deletion with progress indication.

        Args:
            file_items: List of file tree items to delete
            orphaned_images: List of orphaned image paths
            is_perm: Whether deletion is permanent

        Returns:
            Number of successfully deleted items
        """
        import tkinter.ttk as ttk
        total_to_delete = len(file_items) + len(orphaned_images)

        # Create progress popup
        progress_popup = tk.Toplevel(self)  # type: ignore
        progress_popup.title("Deleting Files...")
        progress_popup.geometry("400x120")
        progress_popup.resizable(False, False)
        progress_popup.transient(self)  # type: ignore
        progress_popup.grab_set()

        # Center popup
        x = self.winfo_x() + (self.winfo_width() // 2) - 200
        y = self.winfo_y() + (self.winfo_height() // 2) - 60
        progress_popup.geometry(f"+{x}+{y}")

        # Progress popup uses theme colors automatically via ttkbootstrap
        from tkinter import ttk
        lbl = ttk.Label(progress_popup, text="Starting deletion...", font=("TkDefaultFont", 9))
        lbl.pack(pady=(20, 10), padx=20, fill='x')

        pb = ttk_bs.Progressbar(progress_popup, orient='horizontal', length=360,
                               mode='determinate', bootstyle='primary')
        pb.pack(padx=20, pady=10)
        pb['maximum'] = total_to_delete
        pb['value'] = 0

        deleted_count = 0
        parents_to_check = set()

        try:
            # Delete regular files
            for i, item in enumerate(file_items):
                values = self.tree.item(item, 'values')
                if values:
                    path = values[0]
                    filename = os.path.basename(path)
                    display_name = filename[:57] + "..." if len(filename) > 60 else filename
                    lbl.config(text=f"Deleting: {display_name}")
                    pb['value'] = i + 1
                    progress_popup.update()

                    path = path.replace('/', os.sep)
                    if path and os.path.exists(path):
                        try:
                            if is_perm:
                                os.remove(path)
                            else:
                                send2trash(path)
                            deleted_count += 1

                            # Track UI cleanup needed
                            parent = self.tree.parent(item)
                            parents_to_check.add(parent)
                            self.tree.delete(item)

                            # Update data structures
                            parent_text = self.tree.item(parent, 'text')
                            normalized_path = path.replace(os.sep, '/')
                            if parent_text in self.duplicates:
                                if normalized_path in self.duplicates[parent_text]:
                                    self.duplicates[parent_text].remove(normalized_path)
                            elif parent_text in self.non_duplicates:
                                if normalized_path in self.non_duplicates[parent_text]:
                                    self.non_duplicates[parent_text].remove(normalized_path)
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to delete {path}: {str(e)}")

            # Delete orphaned images
            start_idx = len(file_items)
            for i, path in enumerate(orphaned_images):
                filename = os.path.basename(path)
                display_name = filename[:57] + "..." if len(filename) > 60 else filename
                lbl.config(text=f"Deleting Image: {display_name}")
                pb['value'] = start_idx + i + 1
                progress_popup.update()

                try:
                    p = path.replace('/', os.sep)
                    if is_perm:
                        os.remove(p)
                    else:
                        send2trash(p)
                    deleted_count += 1
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete {path}: {str(e)}")

        finally:
            progress_popup.destroy()

        # Clean up empty parent groups
        for parent in parents_to_check:
            children = self.tree.get_children(parent)
            parent_text = self.tree.item(parent, 'text')

            if not children:
                # Remove empty groups
                if parent_text in self.duplicates:
                    del self.duplicates[parent_text]
                if parent_text in self.non_duplicates:
                    del self.non_duplicates[parent_text]
                self.tree.delete(parent)
            elif len(children) == 1 and parent_text in self.duplicates:
                # Convert single-item duplicate groups to unique groups
                child_path = self.tree.item(children[0], 'values')[0]
                self.non_duplicates[parent_text] = [child_path]
                del self.duplicates[parent_text]
                self.tree.item(parent, open=False, tags=('unique_group',))

        return deleted_count
