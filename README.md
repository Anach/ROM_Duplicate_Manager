# ROM Duplicate Manager

A feature-rich cross-platform tool for intelligently finding, sorting, and safely deleting duplicate ROM (and general archive) files from folders and subfolders.

**No ROMs are harmed!** All deletes send files to your system Recycle Bin/Trash.

---

## Features

- **Recursive Scan**: Scan a folder and all subfolders for duplicate files, grouped by normalized base filename.
- **Smart Select**:
  - Combine version/region/numbering/part info into an intelligent file group.
  - Simple left-click on group? Switch filter mode on the fly!
  - Manual filter override is possible.
- **Filter Options**:
  - Language selection for files (e.g., only show English, Japanese, etc.).
  - File-type/extension filtering.
  - Text-based filtering with substring matching.
- **Sub-folder Filter**: Limit search/filter to specific subdirectories.
- **Keep/Delete Choice**:
  - “Smart Select” suggests which file is the most optimal to keep (e.g., best version/language/region).
  - Color tags: **Green = Keep**, **Red/strike-through = Delete**
  - Easily toggle suggestions and make manual changes.
  - “Select other” quickly marks all but the suggested base file for deletion.
- **Bulk Delete**: Remove all selected files with a single action (files sent to trash for safety).
- **Visuals**:
  - Progress bar for batch operations
  - Customizable row color, smart select style, and dark/light mode (all saved to `.ini` config)
  - Alternate color rows for visual clarity
  - Language, Smart Select, and appearance options remembered between launches (via `.ini`)
- **No grid lines**: Clean, modern look

## Usage

1. **Run**:  
   - With Python:  
     ```bash
     pip install -r requirements.txt
     python rom_duplicate_manager.py
     ```
   - Or use [prebuilt Windows Executable](https://github.com/Anach/ROM_Duplicate_Manager/releases/latest) (`.zip`).
2. **Select Folder** to scan (scans recursively).
3. **Adjust Filters**: Use language, file type, or text filters as needed.
4. **Smart Select**: Let the tool suggest a base file in each group or override manually.
5. **Review and Delete**: Review flagged files (red/strike) and delete selected ones—safe to trash!
6. **Tweak appearance and settings** as desired (changes saved to `.ini`).

## Download

Get the latest release (Windows executable or source) from the [Releases page](https://github.com/Anach/ROM_Duplicate_Manager/releases).

## Requirements

- Python 3.x (if running from source)
- tkinter (comes with Python)
- send2trash (`pip install send2trash`)

## File Structure

- `rom_duplicate_manager.py` - Main application code.
- `requirements.txt` - Python dependencies.
- `rom_duplicate_manager.ini` - User/config settings (auto-generated as needed).
- `rom_duplicate_manager.spec` - PyInstaller config for building standalone executables.
- `.gitignore` - Standard gitignore
- `LICENSE` - License file

## Platform Support

- Works on Windows, macOS, Linux (Python required except for Windows executable)

## License

MIT License

---

**This tool is for personal backup/library management. Please only use it on legally obtained files!**