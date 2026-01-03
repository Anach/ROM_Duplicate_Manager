#!/usr/bin/env python3
"""
ROM Duplicate Manager - Main Application Module

A comprehensive tool for managing duplicate ROM files with intelligent
version detection, smart file selection, and integrated image cleanup.

Features:
- Multiple file grouping strategies (name-based and size/hash-based)
- Smart version detection and language preference handling
- Orphaned image cleanup for ROM collections
- Advanced filtering with regex support
- Dark/light theme support
- Bulk operations with recycle bin or permanent deletion

Author: Anach
Version: 1.4.0
License: See LICENSE file
"""

import os
import math
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, font as tkfont
import ttkbootstrap as ttk_bs
from send2trash import send2trash
import configparser
from typing import Dict, List, Set, Tuple, Optional, Callable, Union, Any

# Import from modular structure (relative imports within package)
from .config.settings import load_config, save_config, CONFIG_FILE
from .config.defaults import DEFAULT_FILE_TYPES, DEFAULT_LANGUAGE_PRIORITIES
from .utils.icons import get_icon_photo
from .utils.helpers import (
    normalize_filename, extract_version, extract_languages, get_partial_hash, format_size
)
from .ui.components import ToolTip, AutoScrollbar, create_tooltip
from .core.scanner import AsyncScanner, ScanStatus
from .utils.updater import UpdateChecker, get_current_version

# Import all mixins
from .ui.themes import ThemeMixin
from .ui.menu_bar import MenuBarMixin
from .ui.file_list import FileListMixin
from .ui.dialogs import DialogMixin
from .core.duplicate_logic import DuplicateLogicMixin


