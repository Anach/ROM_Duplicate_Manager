# ROM Duplicate Manager (Built for managing my R36S)

A feature-rich, cross-platform tool for intelligently finding, sorting, and safely deleting duplicate ROM and archive files in your collections. Also detects and removes orphaned cover/screenshot images in a dedicated images subfolder. Built for personal ROM library hygiene—**no files are destroyed, all deletions go to your system Recycle Bin/Trash**.

<img width="1102" height="632" alt="image" src="https://github.com/user-attachments/assets/3da82d2b-e0bd-41ea-8288-1142a21b6cd8" />

---

## Features

- **Recursive Duplicate Scan**: Find duplicate ROM/archive files by normalized base name (ignoring version, region, etc.) in a folder and all subfolders.
- **Smart Select System**:
  - Intelligently aggregates similar files into groups.
  - “Smart Select” marks best version to keep, and others to remove (with color cues: **Green = Keep, Red/Strike = Delete**).
  - Quickly toggle or override suggestions with a click.
- **Language Preference**: Prioritize which language/region to keep in each group.
- **File-type and Sub-folder Filtering**: Limit search/filter by file-type category or inclusion of subfolders.
- **Manual Filter and Marking**:
  - Search for any name/keyword.
  - Buttons to bulk “Keep” or “Delete” by filter.
  - “Reset” to clear marks.
- **Bulk, Safe Delete**: Delete all files marked for removal in one step (sent to Trash).
- **Orphaned Image Handling (NEW in 1.2.0)**:
  - Detects images in `/images/` folder without matching ROM/archive file (“orphaned”).
  - Optionally moves orphaned images to Trash alongside regular duplicates.
- **Status and Progress Reporting**:
  - Progress bar for batch operations
  - Status line shows duplicate/unique/orphaned counts.
- **Customizable Display**:
  - Alternating row colors, dark/light mode, and more—all preferences saved to `.ini`
  - No distracting grid lines; clear modern appearance
- **Extensive Tooltips (NEW in 1.2.0)**:
  - Mouse-over help for nearly every button/setting, ideal for new users

## Usage

1. **Run the program**  
   - With Python:  
     ```
     pip install -r requirements.txt
     python rom_duplicate_manager.py
     ```
   - Or download a [standalone Windows executable](https://github.com/Anach/ROM_Duplicate_Manager/releases/latest).
2. **Browse** to the folder where your ROMs are kept.
3. **(Optional)**: Enable/disable subfolder scan, file-type filter, language preference, or the new image/orphan scan feature.
4. **Scan** for duplicates and orphaned images. See visual grouping and marking.
5. **Use filters and Smart Select** to mark files for keep or delete.
6. **Press Delete Selected** — files (and optionally orphaned images) go to Trash.
7. **Hover mouse** over buttons and fields for quick help/tooltips.

## Requirements

- Python 3.x (if running from source)
- tkinter (standard with Python)
- send2trash (`pip install send2trash`)

## File Structure

- `rom_duplicate_manager.py` — Main application source
- `requirements.txt` — Python dependency list
- `rom_duplicate_manager.ini` — Config/preferences (auto-generated as needed)
- `rom_duplicate_manager.spec` — PyInstaller config for Windows binary
- `.gitignore`, `LICENSE`, `README.md`, `CHANGELOG.md`

## Platform Support

- Windows, macOS, Linux (Python required except for Windows executable)

## License

MIT License

---

_Use responsibly on your own files and libraries! Please only use with legally obtained software/ROMs._
