import os
import re
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, font as tkfont
from send2trash import send2trash
import configparser

# ---------------------
# Config file handling
# ---------------------
CONFIG_FILE = 'rom_duplicate_manager.ini'

def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    return config

def save_config(dark_mode, row_colors, language, smart_select, scan_images):
    config = configparser.ConfigParser()
    config['Settings'] = {
        'dark_mode': str(dark_mode),
        'row_colors': str(row_colors),
        'language': str(language),
        'smart_select': str(smart_select),
        'scan_images': str(scan_images)
    }
    with open(CONFIG_FILE, 'w') as f:
        config.write(f)

# ---------------------
# Normalize filenames
# ---------------------
def normalize_filename(filename):
    name, _ = os.path.splitext(filename)
    name = re.sub(r'\s*\(.*?\)$', '', name).strip()
    return name

# ---------------------
# Extract version from filename
# ---------------------
def extract_version(filename):
    """Extract version number or date from filename. Returns tuple for comparison."""
    filename_lower = filename.lower()
    name_no_ext, _ = os.path.splitext(filename)

    # 1. Dates: YYYY-MM-DD, YYYY.MM.DD, YYYY_MM_DD, YYYYMMDD
    date_val = (0, 0, 0)
    date_match = re.search(r'(20\d{2}|19\d{2})[.\-_](\d{1,2})[.\-_](\d{1,2})', name_no_ext)
    if date_match:
        try:
            date_val = tuple(map(int, date_match.groups()))
        except ValueError: pass
    else:
        date_match = re.search(r'(?<!\d)(20\d{2}|19\d{2})(\d{2})(\d{2})(?!\d)', name_no_ext)
        if date_match:
            try:
                date_val = tuple(map(int, date_match.groups()))
            except ValueError: pass

    # 2. Explicit version: v1.0, version 2.1, etc.
    v_val = (0,)
    v_matches = re.findall(r'v(?:er(?:sion)?)?[\s\-_]?(\d+(?:\.\d+)*)', name_no_ext, re.IGNORECASE)
    if v_matches:
        try:
            v_val = tuple(map(int, v_matches[-1].split('.')))
        except ValueError: pass

    # 3. Proto/Beta version: (proto 1), (beta 2)
    proto_val = (0,)
    proto_match = re.search(r'\((?:proto|beta)\s*(\d+)\)', filename_lower)
    if proto_match:
        try:
            proto_val = (int(proto_match.group(1)),)
        except ValueError: pass

    # 4. Other numbers in parentheses or at the end
    other_val = (0,)
    p_match = re.search(r'\((\d+)\)', name_no_ext)
    if p_match:
        try:
            other_val = (int(p_match.group(1)),)
        except ValueError: pass
    else:
        t_match = re.search(r'[_\s\-](\d+(?:\.\d+)*)$', name_no_ext)
        if t_match:
            try:
                other_val = tuple(map(int, t_match.group(1).split('.')))
            except ValueError: pass

    # Return a combined tuple for comparison.
    # Date is most significant, then explicit version, then proto version, then others.
    return date_val + v_val + proto_val + other_val

# ---------------------
# Extract languages from filename
# ---------------------
def extract_languages(filename):
    """Extract language codes and video formats from filename."""
    languages = set()

    # Language code mappings
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

    # Region to language mappings
    region_map = {
        'usa': 'English-US',
        'europe': 'English-EU',
        'australia': 'English-EU',
        'uk': 'English-EU',
        'world': 'World',
        'global': 'World'
    }

    # Video format mappings
    format_map = {
        'ntsc': 'NTSC',
        'pal': 'PAL',
        'secam': 'SECAM'
    }

    filename_lower = filename.lower()

    # Extract from parentheses like (En,Fr,De) or (USA, Europe)
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

# ---------------------
# Scan folder
# ---------------------
def scan_folder(folder, recursive=False, extension_filter=None):
    groups = {}

    def process_file(f, full_path):
        if extension_filter:
            _, ext = os.path.splitext(f)
            if ext.lower() not in extension_filter:
                return

        base = normalize_filename(f)
        full_path = full_path.replace('\\', '/')
        groups.setdefault(base, []).append(full_path)

    if recursive:
        for root, dirs, files in os.walk(folder):
            for f in files:
                full_path = os.path.join(root, f)
                process_file(f, full_path)
    else:
        for f in os.listdir(folder):
            full_path = os.path.join(folder, f)
            if os.path.isfile(full_path):
                process_file(f, full_path)

    duplicates = {k:v for k,v in groups.items() if len(v) > 1}
    non_duplicates = {k:v for k,v in groups.items() if len(v) == 1}

    return duplicates, non_duplicates

