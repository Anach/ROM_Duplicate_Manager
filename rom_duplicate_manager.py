#!/usr/bin/env python3
"""
ROM Duplicate Manager

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
Version: 1.0.0
License: See LICENSE file
"""

import os
import re
import fnmatch
import hashlib
import subprocess
import math
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, font as tkfont
from send2trash import send2trash
import configparser
import base64
from typing import Dict, List, Set, Tuple, Optional, Callable, Union, Any, cast

# Application constants
PACMAN_ICON_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAABq0lEQVR4nO2bYZKDIAyFkzdcpvc/TI/DjrvT3Z1WBSQJifD9q6LvvQwgxZFosVgsFvPClmL5Sbm2LT9svLGn0COKwV5DWxWDowTXKgQoYHhJPUQML6nLow2MHhK4Q/geP7AU0+aKL1iIWNLqL2kZ4cfnsfwkd0Cjunvhz44PXXKT8E23kDn/NWXmYT2h5skAzfDf1779frWzoMY3pMRaQ1kVobsA2fms3+sf0oLvY35vDrCkNA8kFdHBoVuWxulO3f8o9Jbj6BxLFqBlYpN8FPbsDSQ5Gz+haoogEV59QyRf7P6lcL3ht+BXwh/lSX12DsXE/wtobYwmUsJTNz/VIIdPAKt3Aqo9wHNoVwXgQcF/9cnREBhRDJAjtqJbFx7kkFchJIthug6Q5L9xjSECCoTGEOGSIDmnt1eAglMzX5ydA92IK0OEa25KgSkNEdDNMd8UjQa8r9V7mX4IlECxReBeIPZuMGIRav1C46ajafEJmhy0XuC9F7T6g4WIFVd8wVJMk6t+WEI88hY6PJgYqQsZK/ZFkNJjUmDa7wX2mPKLkUjfDC0WiwXNzBcIwbWZE7SXrAAAAABJRU5ErkJggg=="
CONFIG_FILE = 'rom_duplicate_manager.ini'

def get_icon_photo() -> Optional[tk.PhotoImage]:
    """Convert base64 icon to tkinter PhotoImage.

    Returns:
        PhotoImage object or None if loading fails
    """
    try:
        icon_data = base64.b64decode(PACMAN_ICON_BASE64)
        return tk.PhotoImage(data=icon_data)
    except Exception as e:
        print(f"Failed to load icon: {e}")
        return None


def load_config() -> configparser.ConfigParser:
    """Load application configuration from INI file.

    Returns:
        ConfigParser object with loaded settings or empty if file doesn't exist
    """
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    return config


def save_config(dark_mode: bool, row_colors: bool, language: str, smart_select: bool,
                scan_images: bool, match_size: bool, permanent_delete: bool,
                use_regex: bool, file_type: str, search_in_path: bool) -> None:
    """Save application configuration to INI file.

    Args:
        dark_mode: Whether dark mode is enabled
        row_colors: Whether alternating row colors are enabled
        language: Preferred language setting
        smart_select: Whether smart selection is enabled
        scan_images: Whether image scanning is enabled
        match_size: Whether size-based matching is enabled
        permanent_delete: Whether permanent deletion is enabled
        use_regex: Whether regex filtering is enabled
        file_type: Current file type filter
        search_in_path: Whether to search in full file paths
    """
    config = configparser.ConfigParser()
    config['Settings'] = {
        'dark_mode': str(dark_mode),
        'row_colors': str(row_colors),
        'language': str(language),
        'smart_select': str(smart_select),
        'scan_images': str(scan_images),
        'match_size': str(match_size),
        'permanent_delete': str(permanent_delete),
        'use_regex': str(use_regex),
        'file_type': str(file_type),
        'search_in_path': str(search_in_path)
    }
    with open(CONFIG_FILE, 'w') as f:
        config.write(f)


def normalize_filename(filename: str, system_extensions: Optional[Set[str]] = None,
                       ignore_system_prefix: bool = False) -> str:
    """Normalize filename by removing copy indicators and version suffixes.

    Removes patterns like " - Copy", " - Copy (n)", and trailing parentheses/brackets
    to create a base name for comparison. Can also strip 3-4 digit catalog
    prefixes from ROM filenames when wildcard scanning is enabled to align
    numbered system files with unnumbered archives.

    Args:
        filename: The filename to normalize
        system_extensions: Set of ROM/system extensions to check for catalog prefixes
        ignore_system_prefix: Whether to strip leading 3-4 digit prefixes for ROMs

    Returns:
        Normalized filename without extension
    """
    name, ext = os.path.splitext(filename)
    if ignore_system_prefix and system_extensions and ext.lower() in system_extensions:
        name = re.sub(r'^\d{3,4}\s+', '', name)

    while True:
        old_name = name
        name = re.sub(r'\s*-\s*Copy(?:\s*\(\d+\))?$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*[\(\[].*?[\)\]]$', '', name)
        name = name.strip()
        if name == old_name:
            break
    return name


