import os
import re
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
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

def save_config(dark_mode, show_grid, alternate_colors):
    config = configparser.ConfigParser()
    config['Settings'] = {
        'dark_mode': str(dark_mode),
        'show_grid': str(show_grid),
        'alternate_colors': str(alternate_colors)
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
    """Extract version number from filename. Returns tuple for comparison."""
    # Pattern 1: v1.2, ver2.0, version3.1
    match = re.search(r'[_\s\-]?v(?:er(?:sion)?)?[\s\-_]?(\d+(?:\.\d+)*)', filename, re.IGNORECASE)
    if match:
        version_str = match.group(1)
        try:
            return tuple(map(int, version_str.split('.')))
        except ValueError:
            pass
    
    # Pattern 2: (1), (2)
    match = re.search(r'\((\d+)\)', filename)
    if match:
        try:
            return (int(match.group(1)),)
        except ValueError:
            pass
    
    # Pattern 3: trailing numbers like _1, -2
    match = re.search(r'[_\s\-](\d+)(?:\.\d+)*$', filename)
    if match:
        version_str = match.group(1)
        try:
            return tuple(map(int, version_str.split('.')))
        except ValueError:
            pass
    
    return (0,)

# ---------------------
# Scan folder
# ---------------------
def scan_folder(folder):
    groups = {}
    for f in os.listdir(folder):
        full_path = os.path.join(folder, f)
        if os.path.isfile(full_path):
            base = normalize_filename(f)
            full_path = full_path.replace('\\', '/')
            groups.setdefault(base, []).append(full_path)
    
    duplicates = {k:v for k,v in groups.items() if len(v) > 1}
    non_duplicates = {k:v for k,v in groups.items() if len(v) == 1}
    
    return duplicates, non_duplicates

# ---------------------
# GUI
# ---------------------
class DuplicateManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Base Name Duplicate Manager")
        self.geometry("1000x600")

        config = load_config()
        dark_mode_saved = config.getboolean('Settings', 'dark_mode', fallback=False)
        show_grid_saved = config.getboolean('Settings', 'show_grid', fallback=True)
        alternate_colors_saved = config.getboolean('Settings', 'alternate_colors', fallback=True)

        self.dark_mode_enabled = tk.BooleanVar(value=dark_mode_saved)
        self.show_grid = tk.BooleanVar(value=show_grid_saved)
        self.alternate_colors = tk.BooleanVar(value=alternate_colors_saved)
        self.dark_bg = '#2d2d2d'
        self.dark_fg = '#e0e0e0'
        self.light_bg = '#f0f0f0'
        self.selection_bg = '#3399ff'
        self.selection_fg = 'black'
        
        self.light_highlight = 'blue'
        self.dark_highlight = '#00d4ff'
        
        self.light_fade = '#999999'
        self.dark_fade = '#666666'

        self.folder = tk.StringVar()
        self.filter_text = tk.StringVar()
        self.auto_highlight = tk.BooleanVar()
        self.auto_select_filter = tk.BooleanVar()
        self.suggest_base = tk.BooleanVar()
        self.select_other = tk.BooleanVar()
        
        self.filter_text.trace_add('write', self.on_filter_change)
        self.suggest_base.trace_add('write', self.on_suggest_base_change)
        self.select_other.trace_add('write', self.on_select_other_change)

        self.frame_top = tk.Frame(self, relief='raised', bd=2)
        self.frame_top.pack(fill='x', padx=5, pady=5)

        tk.Label(self.frame_top, text="Folder:").pack(side='left', padx=2)
        tk.Entry(self.frame_top, textvariable=self.folder, width=50).pack(side='left', padx=5)
        tk.Button(self.frame_top, text="Browse", command=self.browse_folder).pack(side='left')
        tk.Button(self.frame_top, text="Scan", command=self.scan).pack(side='left', padx=5)
        
        tk.Checkbutton(self.frame_top, text="Suggest-base", variable=self.suggest_base).pack(side='left', padx=2)
        tk.Checkbutton(self.frame_top, text="Select other", variable=self.select_other).pack(side='left', padx=2)

        ttk.Separator(self.frame_top, orient='vertical').pack(side='left', fill='y', padx=10)

        tk.Label(self.frame_top, text="Filter:").pack(side='left', padx=5)
        self.filter_entry = tk.Entry(self.frame_top, textvariable=self.filter_text, width=20)
        self.filter_entry.pack(side='left', padx=5)
        tk.Button(self.frame_top, text="Clear", command=self.clear_filter).pack(side='left', padx=2)
        
        tk.Checkbutton(self.frame_top, text="Auto-highlight", variable=self.auto_highlight, 
                      command=self.apply_filter).pack(side='left', padx=5)
        tk.Checkbutton(self.frame_top, text="Auto-select", variable=self.auto_select_filter, 
                      command=self.apply_filter).pack(side='left', padx=5)
        
        ttk.Separator(self.frame_top, orient='vertical').pack(side='left', fill='y', padx=10)
        
        tk.Checkbutton(self.frame_top, text="Show Grid", variable=self.show_grid, 
                      command=self.toggle_grid).pack(side='left', padx=5)
        tk.Checkbutton(self.frame_top, text="Alternate colors", variable=self.alternate_colors, 
                      command=self.toggle_alternate_colors).pack(side='left', padx=5)
        tk.Checkbutton(self.frame_top, text="Dark Mode", variable=self.dark_mode_enabled, 
                      command=self.toggle_dark_mode).pack(side='left', padx=5)

        tree_frame = tk.Frame(self, relief='sunken', bd=2)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        self.style = ttk.Style(self)
        self.tree = ttk.Treeview(tree_frame, columns=('path',), selectmode='extended',
                                yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        self.tree.heading('#0', text='Filename')
        self.tree.heading('path', text='Full Path')
        self.tree.column('path', width=700)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.delete_button = tk.Button(self, text="Delete Selected", command=self.delete_selected)
        self.delete_button.pack(pady=5)

        self.duplicates = {}
        self.non_duplicates = {}
        
        if self.dark_mode_enabled.get():
            self.apply_dark_mode()
        else:
            self.apply_light_mode()
        
        self.apply_display_settings()

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder.set(folder)

    def scan(self):
        folder = self.folder.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder")
            return

        self.duplicates, self.non_duplicates = scan_folder(folder)
        
        if not self.duplicates:
            messagebox.showinfo("No Duplicates", 
                              f"No duplicate files found in the folder.\nShowing {len(self.non_duplicates)} unique file(s).")
        else:
            messagebox.showinfo("Scan Complete", 
                              f"Found {len(self.duplicates)} duplicate group(s) and {len(self.non_duplicates)} unique file(s).")
        
        self.populate_tree()

    def on_suggest_base_change(self, *args):
        if hasattr(self, 'tree') and self.tree.get_children():
            self.apply_base_suggestions()

    def apply_base_suggestions(self):
        for parent in self.tree.get_children():
            parent_text = self.tree.item(parent, 'text')
            if parent_text in self.duplicates:
                files = self.duplicates[parent_text]
                
                def file_priority(filepath):
                    filename = os.path.basename(filepath)
                    version = extract_version(filename)
                    length = len(filename)
                    return tuple(-v for v in version) + (length,)
                
                base_file = min(files, key=file_priority)
                
                for child in self.tree.get_children(parent):
                    child_path = self.tree.item(child, 'values')[0]
                    current_tags = list(self.tree.item(child, 'tags'))
                    
                    current_tags = [t for t in current_tags if t != 'base']
                    
                    if self.suggest_base.get() and child_path == base_file:
                        current_tags.append('base')
                    
                    self.tree.item(child, tags=tuple(current_tags))
        
        self.update_tag_colors()
        self.apply_filter()

    def on_select_other_change(self, *args):
        if self.select_other.get():
            self.apply_select_other()
        else:
            self.tree.selection_remove(*self.tree.selection())

    def apply_select_other(self):
        self.tree.selection_remove(*self.tree.selection())
        for parent in self.tree.get_children():
            for child in self.tree.get_children(parent):
                tags = self.tree.item(child, 'tags')
                if 'base' not in tags:
                    self.tree.selection_add(child)

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        
        for base_name, files in self.duplicates.items():
            parent_id = self.tree.insert('', 'end', text=base_name, open=True, tags=('duplicate_group',))
            
            def file_priority(filepath):
                filename = os.path.basename(filepath)
                version = extract_version(filename)
                length = len(filename)
                return tuple(-v for v in version) + (length,)
            
            base_file = min(files, key=file_priority)
            
            for f in files:
                child_id = self.tree.insert(parent_id, 'end', text=os.path.basename(f), values=(f,))
                if self.suggest_base.get() and f == base_file:
                    self.tree.item(child_id, tags=('base',))
        
        for base_name, files in self.non_duplicates.items():
            parent_id = self.tree.insert('', 'end', text=base_name, open=False, tags=('unique_group',))
            for f in files:
                self.tree.insert(parent_id, 'end', text=os.path.basename(f), values=(f,))
        
        self.update_tag_colors()
        self.refresh_row_colors()
        self.apply_filter()

    def on_filter_change(self, *args):
        self.apply_filter()

    def clear_filter(self):
        self.filter_text.set('')
        self.auto_highlight.set(False)
        self.auto_select_filter.set(False)
        self.tree.selection_remove(*self.tree.selection())
        self.apply_filter()

    def apply_filter(self):
        text = self.filter_text.get().lower()
        
        if not self.auto_select_filter.get():
            pass
        else:
            self.tree.selection_remove(*self.tree.selection())
        
        for parent in self.tree.get_children():
            has_matching_child = False
            
            for child in self.tree.get_children(parent):
                filename = self.tree.item(child, 'text').lower()
                matches_filter = text and text in filename
                
                if matches_filter or not text:
                    has_matching_child = True
                
                current_tags = list(self.tree.item(child, 'tags'))
                
                is_base = 'base' in current_tags
                
                if 'filtered' in current_tags:
                    current_tags.remove('filtered')
                
                has_oddrow = 'oddrow' in current_tags
                has_evenrow = 'evenrow' in current_tags
                
                new_tags = []
                if is_base:
                    new_tags.append('base')
                if has_oddrow:
                    new_tags.append('oddrow')
                if has_evenrow:
                    new_tags.append('evenrow')
                
                if self.auto_highlight.get() and matches_filter:
                    new_tags.append('filtered')
                
                self.tree.item(child, tags=tuple(new_tags))
                
                if self.auto_select_filter.get() and matches_filter:
                    self.tree.selection_add(child)
            
            if text and not has_matching_child:
                self.tree.item(parent, open=False)
            else:
                self.tree.item(parent, open=True)
        
        self.update_tag_colors()

    def update_tag_colors(self):
        highlight_color = self.dark_highlight if self.dark_mode_enabled.get() else self.light_highlight
        fade_color = self.dark_fade if self.dark_mode_enabled.get() else self.light_fade
        
        self.tree.tag_configure('base', foreground=fade_color)
        self.tree.tag_configure('filtered', foreground=highlight_color)

    def toggle_grid(self):
        self.apply_display_settings()
        save_config(self.dark_mode_enabled.get(), self.show_grid.get(), self.alternate_colors.get())

    def toggle_alternate_colors(self):
        self.apply_display_settings()
        save_config(self.dark_mode_enabled.get(), self.show_grid.get(), self.alternate_colors.get())

    def apply_display_settings(self):
        if self.show_grid.get():
            if self.dark_mode_enabled.get():
                self.style.layout('Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
                self.style.configure('Treeview', rowheight=25, borderwidth=1, relief='solid')
            else:
                self.style.layout('Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
                self.style.configure('Treeview', rowheight=25, borderwidth=1, relief='solid')
        else:
            self.style.configure('Treeview', rowheight=25, borderwidth=0)
        
        if self.alternate_colors.get():
            if self.dark_mode_enabled.get():
                self.tree.tag_configure('oddrow', background='#3a3a3a')
                self.tree.tag_configure('evenrow', background='#2d2d2d')
            else:
                self.tree.tag_configure('oddrow', background='#e8e8e8')
                self.tree.tag_configure('evenrow', background='white')
        else:
            if self.dark_mode_enabled.get():
                self.tree.tag_configure('oddrow', background='#2d2d2d')
                self.tree.tag_configure('evenrow', background='#2d2d2d')
            else:
                self.tree.tag_configure('oddrow', background='white')
                self.tree.tag_configure('evenrow', background='white')
        
        self.refresh_row_colors()

    def refresh_row_colors(self):
        row_count = 0
        for parent in self.tree.get_children():
            for child in self.tree.get_children(parent):
                current_tags = list(self.tree.item(child, 'tags'))
                
                current_tags = [t for t in current_tags if t not in ('oddrow', 'evenrow')]
                
                if row_count % 2 == 0:
                    current_tags.append('evenrow')
                else:
                    current_tags.append('oddrow')
                
                self.tree.item(child, tags=tuple(current_tags))
                row_count += 1

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "No files selected")
            return

        file_items = [item for item in selected if self.tree.parent(item)]
        if not file_items:
            messagebox.showinfo("Info", "No valid file nodes selected")
            return

        confirm = messagebox.askyesno("Confirm Delete", 
                                     f"Are you sure you want to delete {len(file_items)} file(s)?")
        if not confirm:
            return

        deleted_count = 0
        parents_to_check = set()
        
        for item in file_items:
            values = self.tree.item(item, 'values')
            if values:
                path = values[0]
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
                            if normalized_path in self.duplicates[parent_text]:
                                self.duplicates[parent_text].remove(normalized_path)
                        elif parent_text in self.non_duplicates:
                            if normalized_path in self.non_duplicates[parent_text]:
                                self.non_duplicates[parent_text].remove(normalized_path)
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to delete {path}: {str(e)}")

        for parent in parents_to_check:
            children = self.tree.get_children(parent)
            parent_text = self.tree.item(parent, 'text')
            
            if not children:
                if parent_text in self.duplicates:
                    del self.duplicates[parent_text]
                if parent_text in self.non_duplicates:
                    del self.non_duplicates[parent_text]
                self.tree.delete(parent)
            elif len(children) == 1 and parent_text in self.duplicates:
                child_path = self.tree.item(children[0], 'values')[0]
                self.non_duplicates[parent_text] = [child_path]
                del self.duplicates[parent_text]
                self.tree.item(parent, open=False, tags=('unique_group',))

        self.refresh_row_colors()
        
        messagebox.showinfo("Done", f"Deleted {deleted_count} file(s)")

    def toggle_dark_mode(self):
        if self.dark_mode_enabled.get():
            self.apply_dark_mode()
        else:
            self.apply_light_mode()
        
        save_config(self.dark_mode_enabled.get(), self.show_grid.get(), self.alternate_colors.get())

    def apply_dark_mode(self):
        self.configure(bg=self.dark_bg)
        
        for widget in self.winfo_children():
            self.apply_dark_mode_recursive(widget)
        
        self.style.theme_use('default')
        self.style.configure('Treeview',
                           background=self.dark_bg,
                           foreground=self.dark_fg,
                           fieldbackground=self.dark_bg)
        self.style.configure('Treeview.Heading',
                           background='#1a1a1a',
                           foreground=self.dark_fg,
                           relief='raised',
                           borderwidth=1)
        self.style.map('Treeview',
                      background=[('selected', self.selection_bg)],
                      foreground=[('selected', self.selection_fg)])
        self.style.map('Treeview.Heading',
                      background=[('active', '#404040')])
        
        self.update_tag_colors()
        self.apply_display_settings()

    def apply_dark_mode_recursive(self, widget):
        widget_type = widget.winfo_class()
        try:
            if widget_type in ('Frame', 'Labelframe'):
                widget.configure(bg=self.dark_bg)
            elif widget_type == 'Label':
                widget.configure(bg=self.dark_bg, fg=self.dark_fg)
            elif widget_type == 'Button':
                widget.configure(bg='#404040', fg=self.dark_fg, 
                               activebackground='#505050', activeforeground=self.dark_fg,
                               highlightbackground=self.dark_bg)
            elif widget_type == 'Entry':
                widget.configure(bg='#404040', fg=self.dark_fg, 
                               insertbackground=self.dark_fg, 
                               selectbackground=self.selection_bg,
                               selectforeground=self.selection_fg,
                               highlightbackground=self.dark_bg,
                               highlightcolor='#505050')
            elif widget_type == 'Checkbutton':
                widget.configure(bg=self.dark_bg, fg=self.dark_fg, 
                               activebackground=self.dark_bg, activeforeground=self.dark_fg,
                               selectcolor='#404040',
                               highlightbackground=self.dark_bg)
        except tk.TclError:
            pass
        
        for child in widget.winfo_children():
            self.apply_dark_mode_recursive(child)

    def apply_light_mode(self):
        self.configure(bg=self.light_bg)
        
        for widget in self.winfo_children():
            self.apply_light_mode_recursive(widget)
        
        self.style.theme_use('default')
        self.style.configure('Treeview',
                           background='white',
                           foreground='black',
                           fieldbackground='white')
        self.style.configure('Treeview.Heading',
                           background='#e0e0e0',
                           foreground='black',
                           relief='raised',
                           borderwidth=1)
        self.style.map('Treeview',
                      background=[('selected', self.selection_bg)],
                      foreground=[('selected', self.selection_fg)])
        self.style.map('Treeview.Heading',
                      background=[('active', '#d0d0d0')])
        
        self.update_tag_colors()
        self.apply_display_settings()

    def apply_light_mode_recursive(self, widget):
        widget_type = widget.winfo_class()
        try:
            if widget_type in ('Frame', 'Labelframe'):
                widget.configure(bg=self.light_bg)
            elif widget_type == 'Label':
                widget.configure(bg=self.light_bg, fg='black')
            elif widget_type == 'Button':
                widget.configure(bg='#e0e0e0', fg='black',
                               activebackground='#d0d0d0', activeforeground='black',
                               highlightbackground=self.light_bg)
            elif widget_type == 'Entry':
                widget.configure(bg='white', fg='black',
                               insertbackground='black',
                               selectbackground=self.selection_bg,
                               selectforeground=self.selection_fg,
                               highlightbackground=self.light_bg,
                               highlightcolor='#0078d7')
            elif widget_type == 'Checkbutton':
                widget.configure(bg=self.light_bg, fg='black',
                               activebackground=self.light_bg, activeforeground='black',
                               selectcolor='white',
                               highlightbackground=self.light_bg)
        except tk.TclError:
            pass
        
        for child in widget.winfo_children():
            self.apply_light_mode_recursive(child)

if __name__ == '__main__':
    app = DuplicateManager()
    app.mainloop()