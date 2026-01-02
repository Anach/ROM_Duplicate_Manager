# ROM Duplicate Manager

A cross-platform GUI tool for duplicate ROM, archive, and image file management. Detect and clean duplicates by filename *or* true file content, delete safely or permanently, and manage orphaned images—all with intuitive interface and comprehensive tooltips.

---

## Features

- **Find duplicates by name or by content!**
  - **Filename mode (default):** Groups potential duplicates by normalized name (ignoring region, version, “Copy”, etc.).
  - **Match Size mode (NEW!):** Groups true duplicates by file size and partial content hash, catching duplicates regardless of filename.
- **Smart Select System:**  
  - Marks which file to keep (based on language/region/version), others for removal—easy to override.
- **Permanent Delete Option (NEW!):**
  - Choose to bypass the Recycle Bin/Trash and delete files instantly, with confirmation for safety.
- **Delete Orphaned Images:**
  - Finds and deletes files in the `/images/` folder not paired with any ROM/archive (e.g., unneeded covers/scrapes).
- **Subfolder, language, and filetype filters**
- **Batch Operations with Progress Indicators:**  
  - Progress dialogs during long scans and deletes, with current file display.
- **Row color alternation & full dark/light mode**
- **User configuration saved/restored** (including Match Size, Permanent Delete, etc.)
- **Rich tooltip help for all controls**

## Usage

1. Run with Python:
   ```
   pip install -r requirements.txt
   python rom_duplicate_manager.py
   ```
   Or download a [Windows executable from Releases](https://github.com/Anach/ROM_Duplicate_Manager/releases/latest).
2. Browse/select your ROM folder.
3. (Optional) Adjust subfolder, filetype, language, “Match Size”, “Permanent Delete”, and “Scan Images” options.
4. Click “Scan”. Inspect/override Smart Select marks if needed.
5. Click “Delete Selected” to delete (safely or permanently—your choice).
6. Hover over any button or setting for instant help.

## Requirements

- Python 3.x
- `tkinter` (standard)
- `send2trash` (install with `pip install send2trash`)

## File Structure

- `rom_duplicate_manager.py` — Main code.
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