def extract_version(filename: str) -> Tuple[int, ...]:
    """Extract version information from filename for comparison.

    Identifies and extracts version numbers, dates, and other version indicators
    to enable intelligent version comparison for duplicate detection.

    Supports formats:
    - Dates: YYYY-MM-DD, YYYY.MM.DD, YYYY_MM_DD, YYYYMMDD
    - Version numbers: v1.0, version 2.1, etc.
    - Proto/Beta indicators: (proto 1), (beta 2)
    - Numeric suffixes in parentheses or at end

    Args:
        filename: The filename to analyze

    Returns:
        Tuple of version components for comparison (higher values = newer)
    """
    filename_lower = filename.lower()
    name_no_ext, _ = os.path.splitext(filename)

    # Extract dates in various formats
    date_val = (0, 0, 0)
    date_match = re.search(r'(20\d{2}|19\d{2})[.\-_](\d{1,2})[.\-_](\d{1,2})', name_no_ext)
    if date_match:
        try:
            date_val = tuple(map(int, date_match.groups()))
        except ValueError:
            pass
    else:
        date_match = re.search(r'(?<!\d)(20\d{2}|19\d{2})(\d{2})(\d{2})(?!\d)', name_no_ext)
        if date_match:
            try:
                date_val = tuple(map(int, date_match.groups()))
            except ValueError:
                pass

    # Extract explicit version numbers
    v_val = (0,)
    v_matches = re.findall(r'v(?:er(?:sion)?)?[\s\-_]?(\d+(?:\.\d+)*)', name_no_ext, re.IGNORECASE)
    if v_matches:
        try:
            v_val = tuple(map(int, v_matches[-1].split('.')))
        except ValueError:
            pass
    # Extract proto/beta version indicators
    proto_val = (0,)
    proto_match = re.search(r'\((?:proto|beta)\s*(\d+)\)', filename_lower)
    if proto_match:
        try:
            proto_val = (int(proto_match.group(1)),)
        except ValueError:
            pass

    # Extract other numeric indicators
    other_val = (0,)
    p_match = re.search(r'\((\d+)\)', name_no_ext)
    if p_match:
        try:
            other_val = (int(p_match.group(1)),)
        except ValueError:
            pass
    else:
        t_match = re.search(r'[_\s\-](\d+(?:\.\d+)*)$', name_no_ext)
        if t_match:
            try:
                other_val = tuple(map(int, t_match.group(1).split('.')))
            except ValueError:
                pass

    return date_val + v_val + proto_val + other_val


def extract_languages(filename: str) -> Set[str]:
    """Extract language codes and video formats from filename.

    Analyzes filename patterns to identify language preferences and video formats
    for ROM files, supporting various naming conventions commonly used in ROM sets.

    Args:
        filename: The filename to analyze

    Returns:
        Set of detected language/region identifiers, or {'Unknown'} if none found
    """
    languages = set()

    # Language and region mappings
    lang_map = {
        'en': 'English', 'english': 'English',
        'ja': 'Japanese', 'japan': 'Japanese',
        'fr': 'French', 'france': 'French',
        'de': 'German', 'germany': 'German',
        'es': 'Spanish', 'spain': 'Spanish',
        'it': 'Italian', 'italy': 'Italian',
        'nl': 'Dutch', 'netherlands': 'Dutch',
        'pt': 'Portuguese', 'portugal': 'Portuguese',
        'sv': 'Swedish', 'sweden': 'Swedish',
        'zh': 'Chinese', 'taiwan': 'Chinese', 'china': 'Chinese',
        'ko': 'Korean', 'korea': 'Korean'
    }

    region_map = {
        'usa': 'English-US', 'europe': 'English-EU', 'australia': 'English-EU',
        'uk': 'English-EU', 'world': 'World', 'global': 'World'
    }

    format_map = {'ntsc': 'NTSC', 'pal': 'PAL', 'secam': 'SECAM'}

    filename_lower = filename.lower()

    # Extract language information from parentheses
    paren_matches = re.findall(r'\(([^)]+)\)', filename)
    for match in paren_matches:
        parts = re.split(r'[,\s]+', match.lower())
        for part in parts:
            part = part.strip()
            if part in lang_map:
                languages.add(lang_map[part])
            elif part in region_map:
                languages.add(region_map[part])
            elif part in format_map:
                languages.add(format_map[part])

    return languages if languages else {'Unknown'}


def get_partial_hash(filepath: str) -> Optional[str]:
    """Generate a fast partial hash for file content comparison.

    Creates an MD5 hash from the first and last 64KB of a file to enable
    efficient duplicate detection while avoiding full file hashing.

    Args:
        filepath: Path to the file to hash

    Returns:
        Hex digest of partial hash, "empty" for zero-byte files, or None on error
    """
    try:
        size = os.path.getsize(filepath)
        if size == 0:
            return "empty"

        chunk_size = 65536  # 64KB chunks
        hasher = hashlib.md5()

        with open(filepath, "rb") as f:
            hasher.update(f.read(chunk_size))
            if size > chunk_size:
                try:
                    f.seek(-chunk_size, os.SEEK_END)
                    hasher.update(f.read(chunk_size))
                except OSError:
                    pass  # Handle files that can't seek to end

        return hasher.hexdigest()
    except Exception:
        return None