# ---------------------
# Tooltip handling
# ---------------------
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None
        widget.bind("<Enter>", self.schedule_tip, add="+")
        widget.bind("<Leave>", self.hide_tip, add="+")
        widget.bind("<ButtonPress>", self.hide_tip, add="+")

    def schedule_tip(self, event=None):
        self.hide_tip()
        if self.text:
            self.id = self.widget.after(500, self.show_tip)

    def show_tip(self, event=None):
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
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        tw.attributes("-topmost", True)
        label = tk.Label(tw, text=self.text, justify='left',
                       background="#ffffe0", foreground="black", relief='solid', borderwidth=1,
                       font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
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

def create_tooltip(widget, text):
    if hasattr(widget, 'tooltip'):
        widget.tooltip.text = text
    else:
        widget.tooltip = ToolTip(widget, text)

    # For complex widgets like Combobox, bind to children too
    def bind_children(w):
        for child in w.winfo_children():
            child.bind("<Enter>", widget.tooltip.schedule_tip, add="+")
            child.bind("<Leave>", widget.tooltip.hide_tip, add="+")
            bind_children(child)

    try:
        bind_children(widget)
    except tk.TclError:
        pass

# ---------------------
# Auto-hiding Scrollbar
# ---------------------
class AutoScrollbar(ttk.Scrollbar):
    """A scrollbar that hides itself when not needed."""
    def set(self, low, high):
        if float(low) <= 0.0 and float(high) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        ttk.Scrollbar.set(self, low, high)

# ---------------------
# GUI
# ---------------------
class DuplicateManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ROM Duplicate Manager")
        self.geometry("1100x600")

        config = load_config()
        dark_mode_saved = config.getboolean('Settings', 'dark_mode', fallback=False)
        row_colors_saved = config.getboolean('Settings', 'row_colors',
                                            fallback=config.getboolean('Settings', 'alternate_colors', fallback=True))
        language_saved = config.get('Settings', 'language', fallback='Any')
        smart_select_saved = config.getboolean('Settings', 'smart_select', fallback=False)
        scan_images_saved = config.getboolean('Settings', 'scan_images', fallback=False)

        self.dark_mode_enabled = tk.BooleanVar(value=dark_mode_saved)
        self.row_colors = tk.BooleanVar(value=row_colors_saved)
        self.dark_bg = '#2d2d2d'
        self.dark_fg = '#e0e0e0'
        self.light_bg = '#f0f0f0'
        self.selection_bg = '#3399ff'
        self.selection_fg = 'black'

        self.light_highlight = 'blue'
        self.dark_highlight = '#00d4ff'

        self.folder = tk.StringVar()
        self.filter_text = tk.StringVar()
        self.smart_select = tk.BooleanVar(value=smart_select_saved)
        self.scan_images = tk.BooleanVar(value=scan_images_saved)
        self.include_subfolders = tk.BooleanVar(value=False)
        self.file_type_filter = tk.StringVar(value="Wildcard *.*")
        self.language_filter = tk.StringVar(value=language_saved)

        # File type categories
        self.file_types = {
            "Wildcard *.*": None,
            "Archive": {".zip", ".7z", ".jar", ".lha", ".lzh", ".rar", ".tar", ".gz"},
            "Disk Image": {".iso", ".bin", ".cue", ".img", ".mdf", ".mds", ".nrg", ".ccd", ".chd", ".gdi", ".cdi"},
            "Images": {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif"},
            "Video": {".mp4", ".mpg", ".mpeg", ".avi", ".mov", ".wmv", ".mkv"},
            "System": {
                ".adf", ".hdf", ".cpc", ".dsk", ".cpr", ".do", ".po", ".apple2", ".a26", ".a52", ".a78", ".lnx",
                ".st", ".xfd", ".atr", ".atx", ".com", ".xex", ".cas", ".sap", ".d64", ".d71", ".d81", ".g64",
                ".prg", ".t64", ".tap", ".crt", ".gb", ".gbc", ".gba", ".md", ".smd", ".gen", ".60", ".sms",
                ".nes", ".fds", ".smc", ".sfc", ".fig", ".swc", ".n64", ".v64", ".z64", ".pbp", ".cso", ".neo",
                ".pce", ".sgx", ".ws", ".wsc", ".col", ".int", ".vec", ".min", ".sv", ".gg", ".ngp", ".ngc",
                ".vb", ".32x", ".p8", ".png", ".solarus", ".tic", ".love", ".scummvm", ".ldb", ".nx", ".v32"
            }
        }

        self.filter_text.trace_add('write', self.on_filter_change)
        self._smart_select_trace = self.smart_select.trace_add('write', self.on_smart_select_change)

        self.frame_top = tk.Frame(self, relief='raised', bd=2)
        self.frame_top.pack(fill='x', padx=5, pady=5)

        # Row 1: Folder, Subfolders, File Type, Language, Smart Select
        row1 = tk.Frame(self.frame_top)
        row1.pack(fill='x', padx=2, pady=2)

        tk.Label(row1, text="Folder:").pack(side='left', padx=2)
        self.folder_entry = tk.Entry(row1, textvariable=self.folder, width=30)
        self.folder_entry.pack(side='left', padx=5)
        self.folder_entry.bind('<Return>', lambda e: self.scan())
        create_tooltip(self.folder_entry, "Current folder path. Press Enter to rescan.")

        self.browse_btn = tk.Button(row1, text="Browse", command=self.browse_folder)
        self.browse_btn.pack(side='left')
        create_tooltip(self.browse_btn, "Select a folder to scan for duplicates")

        self.subfolders_check = tk.Checkbutton(row1, text="Sub-folders", variable=self.include_subfolders, command=self.scan)
        self.subfolders_check.pack(side='left', padx=5)
        create_tooltip(self.subfolders_check, "Include sub-folders in the scan")

        tk.Label(row1, text="Type:").pack(side='left', padx=2)
        self.type_combo = ttk.Combobox(row1, textvariable=self.file_type_filter,
                                       values=list(self.file_types.keys()),
                                       state='readonly', width=12)
        self.type_combo.pack(side='left', padx=2)
        self.type_combo.bind('<<ComboboxSelected>>', lambda e: self.scan())
        create_tooltip(self.type_combo, "Filter files by category")

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

        self.smart_select_check = tk.Checkbutton(row1, text="Smart Select", variable=self.smart_select)
        self.smart_select_check.pack(side='left', padx=2)
        create_tooltip(self.smart_select_check, "Automatically mark duplicates for removal based on priority")

        self.scan_images_check = tk.Checkbutton(row1, text="Scan Images", variable=self.scan_images, command=self.on_scan_images_toggle)
        self.scan_images_check.pack(side='left', padx=2)
        create_tooltip(self.scan_images_check, "Enable scanning and automatic deletion of orphaned images in the /images/ sub-folder")

        self.status_label = tk.Label(row1, text="", font=tkfont.Font(size=9, weight='bold'))
        self.status_label.pack(side='left', padx=10)
        create_tooltip(self.status_label, "Summary of scan results")

        # Row 2: Filter and Display controls
        row2 = tk.Frame(self.frame_top)
        row2.pack(fill='x', padx=2, pady=2)

        tk.Label(row2, text="Filter:").pack(side='left', padx=5)
        self.filter_entry = tk.Entry(row2, textvariable=self.filter_text, width=15)
        self.filter_entry.pack(side='left', padx=5)
        create_tooltip(self.filter_entry, "Filter the list by filename")

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

        self.tree.heading('#0', text='Filename')
        self.tree.heading('path', text='Full Path')
        self.tree.column('#0', width=350)
        self.tree.column('path', width=700)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        self.tree.bind('<Button-1>', self.on_tree_click)

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=5)

        self.delete_button = tk.Button(self.button_frame, text="Delete Selected", command=self.delete_selected)
        self.delete_button.pack(side='left', padx=5)
        self.update_delete_button_tooltip()

        # Progress bar for deletions
        self.progress_frame = tk.Frame(self)
        self.progress_frame.pack(fill='x', padx=10, pady=5)
        self.progress_frame.pack_propagate(False)
        self.progress_frame.config(height=60)

        # Inner frame to center and limit width to 50%
        self.progress_inner = tk.Frame(self.progress_frame)
        self.progress_inner.place(relx=0.5, rely=0.5, anchor='center', relwidth=0.5)

        self.progress_bar = ttk.Progressbar(self.progress_inner, orient='horizontal',
                                          mode='determinate', style="Blue.Horizontal.TProgressbar")
        self.progress_label = tk.Label(self.progress_inner, text="")

        self.duplicates = {}
        self.non_duplicates = {}

        if self.dark_mode_enabled.get():
            self.apply_dark_mode()
        else:
            self.apply_light_mode()

        self.apply_display_settings()

    def save_settings(self):
        save_config(self.dark_mode_enabled.get(), self.row_colors.get(),
                    self.language_filter.get(), self.smart_select.get(),
                    self.scan_images.get())

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder.set(folder)
            self.scan()

    def get_orphaned_images(self, keep_filenames=None):
        folder = self.folder.get()
        if not folder or not os.path.isdir(folder):
            return []
        images_folder = os.path.join(folder, 'images')
        if not os.path.isdir(images_folder):
            return []

        if keep_filenames is None:
            keep_filenames = set()
            for paths in self.duplicates.values():
                for path in paths:
                    keep_filenames.add(os.path.splitext(os.path.basename(path))[0].lower())
            for paths in self.non_duplicates.values():
                for path in paths:
                    keep_filenames.add(os.path.splitext(os.path.basename(path))[0].lower())

        image_extensions = self.file_types["Images"]
        orphaned = []
        for f in os.listdir(images_folder):
            full_path = os.path.join(images_folder, f)
            if os.path.isfile(full_path):
                name, ext = os.path.splitext(f)
                if ext.lower() in image_extensions:
                    match_name = name.lower()
                    if match_name.endswith("-image"):
                        match_name = match_name[:-6]
                    if match_name not in keep_filenames:
                        orphaned.append(full_path)
        return orphaned

    def scan(self):
        folder = self.folder.get()
        if not folder or not os.path.isdir(folder):
            return

        ext_filter = self.file_types.get(self.file_type_filter.get())
        self.duplicates, self.non_duplicates = scan_folder(folder, self.include_subfolders.get(), ext_filter)

        status = f"Found {len(self.duplicates)} duplicate group(s) and {len(self.non_duplicates)} unique file(s)."

        if self.scan_images.get():
            orphaned = self.get_orphaned_images()
            if orphaned:
                status += f" | {len(orphaned)} orphaned image(s) found."

        if hasattr(self, 'status_label'):
            self.status_label.config(text=status)

        self.populate_tree()

    def on_language_change(self, event=None):
        if hasattr(self, 'tree') and self.tree.get_children():
            self.apply_base_suggestions()
        self.save_settings()

    def on_scan_images_toggle(self):
        self.update_delete_button_tooltip()
        self.scan()
        self.save_settings()

    def update_delete_button_tooltip(self):
        if self.scan_images.get():
            create_tooltip(self.delete_button, "Move all marked files AND orphaned images to the recycle bin")
        else:
            create_tooltip(self.delete_button, "Move all marked or selected files to the recycle bin")

    def on_smart_select_change(self, *args):
        if not hasattr(self, 'tree') or not self.tree.get_children():
            self.save_settings()
            return

        if self.smart_select.get():
            has_manual = False
            for item in self.tree.tag_has('manual'):
                has_manual = True
                break

            if has_manual:
                confirm = messagebox.askokcancel("Warning", "Smart Select will override your current filters. Proceed?")
                if not confirm:
                    self.smart_select.trace_remove('write', self._smart_select_trace)
                    self.smart_select.set(False)
                    self._smart_select_trace = self.smart_select.trace_add('write', self.on_smart_select_change)
                    self.save_settings()
                    return
                else:
                    for item in self.tree.tag_has('manual'):
                        tags = list(self.tree.item(item, 'tags'))
                        if 'manual' in tags: tags.remove('manual')
                        self.tree.item(item, tags=tuple(tags))

        self.apply_base_suggestions()
        self.save_settings()

    def on_tree_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item: return
        parent = self.tree.parent(item)
        if not parent: return

        tags = list(self.tree.item(item, 'tags'))
        row_tag = next((t for t in tags if t in ('oddrow', 'evenrow')), None)
        filtered_tag = 'filtered' if 'filtered' in tags else None

        if 'base' in tags:
            tags = ['to_remove', 'manual']
        elif 'to_remove' in tags:
            tags = ['base', 'manual']
        else:
            return

        if row_tag: tags.append(row_tag)
        if filtered_tag: tags.append(filtered_tag)

        self.tree.item(item, tags=tuple(tags))
        return "break"

    def get_file_priority(self, filepath):
        lang_pref = self.language_filter.get()
        filename = os.path.basename(filepath)
        filename_lower = filename.lower()

        # Root folder priority
        root_folder = self.folder.get().replace('\\', '/')
        is_not_in_root = 0 if os.path.dirname(filepath.replace('\\', '/')) == root_folder else 1

        is_low_priority = 1 if re.search(r'\(proto|\(demo|\(sample|\(beta', filename_lower) else 0
        languages = extract_languages(filename)
        actual_langs = languages - {'Unknown'}
        num_langs = len(actual_langs)
        version = extract_version(filename)
        length = len(filename)
        is_world = 1 if 'World' in languages else 0
        has_lang = 1 if (lang_pref != 'Any' and lang_pref in languages) else 0
        format_priority = 0
        if lang_pref != 'Any':
            ntsc_regions = ('English-US', 'Japanese', 'Korean', 'Chinese')
            pal_regions = ('English-EU', 'French', 'German', 'Spanish', 'Italian', 'Dutch', 'Portuguese', 'Swedish')
            if lang_pref in ntsc_regions:
                if 'NTSC' in languages: format_priority = 2
                elif 'PAL' in languages: format_priority = 1
                elif 'SECAM' in languages: format_priority = -1
            elif lang_pref in pal_regions:
                if 'PAL' in languages: format_priority = 2
                elif 'SECAM' in languages: format_priority = 1
                elif 'NTSC' in languages: format_priority = -1
        return (is_not_in_root, is_low_priority) + tuple(-v for v in version) + (-is_world, -has_lang, -format_priority, -num_langs, length, filename)

    def get_base_file(self, files):
        return min(files, key=self.get_file_priority)

    def apply_base_suggestions(self):
        for parent in self.tree.get_children():
            parent_text = self.tree.item(parent, 'text')
            if parent_text in self.duplicates:
                files = self.duplicates[parent_text]
                base_file = self.get_base_file(files)
                for child in self.tree.get_children(parent):
                    current_tags = list(self.tree.item(child, 'tags'))
                    if 'manual' in current_tags: continue
                    child_path = self.tree.item(child, 'values')[0]
                    current_tags = [t for t in current_tags if t not in ('base', 'to_remove')]
                    if self.smart_select.get():
                        if child_path == base_file: current_tags.append('base')
                        else: current_tags.append('to_remove')
                    self.tree.item(child, tags=tuple(current_tags))
        self.update_tag_colors()
        self.apply_filter()

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        for base_name in sorted(self.duplicates.keys()):
            files = self.duplicates[base_name]
            parent_id = self.tree.insert('', 'end', text=base_name, open=True, tags=('duplicate_group',))
            base_file = self.get_base_file(files)
            sorted_files = sorted(files, key=self.get_file_priority)
            for f in sorted_files:
                child_id = self.tree.insert(parent_id, 'end', text=os.path.basename(f), values=(f,))
                if self.smart_select.get():
                    if f == base_file: self.tree.item(child_id, tags=('base',))
                    else: self.tree.item(child_id, tags=('to_remove',))
        for base_name in sorted(self.non_duplicates.keys()):
            files = self.non_duplicates[base_name]
            parent_id = self.tree.insert('', 'end', text=base_name, open=False, tags=('unique_group',))
            for f in files: self.tree.insert(parent_id, 'end', text=os.path.basename(f), values=(f,))
        self.update_tag_colors()
        self.refresh_row_colors()
        self.apply_filter()

    def on_filter_change(self, *args):
        self.apply_filter()

    def clear_filter(self):
        self.filter_text.set('')
        self.apply_filter()

    def mark_filtered_keep(self):
        text = self.filter_text.get().lower()
        if not text: return
        for parent in self.tree.get_children():
            for child in self.tree.get_children(parent):
                filename = self.tree.item(child, 'text').lower()
                if text in filename:
                    tags = list(self.tree.item(child, 'tags'))
                    tags = [t for t in tags if t not in ('base', 'to_remove')]
                    tags.append('base')
                    if 'manual' not in tags: tags.append('manual')
                    self.tree.item(child, tags=tuple(tags))
        self.update_tag_colors()

    def mark_filtered_delete(self):
        text = self.filter_text.get().lower()
        if not text: return
        for parent in self.tree.get_children():
            for child in self.tree.get_children(parent):
                filename = self.tree.item(child, 'text').lower()
                if text in filename:
                    tags = list(self.tree.item(child, 'tags'))
                    tags = [t for t in tags if t not in ('base', 'to_remove')]
                    tags.append('to_remove')
                    if 'manual' not in tags: tags.append('manual')
                    self.tree.item(child, tags=tuple(tags))
        self.update_tag_colors()

    def reset_marks(self):
        for parent in self.tree.get_children():
            for child in self.tree.get_children(parent):
                tags = list(self.tree.item(child, 'tags'))
                tags = [t for t in tags if t not in ('base', 'to_remove', 'manual')]
                self.tree.item(child, tags=tuple(tags))
        if self.smart_select.get(): self.apply_base_suggestions()
        else: self.update_tag_colors()

    def apply_filter(self):
        text = self.filter_text.get().lower()
        for parent in self.tree.get_children():
            has_matching_child = False
            for child in self.tree.get_children(parent):
                filename = self.tree.item(child, 'text')
                # Ignore " - Copy" for filtering
                filter_filename = filename.replace(" - Copy", "").lower()
                matches_filter = text and text in filter_filename
                if matches_filter or not text: has_matching_child = True
                current_tags = list(self.tree.item(child, 'tags'))
                if 'filtered' in current_tags: current_tags.remove('filtered')
                if matches_filter: current_tags.append('filtered')
                self.tree.item(child, tags=tuple(current_tags))
            if text and not has_matching_child: self.tree.item(parent, open=False)
            else: self.tree.item(parent, open=True)
        self.update_tag_colors()

    def update_tag_colors(self):
        normal_font = tkfont.nametofont("TkDefaultFont")
        strike_font = normal_font.copy()
        strike_font.configure(overstrike=True)
        bold_font = normal_font.copy()
        bold_font.configure(weight='bold')
        self.tree.tag_configure('base', foreground='green')
        self.tree.tag_configure('to_remove', foreground='red', font=strike_font)
        if self.dark_mode_enabled.get():
            self.tree.tag_configure('filtered', background='#4b5320', font=bold_font)
        else:
            self.tree.tag_configure('filtered', background='#ffffcc', font=bold_font)

    def toggle_row_colors(self):
        self.apply_display_settings()
        self.save_settings()

    def apply_display_settings(self):
        self.style.theme_use('clam')
        is_dark = self.dark_mode_enabled.get()
        bg = self.dark_bg if is_dark else 'white'
        fg = 'white' if is_dark else 'black'

        trough_color = '#1a1a1a' if is_dark else '#e0e0e0'
        vsc_blue = '#007acc'

        self.style.configure("Blue.Horizontal.TProgressbar",
                             background=vsc_blue,
                             troughcolor=trough_color,
                             bordercolor=trough_color,
                             lightcolor=vsc_blue,
                             darkcolor=vsc_blue)

        # Label colors match theme, no background
        self.progress_label.config(bg=bg, fg=fg, anchor='center')
        self.progress_inner.config(bg=bg)

        self.style.configure('Treeview', background=bg, fieldbackground=bg, foreground=fg, rowheight=25, borderwidth=0, relief='flat')
        self.style.map('Treeview', background=[('selected', bg)], foreground=[('selected', '')])
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

    def refresh_row_colors(self):
        row_count = 0
        for parent in self.tree.get_children():
            p_tags = list(self.tree.item(parent, 'tags'))
            p_tags = [t for t in p_tags if t not in ('oddrow', 'evenrow')]
            p_tags.append('evenrow' if row_count % 2 == 0 else 'oddrow')
            self.tree.item(parent, tags=tuple(p_tags))
            row_count += 1
            for child in self.tree.get_children(parent):
                current_tags = list(self.tree.item(child, 'tags'))
                current_tags = [t for t in current_tags if t not in ('oddrow', 'evenrow')]
                current_tags.append('evenrow' if row_count % 2 == 0 else 'oddrow')
                self.tree.item(child, tags=tuple(current_tags))
                row_count += 1

    def delete_selected(self):
        selected = self.tree.selection()
        file_items = [item for item in selected if self.tree.parent(item)]
        if not file_items:
            for item in self.tree.tag_has('to_remove'): file_items.append(item)

        orphaned_images = []
        if self.scan_images.get():
            # Identify files being kept to find images that will become orphaned
            all_files = []
            for paths in self.duplicates.values(): all_files.extend(paths)
            for paths in self.non_duplicates.values(): all_files.extend(paths)

            files_to_delete_paths = set()
            for item in file_items:
                values = self.tree.item(item, 'values')
                if values: files_to_delete_paths.add(values[0])

            keep_filenames = set()
            for path in all_files:
                if path not in files_to_delete_paths:
                    keep_filenames.add(os.path.splitext(os.path.basename(path))[0].lower())

            orphaned_images = self.get_orphaned_images(keep_filenames)

        if not file_items and not orphaned_images:
            messagebox.showinfo("Info", "No files selected or marked for removal")
            return

        total_to_delete = len(file_items) + len(orphaned_images)

        if file_items and orphaned_images:
            msg = f"You are about to move {len(file_items)} marked file(s) AND {len(orphaned_images)} orphaned image(s) to the recycle bin"
        elif file_items:
            msg = f"You are about to move {len(file_items)} marked file(s) to the recycle bin"
        else:
            msg = f"You are about to move {len(orphaned_images)} orphaned image(s) to the recycle bin"

        confirm = messagebox.askokcancel("Confirm Delete", msg)
        if not confirm: return

        # Show progress label above progress bar, both centered and 50% width
        self.progress_label.pack(side='top', fill='x')
        self.progress_bar.pack(side='top', fill='x', pady=(5, 0))

        self.progress_bar['maximum'] = total_to_delete
        self.progress_bar['value'] = 0
        deleted_count = 0
        parents_to_check = set()

        # Delete marked files
        for i, item in enumerate(file_items):
            values = self.tree.item(item, 'values')
            if values:
                path = values[0]
                filename = os.path.basename(path)
                display_name = filename[:57] + "..." if len(filename) > 60 else filename
                self.progress_label.config(text=f"Deleting: {display_name}")
                self.progress_bar['value'] = i + 1
                self.update_idletasks()
                path = path.replace('/', os.sep)
                if path and os.path.exists(path):
                    try:
                        send2trash(path)
                        deleted_count += 1
                        parent = self.tree.parent(item)
                        parents_to_check.add(parent)
                        self.tree.delete(item)
                        parent_text = self.tree.item(parent, 'text')
                        normalized_path = path.replace(os.sep, '/')
                        if parent_text in self.duplicates:
                            if normalized_path in self.duplicates[parent_text]: self.duplicates[parent_text].remove(normalized_path)
                        elif parent_text in self.non_duplicates:
                            if normalized_path in self.non_duplicates[parent_text]: self.non_duplicates[parent_text].remove(normalized_path)
                    except Exception as e: messagebox.showerror("Error", f"Failed to delete {path}: {str(e)}")

        # Delete orphaned images
        start_idx = len(file_items)
        for i, path in enumerate(orphaned_images):
            filename = os.path.basename(path)
            display_name = filename[:57] + "..." if len(filename) > 60 else filename
            self.progress_label.config(text=f"Deleting Image: {display_name}")
            self.progress_bar['value'] = start_idx + i + 1
            self.update_idletasks()
            try:
                send2trash(path.replace('/', os.sep))
                deleted_count += 1
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete {path}: {str(e)}")

        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()

        for parent in parents_to_check:
            children = self.tree.get_children(parent)
            parent_text = self.tree.item(parent, 'text')
            if not children:
                if parent_text in self.duplicates: del self.duplicates[parent_text]
                if parent_text in self.non_duplicates: del self.non_duplicates[parent_text]
                self.tree.delete(parent)
            elif len(children) == 1 and parent_text in self.duplicates:
                child_path = self.tree.item(children[0], 'values')[0]
                self.non_duplicates[parent_text] = [child_path]
                del self.duplicates[parent_text]
                self.tree.item(parent, open=False, tags=('unique_group',))

        self.refresh_row_colors()
        messagebox.showinfo("Done", f"Deleted {deleted_count} item(s)")
        self.scan()

    def toggle_dark_mode(self):
        if self.dark_mode_enabled.get(): self.apply_dark_mode()
        else: self.apply_light_mode()
        self.save_settings()

    def apply_dark_mode(self):
        self.configure(bg=self.dark_bg)
        for widget in self.winfo_children(): self.apply_dark_mode_recursive(widget)
        self.style.configure('Treeview', background=self.dark_bg, foreground=self.dark_fg, fieldbackground=self.dark_bg, bordercolor='#555555', lightcolor='#555555', darkcolor='#555555')
        self.style.configure('Treeview.Heading', background='#1a1a1a', foreground=self.dark_fg, relief='raised', borderwidth=1)
        self.style.map('Treeview', background=[('selected', self.selection_bg)], foreground=[('selected', self.selection_fg)])
        self.style.map('Treeview.Heading', background=[('active', '#404040')])
        self.update_tag_colors()
        self.apply_display_settings()

    def apply_dark_mode_recursive(self, widget):
        widget_type = widget.winfo_class()
        try:
            if widget_type in ('Frame', 'Labelframe'): widget.configure(bg=self.dark_bg)
            elif widget_type == 'Label': widget.configure(bg=self.dark_bg, fg=self.dark_fg)
            elif widget_type == 'Button': widget.configure(bg='#404040', fg=self.dark_fg, activebackground='#505050', activeforeground=self.dark_fg, highlightbackground=self.dark_bg)
            elif widget_type == 'Entry': widget.configure(bg='#404040', fg=self.dark_fg, insertbackground=self.dark_fg, selectbackground=self.selection_bg, selectforeground=self.selection_fg, highlightbackground=self.dark_bg, highlightcolor='#505050')
            elif widget_type == 'Checkbutton': widget.configure(bg=self.dark_bg, fg=self.dark_fg, activebackground=self.dark_bg, activeforeground=self.dark_fg, selectcolor='#404040', highlightbackground=self.dark_bg)
        except tk.TclError: pass
        for child in widget.winfo_children(): self.apply_dark_mode_recursive(child)

    def apply_light_mode(self):
        self.configure(bg=self.light_bg)
        for widget in self.winfo_children(): self.apply_light_mode_recursive(widget)
        self.style.configure('Treeview', background='white', foreground='black', fieldbackground='white', bordercolor='#999999', lightcolor='#999999', darkcolor='#999999')
        self.style.configure('Treeview.Heading', background='#e0e0e0', foreground='black', relief='raised', borderwidth=1)
        self.style.map('Treeview', background=[('selected', self.selection_bg)], foreground=[('selected', self.selection_fg)])
        self.style.map('Treeview.Heading', background=[('active', '#d0d0d0')])
        self.update_tag_colors()
        self.apply_display_settings()

    def apply_light_mode_recursive(self, widget):
        widget_type = widget.winfo_class()
        try:
            if widget_type in ('Frame', 'Labelframe'): widget.configure(bg=self.light_bg)
            elif widget_type == 'Label': widget.configure(bg=self.light_bg, fg='black')
            elif widget_type == 'Button': widget.configure(bg='#e0e0e0', fg='black', activebackground='#d0d0d0', activeforeground='black', highlightbackground=self.light_bg)
            elif widget_type == 'Entry': widget.configure(bg='white', fg='black', insertbackground='black', selectbackground=self.selection_bg, selectforeground=self.selection_fg, highlightbackground=self.light_bg, highlightcolor='#0078d7')
            elif widget_type == 'Checkbutton': widget.configure(bg=self.light_bg, fg='black', activebackground=self.light_bg, activeforeground=self.light_bg, selectcolor='white', highlightbackground=self.light_bg)
        except tk.TclError: pass
        for child in widget.winfo_children(): self.apply_light_mode_recursive(child)

if __name__ == '__main__':
    app = DuplicateManager()
    app.mainloop()