class DuplicateManager(ThemeMixin, MenuBarMixin, FileListMixin, DialogMixin, DuplicateLogicMixin, ttk_bs.Window):
    """Main application window for the ROM Duplicate Manager.

    A comprehensive GUI application for managing duplicate ROM files with features including:
    - Multiple duplicate detection strategies (name-based and size/hash-based)
    - Smart file selection based on version, language, and quality preferences
    - Integrated orphaned image cleanup for ROM collections
    - Advanced filtering with wildcard and regex support
    - Dark/light theme support with user preferences
    - Bulk file operations with recycle bin or permanent deletion support

    The interface provides intuitive controls for scanning directories, filtering results,
    marking files for deletion, and managing application settings.
    """

    # Available ttkbootstrap themes
    LIGHT_THEMES = ['cosmo', 'flatly', 'litera', 'minty', 'lumen', 'sandstone', 'yeti', 'pulse', 'united', 'morph', 'journal', 'simplex', 'cerculean']
    DARK_THEMES = ['darkly', 'superhero', 'solar', 'cyborg', 'vapor']
    ALL_THEMES = LIGHT_THEMES + DARK_THEMES
    DEFAULT_THEME = 'darkly'

    def __init__(self) -> None:
        """Initialize the main application window and all UI components."""
        # Load saved configuration first to determine initial theme
        config = load_config()
        self._load_saved_settings(config)

        # Determine initial theme from saved settings
        initial_theme = getattr(self, 'theme_saved', self.DEFAULT_THEME)
        if initial_theme not in self.ALL_THEMES:
            initial_theme = self.DEFAULT_THEME

        # Initialize ttkbootstrap Window with theme
        super().__init__(themename=initial_theme)
        self.current_theme = initial_theme
        self.title("ROM Duplicate Manager")
        self.geometry("1100x600")

        # Set the application icon
        icon = get_icon_photo()
        if icon:
            self.iconphoto(False, icon)

        # Set proper window close protocol
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self._initialize_variables()

        # Create menu bar (after variables are initialized)
        self._create_menu_bar()

        self._setup_ui_components()
        self._apply_initial_theme()

    def _load_saved_settings(self, config: configparser.ConfigParser) -> None:
        """Load saved settings from configuration file."""
        self.theme_saved = config.get('Settings', 'theme', fallback=self.DEFAULT_THEME)
        self.dark_mode_saved = config.getboolean('Settings', 'dark_mode', fallback=False)
        self.row_colors_saved = config.getboolean('Settings', 'row_colors',
                                                 fallback=config.getboolean('Settings', 'alternate_colors', fallback=True))
        self.language_saved = config.get('Settings', 'language', fallback='Any')
        self.smart_select_saved = config.getboolean('Settings', 'smart_select', fallback=False)
        self.scan_images_saved = config.getboolean('Settings', 'scan_images', fallback=False)
        self.match_size_saved = config.getboolean('Settings', 'match_size', fallback=False)
        self.permanent_delete_saved = config.getboolean('Settings', 'permanent_delete', fallback=False)
        self.use_regex_saved = config.getboolean('Settings', 'use_regex', fallback=False)
        self.file_type_saved = config.get('Settings', 'file_type', fallback='Archive')
        self.search_in_path_saved = config.getboolean('Settings', 'search_in_path', fallback=False)

    def _initialize_variables(self) -> None:
        """Initialize all tkinter variables and application state."""
        # Theme variables
        self.dark_mode_enabled = tk.BooleanVar(value=self.dark_mode_saved)
        self.row_colors = tk.BooleanVar(value=self.row_colors_saved)

        # Get colors from ttkbootstrap theme
        colors = self.style.colors
        self.dark_bg = colors.bg
        self.dark_fg = colors.fg
        self.light_bg = colors.bg
        self.primary = colors.primary
        self.success = colors.success
        self.info = colors.info
        self.warning = colors.warning
        self.danger = colors.danger
        self.selection_bg = colors.info
        self.selection_fg = colors.selectfg
        self.light_highlight = colors.info
        self.dark_highlight = colors.info

        # UI state variables
        self.folder = tk.StringVar()
        self.filter_text = tk.StringVar()
        self.smart_select = tk.BooleanVar(value=self.smart_select_saved)
        self.scan_images = tk.BooleanVar(value=self.scan_images_saved)
        self.match_size = tk.BooleanVar(value=self.match_size_saved)
        self.permanent_delete = tk.BooleanVar(value=self.permanent_delete_saved)
        self.use_regex = tk.BooleanVar(value=self.use_regex_saved)
        self.search_in_path = tk.BooleanVar(value=self.search_in_path_saved)
        self.include_subfolders = tk.BooleanVar(value=False)
        self.file_type_filter = tk.StringVar(value=self.file_type_saved)
        self.language_filter = tk.StringVar(value=self.language_saved)

        # Data storage
        self.duplicates = {}
        self.non_duplicates = {}

        # Async scanner instance
        self._scanner = AsyncScanner()

        # Set up variable tracing
        self.filter_text.trace_add('write', self.on_filter_change)
        self._smart_select_trace = self.smart_select.trace_add('write', self.on_smart_select_change)

    def _setup_ui_components(self) -> None:
        """Create and configure all UI components."""
        self.file_types = DEFAULT_FILE_TYPES

        # Main toolbar container
        self.frame_top = ttk.Frame(self)
        self.frame_top.pack(fill='x', padx=5, pady=5)

        # Create 3 horizontal blocks for organization
        toolbar_container = ttk.Frame(self.frame_top)
        toolbar_container.pack(fill='x')

        # BLOCK 1: Folder Selection
        block1 = ttk.LabelFrame(toolbar_container, text="Location", padding=5)
        block1.pack(side='left', fill='y', padx=(0, 5))

        # Row 1: Folder entry (no label) and Browse
        b1_row1 = ttk.Frame(block1)
        b1_row1.pack(fill='x', pady=1)
        self.folder_entry = ttk.Entry(b1_row1, textvariable=self.folder, width=28)
        self.folder_entry.pack(side='left', padx=2)
        self.folder_entry.bind('<Return>', lambda e: self.scan())
        create_tooltip(self.folder_entry, "Current folder path. Press Enter or Ctrl+R to rescan.")
        self.browse_btn = ttk.Button(b1_row1, text="Browse", command=self.browse_folder)
        self.browse_btn.pack(side='left', padx=2)
        create_tooltip(self.browse_btn, "Select a folder to scan for duplicates")

        # Row 2: File Type first, then Sub-folders
        b1_row2 = ttk.Frame(block1)
        b1_row2.pack(fill='x', pady=1)
        ttk.Label(b1_row2, text="File Type:").pack(side='left', padx=2)
        self.type_combo = ttk.Combobox(b1_row2, textvariable=self.file_type_filter,
                                       values=list(self.file_types.keys()),
                                       state='readonly', width=12)
        self.type_combo.pack(side='left', padx=2)
        self.type_combo.bind('<<ComboboxSelected>>', self.on_file_type_change)
        create_tooltip(self.type_combo, "Filter files by file-types")
        self.subfolders_check = ttk.Checkbutton(b1_row2, text="Sub-folders", variable=self.include_subfolders, command=self.scan)
        self.subfolders_check.pack(side='left', padx=(10, 2))
        create_tooltip(self.subfolders_check, "Include sub-folders in the scan")

        # BLOCK 2: Scan Options
        block2 = ttk.LabelFrame(toolbar_container, text="Options", padding=5)
        block2.pack(side='left', fill='y', padx=5)

        # Row 1: Language, Smart Select
        b2_row1 = ttk.Frame(block2)
        b2_row1.pack(fill='x', pady=3)
        self.lang_combo = ttk.Combobox(b2_row1, textvariable=self.language_filter,
                                       values=['Any', 'English-US', 'English-EU', 'Japanese', 'French', 'German',
                                              'Spanish', 'Italian', 'Dutch', 'Portuguese', 'Swedish',
                                              'Chinese', 'Korean'],
                                       state='readonly', width=12)
        self.lang_combo.pack(side='left', padx=2)
        self.lang_combo.bind('<<ComboboxSelected>>', self.on_language_change)
        create_tooltip(self.lang_combo, "Preferred language for Smart Select suggestions")
        self.smart_select_check = ttk.Checkbutton(b2_row1, text="Smart Select", variable=self.smart_select)
        self.smart_select_check.pack(side='left', padx=(10, 2))
        create_tooltip(self.smart_select_check, "Automatically mark duplicates for removal based on priority")

        # Row 2: Match Size, Scan Images
        b2_row2 = ttk.Frame(block2)
        b2_row2.pack(fill='x', pady=6)
        self.match_size_check = ttk.Checkbutton(b2_row2, text="Match File-Size", variable=self.match_size, command=self.on_match_size_toggle)
        self.match_size_check.pack(side='left', padx=2)
        create_tooltip(self.match_size_check, "Group files by identical size and partial content hash instead of name")
        self.scan_images_check = ttk.Checkbutton(b2_row2, text="Scan Images", variable=self.scan_images, command=self.on_scan_images_toggle)
        self.scan_images_check.pack(side='left', padx=(10, 2))
        create_tooltip(self.scan_images_check, "Enable scanning and automatic deletion of orphaned images in the /images/ sub-folder")

        # BLOCK 3: Filter & Actions
        block3 = ttk.LabelFrame(toolbar_container, text="Filter", padding=5)
        block3.pack(side='left', fill='both', expand=False, padx=(5, 0))

        # Row 1: Filter entry (no label), Regex, Add Path
        b3_row1 = ttk.Frame(block3)
        b3_row1.pack(fill='x', pady=1)
        self.filter_entry = ttk.Entry(b3_row1, textvariable=self.filter_text, width=22)
        self.filter_entry.pack(side='left', padx=2)
        create_tooltip(self.filter_entry, "Filter the list by filename (Ctrl+F to focus)")
        self.regex_check = ttk.Checkbutton(b3_row1, text="Regex", variable=self.use_regex, command=self.on_regex_toggle)
        self.regex_check.pack(side='left', padx=(8, 5))
        create_tooltip(self.regex_check, "Use Regular Expressions for filtering")
        self.path_search_check = ttk.Checkbutton(b3_row1, text="Add Path", variable=self.search_in_path, command=self.on_filter_change)
        self.path_search_check.pack(side='left', padx=5)
        create_tooltip(self.path_search_check, "Include the full file path when filtering")

        # Row 2: Action buttons (wider, aligned)
        b3_row2 = ttk.Frame(block3)
        b3_row2.pack(fill='x', pady=3)
        btn_width = 9
        btn_padding = (5, 3)  # (horizontal, vertical) padding
        self.clear_btn = ttk.Button(b3_row2, text="Clear", command=self.clear_filter, width=btn_width, padding=btn_padding)
        self.clear_btn.pack(side='left', padx=2)
        create_tooltip(self.clear_btn, "Clear the filename filter")
        self.keep_btn = ttk_bs.Button(b3_row2, text="Keep", command=self.mark_filtered_keep, bootstyle='success', width=btn_width, padding=btn_padding)
        self.keep_btn.pack(side='left', padx=2)
        create_tooltip(self.keep_btn, "Mark all files matching the filter to be KEPT")
        self.mark_del_btn = ttk_bs.Button(b3_row2, text="Delete", command=self.mark_filtered_delete, bootstyle='danger', width=btn_width, padding=btn_padding)
        self.mark_del_btn.pack(side='left', padx=2)
        create_tooltip(self.mark_del_btn, "Mark all files matching the filter to be DELETED")
        self.reset_btn = ttk.Button(b3_row2, text="Reset", command=self.reset_marks, width=btn_width, padding=btn_padding)
        self.reset_btn.pack(side='left', padx=2)
        create_tooltip(self.reset_btn, "Reset all manual keep/delete marks")

        # BLOCK 4: Stats
        block4 = ttk.LabelFrame(toolbar_container, text="Stats", padding=5)
        block4.pack(side='left', fill='both', expand=True, padx=(5, 0))

        # Status labels inside Stats block (two rows with wrapping)
        self.status_font = tkfont.Font(size=9, weight='bold')
        status_tooltip = "Summary of scan results. Use Space to toggle, Del to mark for removal."

        # Calculate height for 2 lines to reserve space
        line_height = self.status_font.metrics('linespace')
        two_line_height = line_height * 2 + 4

        # Container frame with fixed height to reserve space for 2 lines
        status_container = ttk.Frame(block4, height=two_line_height)
        status_container.pack(anchor='w', padx=5, fill='x', expand=True)
        status_container.pack_propagate(False)

        self.status_label = ttk.Label(status_container, text="", font=self.status_font, wraplength=1)
        self.status_label.pack(anchor='w', fill='both', expand=True)
        create_tooltip(self.status_label, status_tooltip)

        # Bind to update wraplength dynamically based on container width
        def update_status_wrap(event):
            if event.width > 10:
                self.status_label.configure(wraplength=event.width - 10)
        status_container.bind('<Configure>', update_status_wrap)

        # Second status label for deletion info (initially hidden)
        self.status_label2 = ttk.Label(block4, text="", font=self.status_font)
        create_tooltip(self.status_label2, status_tooltip)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Configure grid to expand properly
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        vsb = AutoScrollbar(tree_frame, orient="vertical")
        hsb = AutoScrollbar(tree_frame, orient="horizontal")

        # ttkbootstrap handles the style automatically via Window initialization
        # Configure Treeview styling
        self.style.configure('Treeview', rowheight=25)
        self.style.configure('Treeview.Heading', borderwidth=0, padding=(5, 2))

        self.tree = ttk.Treeview(tree_frame, columns=('path',), selectmode='extended',
                                yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        # Track current sort state for indicators - default to Filename ascending
        # user_sorted tracks if user has explicitly clicked to sort
        self.sort_column = '#0'
        self.sort_reverse = False
        self.user_sorted = False

        # Set headings with default sort indicator on Filename
        self.tree.heading('#0', text='Filename ▲', anchor='w', command=lambda: self.sort_tree('#0', True))
        self.tree.heading('path', text='Full Path', anchor='w', command=lambda: self.sort_tree('path', False))

        # 50/50 column widths (minwidth ensures separator is draggable)
        self.tree.column('#0', width=400, minwidth=100, stretch=True)
        self.tree.column('path', width=400, minwidth=100, stretch=True)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        self.tree.bind('<Double-1>', self.on_tree_double_click)
        self.tree.bind('<Button-3>', self.show_context_menu)

        # Keyboard Shortcuts
        self.bind('<Control-f>', lambda e: self.filter_entry.focus_set())
        self.bind('<Control-r>', lambda e: self.scan())
        self.tree.bind('<space>', self.on_space_press)
        self.tree.bind('<Delete>', lambda e: self.mark_selected_delete())

        # Context Menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Open File Location", command=self.open_file_location)
        self.context_menu.add_command(label="Open File", command=self.open_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Toggle Keep/Delete", command=self.toggle_selected_status)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Mark to Keep", command=self.mark_selected_keep)
        self.context_menu.add_command(label="Mark to Delete", command=self.mark_selected_delete)

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(pady=(0, 5))

        self.button_row = ttk.Frame(self.button_frame)
        self.button_row.pack(side='top', pady=2)

        self.delete_button = ttk_bs.Button(self.button_row, text="Delete Selected", command=self.delete_selected, bootstyle='danger')
        self.delete_button.pack(side='left', padx=5)
        self.update_delete_button_tooltip()

        self.perm_del_check = ttk.Checkbutton(self.button_row, text="Permanent Delete", variable=self.permanent_delete, command=self.on_permanent_delete_toggle)
        self.perm_del_check.pack(side='left', padx=5)
        create_tooltip(self.perm_del_check, "Bypass the recycle bin and delete files permanently")

    def _apply_initial_theme(self) -> None:
        """Apply the initial theme settings and finalize UI setup."""
        # ttkbootstrap already applied the theme in __init__, but we need to
        # apply styling to legacy widgets and update tag colors
        if self.dark_mode_enabled.get():
            self.apply_dark_mode()
        else:
            self.apply_light_mode()

        self.on_regex_toggle()  # Initialize regex visual state

    def on_closing(self) -> None:
        """Handle window close event properly."""
        self.save_settings()
        self.destroy()

    def save_settings(self) -> None:
        """Save current application settings to configuration file."""
        save_config(
            self.dark_mode_enabled.get(), self.row_colors.get(),
            self.language_filter.get(), self.smart_select.get(),
            self.scan_images.get(), self.match_size.get(),
            self.permanent_delete.get(), self.use_regex.get(),
            self.file_type_filter.get(), self.search_in_path.get(),
            self.current_theme
        )

    def browse_folder(self) -> None:
        """Open folder selection dialog and initiate scan if folder is selected."""
        folder = filedialog.askdirectory()
        if folder:
            self.folder.set(folder)
            self.scan()

    def get_orphaned_images(self, keep_filenames: Optional[Set[str]] = None) -> List[str]:
        """Get list of orphaned image files that don't have corresponding ROMs."""
        folder = self.folder.get()
        if not folder or not os.path.isdir(folder):
            return []

        images_folder = os.path.join(folder, 'images')
        if not os.path.isdir(images_folder):
            return []

        if keep_filenames is None:
            keep_filenames = set()
            # Generate keep list from current scan results
            for paths in self.duplicates.values():
                for path in paths:
                    keep_filenames.add(os.path.splitext(os.path.basename(path))[0].lower())
            for paths in self.non_duplicates.values():
                for path in paths:
                    keep_filenames.add(os.path.splitext(os.path.basename(path))[0].lower())

        image_extensions = self.file_types.get("Images", set())
        orphaned = []

        try:
            for f in os.listdir(images_folder):
                full_path = os.path.join(images_folder, f)
                if os.path.isfile(full_path):
                    name, ext = os.path.splitext(f)
                    if image_extensions and ext.lower() in image_extensions:
                        match_name = name.lower()
                        # Handle "-image" suffix convention
                        if match_name.endswith("-image"):
                            match_name = match_name[:-6]
                        if match_name not in keep_filenames:
                            orphaned.append(full_path)
        except OSError:
            pass  # Handle permission errors gracefully

        return orphaned

    def format_size(self, size_bytes: int) -> str:
        """Format bytes into a human-readable string."""
        if size_bytes == 0:
            return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"

    def update_status_label(self) -> None:
        """Update the status label with scan results and deletion size information."""
        status = f"Found {len(self.duplicates)} duplicate group(s) and {len(self.non_duplicates)} unique file(s)."

        # Calculate total size of files marked for removal
        total_size_to_remove = 0
        items_to_remove = self.tree.tag_has('to_remove')
        files_to_delete_paths = set()

        for item in items_to_remove:
            values = self.tree.item(item, 'values')
            if values:
                path = values[0]
                files_to_delete_paths.add(path)
                try:
                    if os.path.exists(path):
                        total_size_to_remove += os.path.getsize(path)
                except Exception:
                    pass  # Skip files we can't access

        if self.scan_images.get():
            # Calculate orphaned images
            all_files = []
            for paths in self.duplicates.values():
                all_files.extend(paths)
            for paths in self.non_duplicates.values():
                all_files.extend(paths)

            keep_filenames = set()
            for path in all_files:
                if path not in files_to_delete_paths:
                    keep_filenames.add(os.path.splitext(os.path.basename(path))[0].lower())

            # Show current orphaned images
            orphaned_now = self.get_orphaned_images()
            if orphaned_now:
                status += f" | {len(orphaned_now)} orphaned image(s) found."

            # Add size of images that will be deleted
            orphaned_to_delete = self.get_orphaned_images(keep_filenames)
            for p in orphaned_to_delete:
                try:
                    if os.path.exists(p):
                        total_size_to_remove += os.path.getsize(p)
                except Exception:
                    pass

        # Update first status label
        if hasattr(self, 'status_label'):
            self.status_label.config(text=status)

        # Update second status label (deletion info) - show/hide as needed
        if hasattr(self, 'status_label2'):
            if total_size_to_remove > 0:
                self.status_label2.config(text=f"Marked for deletion: {self.format_size(total_size_to_remove)}")
                if not self.status_label2.winfo_ismapped():
                    self.status_label2.pack(anchor='w', padx=5, fill='x', expand=True)
            else:
                self.status_label2.pack_forget()

    def scan(self) -> None:
        """Scan the selected folder for duplicate files with async progress indication."""
        folder = self.folder.get()
        if not folder or not os.path.isdir(folder):
            return

        # Don't start a new scan if one is already running
        if self._scanner.is_running:
            return

        # Create and configure progress popup
        progress_popup = tk.Toplevel(self)
        progress_popup.title("Scanning...")
        progress_popup.geometry("400x120")
        progress_popup.resizable(False, False)
        progress_popup.transient(self)
        progress_popup.grab_set()

        # Set the same icon as main window
        icon = get_icon_photo()
        if icon:
            progress_popup.iconphoto(False, icon)

        # Center popup on parent window
        x = self.winfo_x() + (self.winfo_width() // 2) - 200
        y = self.winfo_y() + (self.winfo_height() // 2) - 60
        progress_popup.geometry(f"+{x}+{y}")

        # Progress popup uses theme colors automatically via ttkbootstrap
        lbl = ttk.Label(progress_popup, text="Starting scan...", font=("TkDefaultFont", 9))
        lbl.pack(pady=(20, 10), padx=20, fill='x')

        pb = ttk_bs.Progressbar(progress_popup, orient='horizontal', length=360, mode='determinate', bootstyle='primary')
        pb.pack(padx=20, pady=10)

        # Handle popup close as cancellation
        def on_popup_close():
            self._scanner.cancel()
        progress_popup.protocol("WM_DELETE_WINDOW", on_popup_close)

        # Start async scan
        ext_filter = self.file_types.get(self.file_type_filter.get())
        system_exts = self.file_types.get("System") or set()
        images_exts = self.file_types.get("Images") or set()
        ignore_system_prefix = ext_filter is None
        exclude_exts = images_exts if (ext_filter is None and not self.scan_images.get()) else None

        self._scanner.start_scan(
            folder,
            self.include_subfolders.get(),
            ext_filter,
            self.match_size.get(),
            system_exts,
            ignore_system_prefix,
            exclude_exts
        )

        def poll_scanner():
            """Poll the scanner for progress updates."""
            result = self._scanner.get_result()

            if result is None:
                # No result yet, continue polling
                if self._scanner.is_running:
                    self.after(16, poll_scanner)  # ~60fps polling
                return

            if result.status == ScanStatus.PROGRESS:
                # Update progress display
                pb['maximum'] = result.total
                pb['value'] = result.progress
                display_msg = result.message[:57] + "..." if len(result.message) > 60 else result.message
                lbl.config(text=display_msg)
                # Continue polling
                self.after(16, poll_scanner)

            elif result.status == ScanStatus.COMPLETE:
                # Scan finished successfully
                self.duplicates = result.duplicates or {}
                self.non_duplicates = result.non_duplicates or {}
                progress_popup.destroy()
                self.populate_tree()
                self.update_status_label()

            elif result.status == ScanStatus.CANCELLED:
                # Scan was cancelled
                progress_popup.destroy()

            elif result.status == ScanStatus.ERROR:
                # Scan encountered an error
                progress_popup.destroy()
                messagebox.showerror("Scan Error", f"An error occurred during scanning:\n{result.message}")

        # Start polling
        self.after(16, poll_scanner)

    def on_language_change(self, event=None) -> None:
        """Handle language filter selection change."""
        if hasattr(self, 'tree') and self.tree.get_children():
            self.apply_base_suggestions()
        self.save_settings()

    def on_file_type_change(self, event=None) -> None:
        """Handle file type filter change."""
        self.scan()
        self.save_settings()

    def on_scan_images_toggle(self) -> None:
        """Handle scan images checkbox toggle."""
        self.update_delete_button_tooltip()
        self.scan()
        self.save_settings()

    def on_match_size_toggle(self) -> None:
        """Handle match size checkbox toggle."""
        self.scan()
        self.save_settings()

    def on_permanent_delete_toggle(self) -> None:
        """Handle permanent delete checkbox toggle with safety confirmation."""
        if self.permanent_delete.get():
            confirm = messagebox.askyesno(
                "Warning",
                "Enabling Permanent Delete will bypass the Recycle Bin.\n\n"
                "Files will be deleted immediately and cannot be recovered.\n\n"
                "Are you sure you want to enable this?",
                icon='warning'
            )
            if not confirm:
                self.permanent_delete.set(False)
        self.save_settings()

    def update_delete_button_tooltip(self) -> None:
        """Update the delete button tooltip based on current settings."""
        if self.scan_images.get():
            create_tooltip(self.delete_button, "Move all marked files AND orphaned images to the recycle bin")
        else:
            create_tooltip(self.delete_button, "Move all marked or selected files to the recycle bin")

    def on_smart_select_change(self, *args) -> None:
        """Handle smart select checkbox change with user confirmation."""
        if not hasattr(self, 'tree') or not self.tree.get_children():
            self.save_settings()
            return

        if self.smart_select.get():
            # Check for existing manual selections
            has_manual = any(self.tree.tag_has('manual'))

            if has_manual:
                confirm = messagebox.askokcancel(
                    "Warning",
                    "Smart Select will override your current manual selections. Proceed?"
                )
                if not confirm:
                    # Revert the checkbox change
                    self.smart_select.trace_remove('write', self._smart_select_trace)
                    self.smart_select.set(False)
                    self._smart_select_trace = self.smart_select.trace_add('write', self.on_smart_select_change)
                    self.save_settings()
                    return
                else:
                    # Clear all manual tags
                    for item in self.tree.tag_has('manual'):
                        tags = list(self.tree.item(item, 'tags'))
                        if 'manual' in tags:
                            tags.remove('manual')
                        self.tree.item(item, tags=tuple(tags))

        self.apply_base_suggestions()
        self.save_settings()


def main():
    """Main entry point for the application."""
    try:
        app = DuplicateManager()
        app.mainloop()
    except Exception as e:
        import traceback
        error_msg = f"Failed to start ROM Duplicate Manager:\n\n{str(e)}\n\n{traceback.format_exc()}"
        try:
            import tkinter.messagebox as mb
            mb.showerror("Startup Error", error_msg)
        except Exception:
            # Fallback if tkinter isn't available
            import sys
            sys.stderr.write(error_msg + "\n")


if __name__ == "__main__":
    main()