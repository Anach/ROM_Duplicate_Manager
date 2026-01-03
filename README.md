# ROM Duplicate Manager

A cross-platform GUI tool for duplicate ROM, archive, and image file management. Detect and clean duplicates by filename *or* true file content, delete safely or permanently, and manage orphaned images, all with an intuitive interface and comprehensive tooltips.

<img width="1102" height="632" alt="image" src="https://github.com/user-attachments/assets/1bb25c6c-2e37-4051-9259-fa0eb610520a" />

---

## Features

- **Find duplicates by name or by content**
  - Filename mode: groups potential duplicates by normalized name (ignores region, version, "Copy", etc.).
  - Match Size mode: groups true duplicates by file size and partial content hash, catching duplicates regardless of filename.
- **Smart Select system**
  - Picks a keep file based on language/region/version; easy to override manually.
- **Scan Images toggle**
  - When off, wildcard scans skip image extensions; when on, images are included and orphan cleanup runs against `/images/`.
- **Orphaned image cleanup**
  - Deletes images in `/images/` not paired with a ROM/archive (covers/scrapes).
- **Wildcard-friendly ROM handling**
  - Strips 3-4 digit catalogue prefixes on ROM/system filenames during wildcard scans to better align names.
- **Permanent Delete option**
  - Bypass the Recycle Bin/Trash and delete instantly, with confirmations for safety.
- **Keyboard shortcuts and tooltips**
  - Ctrl+F focus filter, Ctrl+R rescan, Space toggle keep/delete, Delete mark to remove; hover anywhere for context.
- **Batch operations with progress indicators**
  - Progress dialogs for scans/deletes with current file display; status bar shows how many items are marked and their total size.
- **Themes and persistence**
  - Row color alternation, dark/light mode, and all preferences (file type, Match Size, Permanent Delete, Scan Images, etc.) saved and restored.

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
