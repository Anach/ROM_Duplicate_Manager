# ROM Duplicate Manager

A cross-platform GUI tool for duplicate ROM, archive, and image file management with modern themes and intelligent sorting. Detect and clean duplicates by filename *or* true file content, delete safely or permanently, manage orphaned images, and customize your experience with multiple light and dark themes—all with an intuitive interface and comprehensive tooltips.

<img width="1102" height="632" alt="image" src="https://github.com/user-attachments/assets/1bb25c6c-2e37-4051-9259-fa0eb610520a" />

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
  - All settings saved and restored

- **Keyboard shortcuts**
  - `Ctrl+O`: Browse for folder
  - `Ctrl+R`: Rescan
  - `Ctrl+F`: Focus filter
  - `Space`: Toggle keep/delete on selected items
  - `Delete`: Mark selected items for deletion

- **Enhanced status display**
  - Two-row layout with automatic text wrapping
  - Shows marked file count and total size
  - "Marked for deletion" row hidden when nothing marked

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
   python rom_duplicate_manager.py
   ```
   Or download a [Windows executable from Releases](https://github.com/Anach/ROM_Duplicate_Manager/releases/latest).
2. Browse/select your ROM folder.
3. (Optional) Adjust subfolder, file type, language, Match Size, Permanent Delete, Scan Images, regex/path filter options, and Smart Select preferences.
4. Click **Scan**. Inspect/override Smart Select marks if needed.
5. Click **Delete Selected** to delete (Recycle Bin/Trash or permanent — your choice).
6. Use keyboard shortcuts for faster review, and hover for instant help.

## Requirements

- Python 3.x
- `tkinter` (standard)
- `send2trash` (install with `pip install send2trash`)

## File Structure

- `rom_duplicate_manager.py` — Main code
- `requirements.txt` — Python dependencies
- `rom_duplicate_manager.ini` — User config/prefs (auto-generated)
- `rom_duplicate_manager.spec` — PyInstaller Windows build script
- `.gitignore`, `LICENSE`, etc.

## Platform Support

- Windows, macOS, Linux (via Python, or Windows executable)

## License

MIT License

---

**For managing your own collections only. Use responsibly.**
