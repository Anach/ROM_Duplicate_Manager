# ROM Duplicate Manager

A cross-platform GUI tool for duplicate ROM, archive, and image file management with modern themes and intelligent sorting. Detect and clean duplicates by filename *or* true file content, delete safely or permanently, manage orphaned images, and customize your experience with multiple light and dark themes - all with an intuitive interface and comprehensive tooltips.

<img width="1282" height="752" alt="image" src="https://github.com/user-attachments/assets/7dab7358-41ff-467d-969c-2f63f408f96e" />

---

## Features

### Core Functionality
- **Find duplicates by name or by content**
  - Filename mode: groups potential duplicates by normalized name (ignores region, version, "Copy", etc.)
  - Match Size mode: groups true duplicates by file size and partial content hash, catching duplicates regardless of filename

- **Smart Select system**
  - Intelligently picks a keep file based on language/region/version preferences
  - Easy to override manually with visual feedback (green = keep, red strikethrough = delete)
  - Marked items always stay at top of each group for easy review

### Advanced Features
- **Intelligent sorting**
  - Duplicate groups (multiple files) always shown first
  - Unique groups (single file) shown below
  - Sort by filename or full path, ascending or descending
  - Marked items remain at top within each group regardless of sort

- **Scan Images toggle**
  - When off: wildcard scans skip image extensions
  - When on: images are included and orphan cleanup runs against `/images/` folder

- **Orphaned image cleanup**
  - Automatically detects and removes images in `/images/` not paired with a ROM/archive
  - Keeps only covers/screenshots for files you're keeping

- **Wildcard-friendly ROM handling**
  - Strips 3-4 digit catalogue prefixes on ROM/system filenames during wildcard scans
  - Better alignment between numbered and unnumbered file versions

- **Permanent Delete option**
  - Bypass the Recycle Bin/Trash for instant deletion
  - Confirmation dialogs for safety
  - Saved preference persists across sessions

### User Interface
- **Modern theme system**
  - 10 light themes: cosmo, flatly, journal, litera, lumen, minty, pulse, sandstone, united, yeti
  - 5 dark themes: cyborg, darkly, solar, superhero, vapor
  - Toggle row color alternation
  - Theme choice is saved between sessions

- **Adjustable list font size**
  - View > Font Size menu with Small (8), Medium (10), Large (12)
  - Tree rows auto-resize with the chosen font and the preference is saved

- **Saved preferences**
  - Remembers language, Smart Select, Match Size, Permanent Delete, Scan Images, regex/path filter, include sub-folders, theme, font size, row colors
  - File-Type and Category always start at Archives and All on launch

- **Keyboard shortcuts**
  - `Ctrl+O`: Browse for folder
  - `Ctrl+R`: Rescan
  - `Ctrl+F`: Focus filter
  - `Space`: Toggle keep/delete on selected items
  - `Delete`: Mark selected items for deletion

- **Enhanced status display**
  - Responsive grid shows only active stats (unique, duplicate groups/files, orphaned images, filtered count, marked size)
  - "Marked for deletion" row hidden when nothing is marked

- **Batch operations with progress**
  - Progress dialogs for scans/deletes with current file display
  - Visual feedback during long operations

- **Comprehensive tooltips**
  - Hover over any control for context-specific help

### Technical Features
- **Modular architecture**
  - Clean separation of UI, core logic, and configuration
  - Mixin pattern for maintainability
  - Comprehensive docstrings and type hints

- **Auto-update checker**
  - Checks GitHub for newer versions
  - Platform-specific download links
  - Optional pre-release support

## Usage

1. Run with Python:
   ```
   pip install -r requirements.txt
   python run.py
   ```
   or:
   ```
   python -m rom_duplicate_manager
   ```
   Or download a self-contained archive/executable for **Windows**, **macOS**, or **Linux** from [Releases](https://github.com/Anach/ROM_Duplicate_Manager/releases/latest).
2. Browse/select your ROM folder.
3. (Optional) Adjust Sub-Folders (saved), File-Type (defaults to Archives), Category (defaults to All), language, Match Size, Permanent Delete, Scan Images, regex/path filter options, Smart Select, and View > Font Size.
4. Click **Scan**. Inspect/override Smart Select marks if needed.
5. Click **Delete Selected** to delete (Recycle Bin/Trash or permanent - your choice).
6. Use keyboard shortcuts for faster review, and hover for instant help.

Note: File-Type and Category reset to Archives/All on each launch; other preferences (including Sub-Folders and font size) are saved to `rom_duplicate_manager.ini`.

## Requirements

- Python 3.x
- `tkinter` (standard)
- `send2trash` (install with `pip install send2trash`)

## File Structure

- `run.py` - Simple launcher (`python run.py` or `python -m rom_duplicate_manager`)
- `rom_duplicate_manager/` - Application package:
  - `main.py` - Main window and orchestration
  - `ui/` - UI components (menu bar, themes, dialogs, file list)
  - `core/` - Scanning, duplicate detection, file operations
  - `config/` - Settings load/save and defaults
  - `utils/` - Helpers, icons, updater
- `requirements.txt` - Python dependencies
- `rom_duplicate_manager.ini` - User config/prefs (theme, font size, filters; auto-generated)
- `rom_duplicate_manager.spec` - PyInstaller Windows build script
- `.gitignore`, `LICENSE`, etc.

## Platform Support

- Windows, macOS, Linux (self-contained archives from Releases or run via Python)

## License

MIT License

---

**For managing your own collections only. Use responsibly.**
