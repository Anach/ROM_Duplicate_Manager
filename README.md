# ROM Duplicate Manager

**ROM Duplicate Manager** is a Python GUI tool for managing duplicate ROM files in a selected folder. The program scans a directory, groups ROM files by their normalized base names (ignoring versions, alternate region info, etc.), and helps users find, select, and delete duplicates with helpful filtering and base file suggestion features.

## Features

- **Scan folder for duplicate ROMs** (based on normalized filenames)
- **Suggest base version**: Automatically highlights the most likely main file among duplicates (usually the lowest version number or shortest filename).
- **Filter and highlight** ROM files by any substring.
- **Batch delete selected files** safely to the recycle bin/trash.
- **Display unique/non-duplicate files separately.**
- **Configurable appearance:**
  - Dark/light mode toggle
  - Alternating row colors
  - Show/hide grid lines
- **Remembers display/user settings** in a config file
- **Uses the tkinter GUI library**; safe and fast for local use

## Usage

1. Run `rom_duplicate_manager.py` (Python 3 required; install dependencies with `pip install send2trash`)
2. Browse to the ROM folder and click **Scan**.
3. Review duplicate file groups:
   - Use _Suggest-base_ to highlight the most likely main ROM file.
   - Use _Select other_ to select all files except the base for quick batch operations.
4. Use filter and auto-highlight/select for fast searching.
5. Select and **Delete Selected** to safely move unwanted files to your system's recycle bin.
6. Change appearance and settings with display checkboxes.

## Why Use This?

- Quickly remove unnecessary ROM file duplicates, keeping only preferred versions.
- Maintain a clean ROM library for emulators or archiving.
- Avoid manual file sorting and accidental deletion—safe delete via Trash!
- Works with any file types: not limited to "ROMs."

## Screenshots

<img width="1002" height="632" alt="image" src="https://github.com/user-attachments/assets/1a2b7e11-dfca-4279-a362-4c00b6af9922" />


## Requirements

- **Python 3.x**
- **tkinter** (usually included with Python)
- **send2trash** (`pip install send2trash`)

## License

MIT License

---

_This tool was designed for local file management and does not interact with the Internet or alter system settings outside the selected folder._
