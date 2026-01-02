# Changelog

All notable updates to this project are documented here.

## [v1.3.0] - 2026-01-02

### Added
- **Content-based duplicate detection (“Match Size” mode):**
  - Optionally find duplicates based on file size and partial hash, not just filename.
  - Useful for catching true duplicate files even if their filenames differ.
  - Group labels show approximate file size and short hash.
- **Permanent Delete:**
  - Adds a setting to skip the Recycle Bin/Trash and irreversibly delete files.
  - This setting is saved in the `.ini` config.
  - Confirmation dialogs for safety.
- **Config file enhancements:**
  - Configuration for new options like “Match Size” and “Permanent Delete” now saved and restored automatically.
- **Progress Popups for Long Operations:**
  - Scanning and deletion show progress indicators with file info, improving feedback on large sets.
- **Improved filename normalization:**  
  - Cleans names by also stripping “ - Copy”, “ - Copy (n)”, and trailing parentheses or brackets, drastically reducing false duplicate matches.
- **Expanded tooltips for all new controls.**
- **Dark/light mode and multi-row color works for new features and popups.**

### Improved/Fixes
- Robust exception handling for file permission and filesystem edge cases in new modes.
- Status bar and all dialogs communicate advanced modes and file actions (e.g., permanent delete).

---

## [v1.2.0] - 2026-01-01

- Tooltips for all controls.
- Orphaned images: delete images in `/images` not tied to an existing ROM/archive.

## [v1.1.0] - 2026-01-01

- Subfolder, language, filetype filters.
- Progress bar, smart select display, preference saving.

## [v1.0.0] - 2026-01-01

- Initial release.

---

⚠️ _This changelog is based on recent commit logs and the latest `rom_duplicate_manager.py`. [See full commit history on GitHub.](https://github.com/Anach/ROM_Duplicate_Manager/commits/main)_
