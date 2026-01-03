"""Dialog management mixin for ROM Duplicate Manager.

This module contains all dialog-related methods.
"""

import tkinter as tk
from tkinter import messagebox
from rom_duplicate_manager.utils.updater import UpdateChecker, get_current_version


class DialogMixin:
    """Mixin class providing dialog functionality."""

    def check_for_updates(self) -> None:
        """Check for application updates."""
        try:
            current_version = get_current_version()
            update_checker = UpdateChecker(current_version)

            # Show checking dialog
            checking_dialog = tk.Toplevel(self)  # type: ignore
            checking_dialog.title("Checking for Updates")
            checking_dialog.geometry("300x100")
            checking_dialog.transient(self)  # type: ignore
            checking_dialog.grab_set()

            # Center the dialog
            checking_dialog.geometry("+%d+%d" % (
                self.winfo_rootx() + 50,
                self.winfo_rooty() + 50
            ))

            tk.Label(checking_dialog, text="Checking for updates...").pack(expand=True)
            checking_dialog.update()

            # Check for updates
            update_info = update_checker.check_for_updates_sync()
            checking_dialog.destroy()

            if update_info:
                # Show update available dialog
                message = update_checker.get_update_message(update_info)
                result = messagebox.askyesno("Update Available", message)

                if result:
                    # Open download URL in browser
                    import webbrowser
                    webbrowser.open(update_info.download_url)
                    messagebox.showinfo("Download Started",
                        f"Opening download page for v{update_info.version}.\n\n"
                        "The update will open in your default web browser.")
            else:
                messagebox.showinfo("No Updates",
                    f"You are running the latest version (v{current_version}).")

        except Exception as e:
            messagebox.showerror("Update Check Failed",
                f"Could not check for updates:\n{str(e)}")

    def show_about_dialog(self) -> None:
        """Show application about dialog."""
        current_version = get_current_version()
        about_text = f"""ROM Duplicate Manager v{current_version}

A comprehensive tool for managing duplicate ROM files with intelligent
version detection, smart file selection, and integrated image cleanup.

Features:
• Multiple duplicate detection strategies
• Smart version detection and language preferences
• Orphaned image cleanup for ROM collections
• Advanced filtering with regex support
• Dark/light theme support
• Bulk operations with recycle bin support

Author: Anach
GitHub: https://github.com/Anach/ROM_Duplicate_Manager"""

        messagebox.showinfo("About ROM Duplicate Manager", about_text)