def scan_folder(folder: str, recursive: bool = False, extension_filter: Optional[Set[str]] = None,
                match_size: bool = False, progress_callback: Optional[Callable] = None,
                system_extensions: Optional[Set[str]] = None, ignore_system_prefix: bool = False,
                exclude_extensions: Optional[Set[str]] = None) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Scan folder for duplicate files using name-based or size-based matching.

    Args:
        folder: Directory path to scan
        recursive: Whether to include subdirectories
        extension_filter: Set of file extensions to include (None = all files)
        exclude_extensions: Set of file extensions to skip when extension_filter is None
        match_size: Use size+hash matching instead of filename normalization
        progress_callback: Optional callback function for progress updates
        system_extensions: Optional set of ROM/system extensions for prefix stripping
        ignore_system_prefix: Ignore 3-4 digit catalog prefixes on system ROMs when True

    Returns:
        Tuple of (duplicates_dict, non_duplicates_dict) where keys are group names
        and values are lists of file paths
    """
    file_list = []
    if recursive:
        for root, dirs, files in os.walk(folder):
            for f in files:
                _, ext = os.path.splitext(f)
                ext_lower = ext.lower()
                if extension_filter and ext_lower not in extension_filter:
                    continue
                if not extension_filter and exclude_extensions and ext_lower in exclude_extensions:
                    continue
                file_list.append(os.path.join(root, f).replace('\\', '/'))
    else:
        if os.path.exists(folder):
            for f in os.listdir(folder):
                full_path = os.path.join(folder, f).replace('\\', '/')
                if os.path.isfile(full_path):
                    _, ext = os.path.splitext(f)
                    ext_lower = ext.lower()
                    if extension_filter and ext_lower not in extension_filter:
                        continue
                    if not extension_filter and exclude_extensions and ext_lower in exclude_extensions:
                        continue
                    file_list.append(full_path)

    groups = {}
    total = len(file_list)
    if total == 0:
        return {}, {}

    if not match_size:
        # Name-based grouping
        for i, full_path in enumerate(file_list):
            if progress_callback:
                progress_callback(i + 1, total, f"Scanning: {os.path.basename(full_path)}")
            base = normalize_filename(os.path.basename(full_path), system_extensions, ignore_system_prefix)
            groups.setdefault(base, []).append(full_path)
    else:
        # Size-based grouping with partial hashing
        size_map = {}
        for i, full_path in enumerate(file_list):
            if progress_callback:
                progress_callback(i + 1, total, f"Checking size: {os.path.basename(full_path)}")
            try:
                size = os.path.getsize(full_path)
                size_map.setdefault(size, []).append(full_path)
            except Exception:
                pass  # Skip files we can't access

        # Hash files that share the same size
        hashed_count = 0
        potential_dupes = [paths for paths in size_map.values() if len(paths) > 1]
        total_to_hash = sum(len(p) for p in potential_dupes)

        for size, paths in size_map.items():
            if len(paths) == 1:
                # Unique size - group by normalized name
                full_path = paths[0]
                base = normalize_filename(os.path.basename(full_path), system_extensions, ignore_system_prefix)
                groups.setdefault(base, []).append(full_path)
            else:
                # Multiple files with same size - group by hash
                for full_path in paths:
                    hashed_count += 1
                    if progress_callback:
                        progress_callback(hashed_count, total_to_hash, f"Hashing: {os.path.basename(full_path)}")
                    h = get_partial_hash(full_path)
                    _, ext = os.path.splitext(full_path)
                    if h:
                        base = f"Size: {size:,} bytes ({ext.lower()}) [Hash: {h[:8]}]"
                    else:
                        base = f"Size: {size:,} bytes ({ext.lower()})"
                    groups.setdefault(base, []).append(full_path)

    # Split into duplicates and unique files
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    non_duplicates = {k: v for k, v in groups.items() if len(v) == 1}

    return duplicates, non_duplicates

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

    def schedule_tip(self, event=None) -> None:
        """Schedule tooltip to show after delay."""
        self.hide_tip()
        if self.text:
            self.id = self.widget.after(500, self.show_tip)

    def show_tip(self, event=None) -> None:
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

    def hide_tip(self, event=None) -> None:
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


class DuplicateManager(tk.Tk):
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

    def __init__(self) -> None:
        """Initialize the main application window and all UI components."""
        super().__init__()
        self.title("ROM Duplicate Manager")
        self.geometry("1100x600")

        # Set the application icon
        icon = get_icon_photo()
        if icon:
            self.iconphoto(False, icon)

        # Load saved configuration
        config = load_config()
        self._load_saved_settings(config)
        self._initialize_variables()
        self._setup_ui_components()
        self._apply_initial_theme()

    def _load_saved_settings(self, config: configparser.ConfigParser) -> None:
        """Load saved settings from configuration file."""
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
        self.dark_bg = '#2d2d2d'
        self.dark_fg = '#e0e0e0'
        self.light_bg = '#f0f0f0'
        self.selection_bg = '#3399ff'
        self.selection_fg = 'black'
        self.light_highlight = 'blue'
        self.dark_highlight = '#00d4ff'

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

        # Set up variable tracing
        self.filter_text.trace_add('write', self.on_filter_change)
        self._smart_select_trace = self.smart_select.trace_add('write', self.on_smart_select_change)

    def _get_file_type_definitions(self) -> Dict[str, Optional[Set[str]]]:
        """Define supported file type categories and their extensions.

        Returns:
            Dictionary mapping category names to sets of file extensions
        """
        return {
            "Archive": {".zip", ".7z", ".jar", ".lha", ".lzh", ".rar", ".tar", ".gz"},
            "System": {
                ".adf", ".hdf", ".cpc", ".dsk", ".cpr", ".do", ".po", ".apple2", ".a26", ".a52", ".a78", ".lnx",
                ".st", ".xfd", ".atr", ".atx", ".com", ".xex", ".cas", ".sap", ".d64", ".d71", ".d81", ".g64",
                ".prg", ".t64", ".tap", ".crt", ".gb", ".gbc", ".gba", ".md", ".smd", ".gen", ".60", ".sms",
                ".nes", ".fds", ".smc", ".sfc", ".fig", ".swc", ".n64", ".v64", ".z64", ".pbp", ".cso", ".neo",
                ".pce", ".sgx", ".ws", ".wsc", ".col", ".int", ".vec", ".min", ".sv", ".gg", ".ngp", ".ngc",
                ".vb", ".32x", ".p8", ".png", ".solarus", ".tic", ".love", ".scummvm", ".ldb", ".nx", ".v32"
            },
            "Disk": {".iso", ".bin", ".cue", ".img", ".mdf", ".mds", ".nrg", ".ccd", ".chd", ".gdi", ".cdi"},
            "Image": {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif"},
            "Video": {".mp4", ".mpg", ".mpeg", ".avi", ".mov", ".wmv", ".mkv"},
            "Wildcard *.*": None
        }

    def _setup_ui_components(self) -> None:
        """Create and configure all UI components."""
        self.file_types = self._get_file_type_definitions()

        self.frame_top = tk.Frame(self, relief='raised', bd=2)
        self.frame_top.pack(fill='x', padx=5, pady=5)

        # Row 1: Folder, Subfolders, File Type, Language, Smart Select
        row1 = tk.Frame(self.frame_top)
        row1.pack(fill='x', padx=2, pady=2)

        tk.Label(row1, text="Folder:").pack(side='left', padx=2)
        self.folder_entry = tk.Entry(row1, textvariable=self.folder, width=30)
        self.folder_entry.pack(side='left', padx=5)
        self.folder_entry.bind('<Return>', lambda e: self.scan())
        create_tooltip(self.folder_entry, "Current folder path. Press Enter or Ctrl+R to rescan.")

        self.browse_btn = tk.Button(row1, text="Browse", command=self.browse_folder)
        self.browse_btn.pack(side='left')
        create_tooltip(self.browse_btn, "Select a folder to scan for duplicates")

        self.subfolders_check = tk.Checkbutton(row1, text="Sub-folders", variable=self.include_subfolders, command=self.scan)
        self.subfolders_check.pack(side='left', padx=5)
        create_tooltip(self.subfolders_check, "Include sub-folders in the scan")

        tk.Label(row1, text="File Type:").pack(side='left', padx=2)
        self.type_combo = ttk.Combobox(row1, textvariable=self.file_type_filter,
                                       values=list(self.file_types.keys()),
                                       state='readonly', width=12)
        self.type_combo.pack(side='left', padx=2)
        self.type_combo.bind('<<ComboboxSelected>>', self.on_file_type_change)
        create_tooltip(self.type_combo, "Filter files by file-types")

        ttk.Separator(row1, orient='vertical').pack(side='left', fill='y', padx=10)

        tk.Label(row1, text="Lang:").pack(side='left', padx=2)
        self.lang_combo = ttk.Combobox(row1, textvariable=self.language_filter,
                                       values=['Any', 'English-US', 'English-EU', 'Japanese', 'French', 'German',
                                              'Spanish', 'Italian', 'Dutch', 'Portuguese', 'Swedish',
                                              'Chinese', 'Korean'],
                                       state='readonly', width=10)
        self.lang_combo.pack(side='left', padx=2)
        self.lang_combo.bind('<<ComboboxSelected>>', self.on_language_change)
        create_tooltip(self.lang_combo, "Preferred language for Smart Select suggestions")

        self.scan_images_check = tk.Checkbutton(row1, text="Scan Images", variable=self.scan_images, command=self.on_scan_images_toggle)
        self.scan_images_check.pack(side='left', padx=2)
        create_tooltip(self.scan_images_check, "Enable scanning and automatic deletion of orphaned images in the /images/ sub-folder")

        self.match_size_check = tk.Checkbutton(row1, text="Match Size", variable=self.match_size, command=self.on_match_size_toggle)
        self.match_size_check.pack(side='left', padx=2)
        create_tooltip(self.match_size_check, "Group files by identical size and partial content hash instead of name")

        ttk.Separator(row1, orient='vertical').pack(side='left', fill='y', padx=10)

        self.smart_select_check = tk.Checkbutton(row1, text="Smart Select", variable=self.smart_select)
        self.smart_select_check.pack(side='left', padx=2)
        create_tooltip(self.smart_select_check, "Automatically mark duplicates for removal based on priority")

        # Row 2: Filter and Display controls
        row2 = tk.Frame(self.frame_top)
        row2.pack(fill='x', padx=2, pady=2)

        tk.Label(row2, text="Filter:").pack(side='left', padx=5)
        self.filter_entry = tk.Entry(row2, textvariable=self.filter_text, width=20)
        self.filter_entry.pack(side='left', padx=5)
        create_tooltip(self.filter_entry, "Filter the list by filename (Ctrl+F to focus)")

        self.regex_check = tk.Checkbutton(row2, text="Regex", variable=self.use_regex, command=self.on_regex_toggle)
        self.regex_check.pack(side='left', padx=2)
        create_tooltip(self.regex_check, "Use Regular Expressions for filtering")

        self.path_search_check = tk.Checkbutton(row2, text="Include Path", variable=self.search_in_path, command=self.on_filter_change)
        self.path_search_check.pack(side='left', padx=2)
        create_tooltip(self.path_search_check, "Include the full file path when filtering")

        self.clear_btn = tk.Button(row2, text="Clear", command=self.clear_filter)
        self.clear_btn.pack(side='left', padx=2)
        create_tooltip(self.clear_btn, "Clear the filename filter")

        self.keep_btn = tk.Button(row2, text="Keep", command=self.mark_filtered_keep, fg='green')
        self.keep_btn.pack(side='left', padx=5)
        create_tooltip(self.keep_btn, "Mark all files matching the filter to be KEPT")

        self.mark_del_btn = tk.Button(row2, text="Delete", command=self.mark_filtered_delete, fg='red')
        self.mark_del_btn.pack(side='left', padx=2)
        create_tooltip(self.mark_del_btn, "Mark all files matching the filter to be DELETED")

        self.reset_btn = tk.Button(row2, text="Reset", command=self.reset_marks)
        self.reset_btn.pack(side='left', padx=5)
        create_tooltip(self.reset_btn, "Reset all manual keep/delete marks")

        ttk.Separator(row2, orient='vertical').pack(side='left', fill='y', padx=10)

        self.row_colors_check = tk.Checkbutton(row2, text="Row colors", variable=self.row_colors,
                      command=self.toggle_row_colors)
        self.row_colors_check.pack(side='left', padx=5)
        create_tooltip(self.row_colors_check, "Toggle alternating background colors for list rows")

        self.dark_mode_check = tk.Checkbutton(row2, text="Dark Mode", variable=self.dark_mode_enabled,
                      command=self.toggle_dark_mode)
        self.dark_mode_check.pack(side='left', padx=5)
        create_tooltip(self.dark_mode_check, "Toggle between light and dark user interface")

        tree_frame = tk.Frame(self, relief='sunken', bd=2)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)

        vsb = AutoScrollbar(tree_frame, orient="vertical")
        hsb = AutoScrollbar(tree_frame, orient="horizontal")

        self.style = ttk.Style(self)
        self.tree = ttk.Treeview(tree_frame, columns=('path',), selectmode='extended',
                                yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        self.tree.heading('#0', text='Filename', command=lambda: self.sort_tree('#0', False))
        self.tree.heading('path', text='Full Path', command=lambda: self.sort_tree('path', False))
        self.tree.column('#0', width=350)
        self.tree.column('path', width=700)

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

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=(0, 5))

        self.status_label = tk.Label(self.button_frame, text="", font=tkfont.Font(size=9, weight='bold'))
        self.status_label.pack(side='top', pady=2)
        create_tooltip(self.status_label, "Summary of scan results. Use Space to toggle, Del to mark for removal.")

        self.button_row = tk.Frame(self.button_frame)
        self.button_row.pack(side='top', pady=2)

        self.delete_button = tk.Button(self.button_row, text="Delete Selected", command=self.delete_selected)
        self.delete_button.pack(side='left', padx=5)
        self.update_delete_button_tooltip()

        self.perm_del_check = tk.Checkbutton(self.button_row, text="Permanent Delete", variable=self.permanent_delete, command=self.on_permanent_delete_toggle)
        self.perm_del_check.pack(side='left', padx=5)
        create_tooltip(self.perm_del_check, "Bypass the recycle bin and delete files permanently")

        self._apply_initial_theme()

    def _apply_initial_theme(self) -> None:
        """Apply the initial theme settings and finalize UI setup."""
        if self.dark_mode_enabled.get():
            self.apply_dark_mode()
        else:
            self.apply_light_mode()

        self.apply_display_settings()
        self.on_regex_toggle()  # Initialize regex visual state

    def save_settings(self) -> None:
        """Save current application settings to configuration file."""
        save_config(
            self.dark_mode_enabled.get(), self.row_colors.get(),
            self.language_filter.get(), self.smart_select.get(),
            self.scan_images.get(), self.match_size.get(),
            self.permanent_delete.get(), self.use_regex.get(),
            self.file_type_filter.get(), self.search_in_path.get()
        )

    def browse_folder(self) -> None:
        """Open folder selection dialog and initiate scan if folder is selected."""
        folder = filedialog.askdirectory()
        if folder:
            self.folder.set(folder)
            self.scan()

    def get_orphaned_images(self, keep_filenames: Optional[Set[str]] = None) -> List[str]:
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
        """Update the status label with scan results and deletion size information.

        Calculates and displays:
        - Number of duplicate groups and unique files found
        - Count of orphaned images (if image scanning enabled)
        - Total size of files marked for deletion
        """
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

        if total_size_to_remove > 0:
            status += f" | Marked for deletion: {self.format_size(total_size_to_remove)}"

        if hasattr(self, 'status_label'):
            self.status_label.config(text=status)

    def scan(self) -> None:
        """Scan the selected folder for duplicate files with progress indication.

        Creates a modal progress dialog and scans the folder using either
        name-based or size-based matching depending on current settings.
        Updates the UI with results upon completion.
        """
        folder = self.folder.get()
        if not folder or not os.path.isdir(folder):
            return

        # Create and configure progress popup
        progress_popup = tk.Toplevel(self)
        progress_popup.title("Scanning...")
        progress_popup.geometry("400x120")
        progress_popup.resizable(False, False)
        progress_popup.transient(self)
        progress_popup.grab_set()

        # Center popup on parent window
        x = self.winfo_x() + (self.winfo_width() // 2) - 200
        y = self.winfo_y() + (self.winfo_height() // 2) - 60
        progress_popup.geometry(f"+{x}+{y}")

        # Apply theme styling
        is_dark = self.dark_mode_enabled.get()
        popup_bg = self.dark_bg if is_dark else self.light_bg
        popup_fg = self.dark_fg if is_dark else 'black'
        progress_popup.configure(bg=popup_bg)

        lbl = tk.Label(progress_popup, text="Starting scan...", bg=popup_bg, fg=popup_fg, font=("TkDefaultFont", 9))
        lbl.pack(pady=(20, 10), padx=20, fill='x')

        pb = ttk.Progressbar(progress_popup, orient='horizontal', length=360, mode='determinate', style="Blue.Horizontal.TProgressbar")
        pb.pack(padx=20, pady=10)

        def progress_callback(current: int, total: int, msg: str) -> None:
            """Update progress display."""
            pb['maximum'] = total
            pb['value'] = current
            display_msg = msg[:57] + "..." if len(msg) > 60 else msg
            lbl.config(text=display_msg)
            progress_popup.update()

        try:
            ext_filter = self.file_types.get(self.file_type_filter.get())
            system_exts = self.file_types.get("System") or set()
            images_exts = self.file_types.get("Images") or set()
            ignore_system_prefix = ext_filter is None
            exclude_exts = images_exts if (ext_filter is None and not self.scan_images.get()) else None
            self.duplicates, self.non_duplicates = scan_folder(
                folder,
                self.include_subfolders.get(),
                ext_filter,
                self.match_size.get(),
                progress_callback,
                system_exts,
                ignore_system_prefix,
                exclude_exts
            )
        finally:
            progress_popup.destroy()

        self.populate_tree()
        self.update_status_label()

    def on_language_change(self, event=None) -> None:
        """Handle language filter selection change.

        Reapplies smart selection with new language preference and saves settings.

        Args:
            event: Tkinter event object (unused)
        """
        if hasattr(self, 'tree') and self.tree.get_children():
            self.apply_base_suggestions()
        self.save_settings()

    def on_file_type_change(self, event=None) -> None:
        """Handle file type filter change.

        Triggers a new scan with the selected file type filter and saves settings.

        Args:
            event: Tkinter event object (unused)
        """
        self.scan()
        self.save_settings()

    def on_scan_images_toggle(self) -> None:
        """Handle scan images checkbox toggle.

        Updates tooltip, triggers rescan, and saves settings.
        """
        self.update_delete_button_tooltip()
        self.scan()
        self.save_settings()

    def on_match_size_toggle(self) -> None:
        """Handle match size checkbox toggle.

        Triggers rescan with size-based matching and saves settings.
        """
        self.scan()
        self.save_settings()

    def on_permanent_delete_toggle(self) -> None:
        """Handle permanent delete checkbox toggle with safety confirmation.

        Shows warning dialog for permanent deletion and saves settings.
        """
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
        """Handle smart select checkbox change with user confirmation.

        When enabling smart select, warns user if manual selections exist
        and offers to override them. Applies intelligent file selection
        based on version, language, and quality preferences.

        Args:
            *args: Variable arguments from tkinter trace callback
        """
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

    def toggle_item_status(self, item: str) -> None:
        """Toggle the keep/delete status of a specific tree item.

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

    def on_tree_double_click(self, event) -> str:
        """Handle double-click to toggle item status.

        Args:
            event: Tkinter mouse event

        Returns:
            "break" to prevent further event propagation
        """
        item = self.tree.identify_row(event.y)
        self.toggle_item_status(item)
        return "break"

    def on_space_press(self, event) -> str:
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

    def show_context_menu(self, event) -> None:
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

    def get_file_priority(self, filepath: str) -> Tuple:
        """Calculate file priority for smart selection based on multiple criteria.

        Evaluates files based on:
        - Location (root folder preferred)
        - Quality indicators (proto/beta/demo = lower priority)
        - Version information (newer versions preferred)
        - Language preference matching
        - Video format compatibility
        - File name length (shorter names preferred)

        Args:
            filepath: Full path to the file to evaluate

        Returns:
            Tuple for comparison where lower values = higher priority
        """
        lang_pref = self.language_filter.get()
        filename = os.path.basename(filepath)
        filename_lower = filename.lower()

        # Location priority (root folder preferred)
        root_folder = self.folder.get().replace('\\', '/')
        is_not_in_root = 0 if os.path.dirname(filepath.replace('\\', '/')) == root_folder else 1

        # Quality indicators (lower is worse)
        is_low_priority = 1 if re.search(r'\(proto|\(demo|\(sample|\(beta', filename_lower) else 0

        languages = extract_languages(filename)
        actual_langs = languages - {'Unknown'}
        num_langs = len(actual_langs)
        version = extract_version(filename)
        length = len(filename)
        is_world = 1 if 'World' in languages else 0
        has_lang = 1 if (lang_pref != 'Any' and lang_pref in languages) else 0

        # Video format priority based on language preference
        format_priority = 0
        if lang_pref != 'Any':
            ntsc_regions = ('English-US', 'Japanese', 'Korean', 'Chinese')
            pal_regions = ('English-EU', 'French', 'German', 'Spanish', 'Italian', 'Dutch', 'Portuguese', 'Swedish')
            if lang_pref in ntsc_regions:
                if 'NTSC' in languages:
                    format_priority = 2
                elif 'PAL' in languages:
                    format_priority = 1
                elif 'SECAM' in languages:
                    format_priority = -1
            elif lang_pref in pal_regions:
                if 'PAL' in languages:
                    format_priority = 2
                elif 'SECAM' in languages:
                    format_priority = 1
                elif 'NTSC' in languages:
                    format_priority = -1

        # Return priority tuple (lower values = higher priority)
        return (is_not_in_root, is_low_priority) + tuple(-v for v in version) + \
               (-is_world, -has_lang, -format_priority, -num_langs, length, filename)

    def get_base_file(self, files: List[str]) -> str:
        """Select the best file from a group of duplicates.

        Uses the priority system to determine which file should be kept
        based on quality indicators, version, language preference, etc.

        Args:
            files: List of file paths to evaluate

        Returns:
            Path to the file with the highest priority (lowest priority value)
        """
        return min(files, key=self.get_file_priority)

    def apply_base_suggestions(self) -> None:
        """Apply smart selection suggestions to all duplicate groups.

        For each group of duplicates, identifies the best file using priority
        ranking and marks others for removal if smart select is enabled.
        """
        for parent in self.tree.get_children():
            parent_text = self.tree.item(parent, 'text')
            if parent_text in self.duplicates:
                files = self.duplicates[parent_text]
                base_file = self.get_base_file(files)

                for child in self.tree.get_children(parent):
                    current_tags = list(self.tree.item(child, 'tags'))
                    # Skip manually marked items
                    if 'manual' in current_tags:
                        continue

                    child_path = self.tree.item(child, 'values')[0]
                    current_tags = [t for t in current_tags if t not in ('base', 'to_remove')]

                    if self.smart_select.get():
                        if child_path == base_file:
                            current_tags.append('base')
                        else:
                            current_tags.append('to_remove')

                    self.tree.item(child, tags=tuple(current_tags))

        self.update_tag_colors()
        self.update_status_label()
        self.apply_filter()

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

    def on_filter_change(self, *args) -> None:
        """Handle filter text or search options change.

        Args:
            *args: Variable arguments from tkinter trace callback
        """
        self.apply_filter()

    def on_regex_toggle(self) -> None:
        """Handle regex checkbox toggle with visual feedback.

        Changes the filter entry background color to indicate regex mode
        and reapplies the current filter with the new mode.
        """
        is_dark = self.dark_mode_enabled.get()
        if self.use_regex.get():
            bg = '#2d3d4d' if is_dark else '#e6f3ff'
        else:
            bg = self.dark_bg if is_dark else 'white'
        self.filter_entry.configure(bg=bg)

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

                # Update filtered tag
                current_tags = list(self.tree.item(child, 'tags'))
                if 'filtered' in current_tags:
                    current_tags.remove('filtered')
                if matches_filter:
                    current_tags.append('filtered')
                self.tree.item(child, tags=tuple(current_tags))

            # Expand/collapse parent based on matches
            if not is_empty and not has_matching_child:
                self.tree.item(parent, open=False)
            else:
                self.tree.item(parent, open=True)

        self.update_tag_colors()

    def update_tag_colors(self) -> None:
        """Update the visual styling for different file states.

        Configures colors and fonts for base (keep), to_remove (delete),
        and filtered items based on the current theme.
        """
        normal_font = tkfont.nametofont("TkDefaultFont")
        strike_font = normal_font.copy()
        strike_font.configure(overstrike=True)
        bold_font = normal_font.copy()
        bold_font.configure(weight='bold')

        # Configure tag colors and styles
        self.tree.tag_configure('base', foreground='green')
        self.tree.tag_configure('to_remove', foreground='red', font=strike_font)

        if self.dark_mode_enabled.get():
            self.tree.tag_configure('filtered', background='#4b5320', font=bold_font)
        else:
            self.tree.tag_configure('filtered', background='#ffffcc', font=bold_font)

    def toggle_row_colors(self) -> None:
        """Toggle alternating row colors and save the setting."""
        self.apply_display_settings()
        self.save_settings()

    def apply_display_settings(self) -> None:
        """Apply current display settings including theme and row coloring.

        Configures the treeview appearance, progress bar styling, and
        alternating row colors based on current theme and user preferences.
        """
        self.style.theme_use('clam')
        is_dark = self.dark_mode_enabled.get()
        bg = self.dark_bg if is_dark else 'white'
        fg = 'white' if is_dark else 'black'
        sel_fg = 'white' if is_dark else 'black'  # Better visibility in dark mode

        # Configure progress bar styling
        trough_color = '#1a1a1a' if is_dark else '#e0e0e0'
        vsc_blue = '#007acc'
        self.style.configure("Blue.Horizontal.TProgressbar",
                             background=vsc_blue,
                             troughcolor=trough_color,
                             bordercolor=trough_color,
                             lightcolor=vsc_blue,
                             darkcolor=vsc_blue)

        # Configure treeview styling
        self.style.configure('Treeview',
                           background=bg, fieldbackground=bg, foreground=fg,
                           rowheight=25, borderwidth=0, relief='flat')
        self.style.map('Treeview',
                      background=[('selected', self.selection_bg)],
                      foreground=[('selected', sel_fg)])

        # Configure alternating row colors
        if self.row_colors.get():
            if self.dark_mode_enabled.get():
                self.tree.tag_configure('oddrow', background='#3d3d3d')
                self.tree.tag_configure('evenrow', background='#2d2d2d')
            else:
                self.tree.tag_configure('oddrow', background='#e0e0e0')
                self.tree.tag_configure('evenrow', background='white')
        else:
            self.tree.tag_configure('oddrow', background=bg)
            self.tree.tag_configure('evenrow', background=bg)

        self.refresh_row_colors()

    def refresh_row_colors(self) -> None:
        """Refresh alternating row color tags for all tree items.

        Applies alternating background colors to file items while preserving
        parent group selection backgrounds.
        """
        row_count = 0
        for parent in self.tree.get_children():
            # Remove alternating colors from parents to preserve selection background
            p_tags = list(self.tree.item(parent, 'tags'))
            p_tags = [t for t in p_tags if t not in ('oddrow', 'evenrow')]
            self.tree.item(parent, tags=tuple(p_tags))
            row_count += 1

            # Apply alternating colors to children
            for child in self.tree.get_children(parent):
                current_tags = list(self.tree.item(child, 'tags'))
                current_tags = [t for t in current_tags if t not in ('oddrow', 'evenrow')]
                current_tags.append('evenrow' if row_count % 2 == 0 else 'oddrow')
                self.tree.item(child, tags=tuple(current_tags))
                row_count += 1

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
        total_to_delete = len(file_items) + len(orphaned_images)

        # Create progress popup
        progress_popup = tk.Toplevel(self)
        progress_popup.title("Deleting Files...")
        progress_popup.geometry("400x120")
        progress_popup.resizable(False, False)
        progress_popup.transient(self)
        progress_popup.grab_set()

        # Center popup
        x = self.winfo_x() + (self.winfo_width() // 2) - 200
        y = self.winfo_y() + (self.winfo_height() // 2) - 60
        progress_popup.geometry(f"+{x}+{y}")

        # Apply theme
        is_dark = self.dark_mode_enabled.get()
        popup_bg = self.dark_bg if is_dark else self.light_bg
        popup_fg = self.dark_fg if is_dark else 'black'
        progress_popup.configure(bg=popup_bg)

        lbl = tk.Label(progress_popup, text="Starting deletion...",
                      bg=popup_bg, fg=popup_fg, font=("TkDefaultFont", 9))
        lbl.pack(pady=(20, 10), padx=20, fill='x')

        pb = ttk.Progressbar(progress_popup, orient='horizontal', length=360,
                            mode='determinate', style="Blue.Horizontal.TProgressbar")
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

    def toggle_dark_mode(self) -> None:
        """Toggle between dark and light themes and save the preference."""
        if self.dark_mode_enabled.get():
            self.apply_dark_mode()
        else:
            self.apply_light_mode()
        self.save_settings()

    def apply_dark_mode(self) -> None:
        """Apply dark theme styling to all UI components.

        Recursively applies dark colors and styling to the main window
        and all child widgets, including the treeview and headings.
        """
        self.configure(bg=self.dark_bg)
        for widget in self.winfo_children():
            self.apply_dark_mode_recursive(widget)

        # Configure treeview dark theme
        self.style.configure('Treeview',
                           background=self.dark_bg, foreground=self.dark_fg,
                           fieldbackground=self.dark_bg, bordercolor='#555555',
                           lightcolor='#555555', darkcolor='#555555')
        self.style.configure('Treeview.Heading',
                           background='#1a1a1a', foreground=self.dark_fg,
                           relief='raised', borderwidth=1)
        self.style.map('Treeview',
                      background=[('selected', self.selection_bg)],
                      foreground=[('selected', 'white')])
        self.style.map('Treeview.Heading', background=[('active', '#404040')])

        self.update_tag_colors()
        self.apply_display_settings()

    def apply_dark_mode_recursive(self, widget: tk.Misc) -> None:
        """Recursively apply dark theme styling to a widget and its children.

        Args:
            widget: The widget to apply dark styling to
        """
        widget_type = widget.winfo_class()
        w: Any = widget  # Cast to Any for dynamic configure calls
        try:
            if widget_type in ('Frame', 'Labelframe'):
                w.configure(bg=self.dark_bg)
            elif widget_type == 'Label':
                w.configure(bg=self.dark_bg, fg=self.dark_fg)
            elif widget_type == 'Button':
                w.configure(bg='#404040', fg=self.dark_fg, activebackground='#505050',
                           activeforeground=self.dark_fg, highlightbackground=self.dark_bg)
            elif widget_type == 'Entry':
                w.configure(bg='#404040', fg=self.dark_fg, insertbackground=self.dark_fg,
                           selectbackground=self.selection_bg, selectforeground=self.selection_fg,
                           highlightbackground=self.dark_bg, highlightcolor='#505050')
            elif widget_type == 'Checkbutton':
                w.configure(bg=self.dark_bg, fg=self.dark_fg, activebackground=self.dark_bg,
                           activeforeground=self.dark_fg, selectcolor='#404040',
                           highlightbackground=self.dark_bg)
        except tk.TclError:
            pass  # Some widgets may not support all properties

        for child in widget.winfo_children():
            self.apply_dark_mode_recursive(child)

    def apply_light_mode(self) -> None:
        """Apply light theme styling to all UI components.

        Recursively applies light colors and styling to the main window
        and all child widgets, including the treeview and headings.
        """
        self.configure(bg=self.light_bg)
        for widget in self.winfo_children():
            self.apply_light_mode_recursive(widget)

        # Configure treeview light theme
        self.style.configure('Treeview',
                           background='white', foreground='black',
                           fieldbackground='white', bordercolor='#999999',
                           lightcolor='#999999', darkcolor='#999999')
        self.style.configure('Treeview.Heading',
                           background='#e0e0e0', foreground='black',
                           relief='raised', borderwidth=1)
        self.style.map('Treeview',
                      background=[('selected', self.selection_bg)],
                      foreground=[('selected', 'black')])
        self.style.map('Treeview.Heading', background=[('active', '#d0d0d0')])

        self.update_tag_colors()
        self.apply_display_settings()

    def apply_light_mode_recursive(self, widget: tk.Misc) -> None:
        """Recursively apply light theme styling to a widget and its children.

        Args:
            widget: The widget to apply light styling to
        """
        widget_type = widget.winfo_class()
        w: Any = widget  # Cast to Any for dynamic configure calls
        try:
            if widget_type in ('Frame', 'Labelframe'):
                w.configure(bg=self.light_bg)
            elif widget_type == 'Label':
                w.configure(bg=self.light_bg, fg='black')
            elif widget_type == 'Button':
                w.configure(bg='#e0e0e0', fg='black', activebackground='#d0d0d0',
                           activeforeground='black', highlightbackground=self.light_bg)
            elif widget_type == 'Entry':
                w.configure(bg='white', fg='black', insertbackground='black',
                           selectbackground=self.selection_bg, selectforeground=self.selection_fg,
                           highlightbackground=self.light_bg, highlightcolor='#0078d7')
            elif widget_type == 'Checkbutton':
                w.configure(bg=self.light_bg, fg='black', activebackground=self.light_bg,
                           activeforeground=self.light_bg, selectcolor='white',
                           highlightbackground=self.light_bg)
        except tk.TclError:
            pass  # Some widgets may not support all properties

        for child in widget.winfo_children():
            self.apply_light_mode_recursive(child)

    def sort_tree(self, col: str, reverse: bool) -> None:
        """Sort treeview content when a column header is clicked.

        Sorts both parent groups and children within each group,
        maintaining the hierarchical structure while enabling easy organization.

        Args:
            col: Column identifier to sort by ('#0' for filename, 'path' for full path)
            reverse: Whether to sort in reverse order
        """
        # Get all top-level items (groups)
        groups = [(self.tree.item(k, "text"), k) for k in self.tree.get_children('')]

        # Sort groups alphabetically
        groups.sort(key=lambda t: t[0].lower(), reverse=reverse)

        # Rearrange groups in the tree
        for index, (val, k) in enumerate(groups):
            self.tree.move(k, '', index)

            # Also sort children within each group
            children = [(self.tree.set(c, col) if col != '#0' else self.tree.item(c, "text"), c)
                        for c in self.tree.get_children(k)]
            children.sort(key=lambda t: t[0].lower(), reverse=reverse)
            for c_index, (c_val, c_id) in enumerate(children):
                self.tree.move(c_id, k, c_index)

        # Set up reverse sort for next click
        self.tree.heading(col, command=lambda: self.sort_tree(col, not reverse))
        self.refresh_row_colors()

if __name__ == '__main__':
    """Main application entry point.

    Creates and runs the ROM Duplicate Manager application.
    Handles any startup exceptions gracefully.
    """
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
            print(error_msg)
        raise
