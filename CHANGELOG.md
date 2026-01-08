# Changelog

All notable updates to this project are documented here.

## [v1.4.4] - 2026-01-08

### Fixed
- Scan Images now always checks orphaned images against all scanned files, independent of File-Type and Category filters.
- Delete Selected now deletes all marked items (plus any additional selections) instead of only one item in single-file groups.
- Marked items retain their strikethrough styling even when a manual filter highlight is active.

## [v1.4.3] - 2026-01-06

### Added
- **Font Size Adjustment**:
  - Added a new "Font Size" submenu to the View menu with Small (8), Medium (10), and Large (12) options.
  - Adjustment specifically targets the main scan results (Treeview) for better readability while keeping the rest of the UI at default size.
  - Font size preference is saved to the INI configuration.
- **Unified Theme Fonts**: Standardized font sizes across all themes (fixing an issue where the 'Darkly' theme used a different default size).
- **Enhanced Category Filtering**: Added a new category selection combobox to filter results by Games, Demos, Betas, Utilities, and more.
- **Cross-platform releases**: GitHub Actions (YML) now builds self-contained archives for Windows, macOS, and Linux; Python entrypoints remain available for manual runs.

### Changed
- **Improved Stats Display**:
  - Refined the stats block with better vertical padding and sub-heading spacing for improved readability.
  - Optimized toolbar layout to ensure stats remain fully visible at the default window size.
- **Enhanced Sorting**: Manual filter items now sort to the top of their groups, making bulk marking much more efficient.
- **Configuration Persistence**:
  - "Sub-Folders" setting now saves to the INI file.
  - "File Type" and "Category" filters now correctly revert to defaults on startup.
  - Replaced legacy dark-mode logic with a unified theme-based configuration.

### Fixed
- Fixed alignment and spacing issues in the stats sub-headings.
- Resolved a potential crash when applying fonts to the Treeview widget.

## [v1.4.2] - 2026-01-04

### Added
- **Enhanced Update Check System**:
  - Converted "Check for Updates" into a sub-menu with automated check options.
  - Added automated check frequencies: Daily, Weekly, Monthly, and Never.
  - Automated checks run silently on startup and only notify the user if an update is found.
  - Manual "Check Now" option remains interactive for immediate feedback.
  - Last update check timestamp and frequency preference are now saved to the INI file.
- **Enhanced status display**:
  - Split status into a dynamic grid with up to six statistics: Unique Files, Duplicate Groups, Duplicate Files, Orphaned Images, Filtered Items, and Marked for Deletion.
  - **Smart Visibility**: Statistics only appear when they have a value greater than zero, keeping the UI clean and focused.
  - **Auto-Expanding Layout**: Automatically switches between 1-column and 2-column layouts to minimize vertical space usage.
  - **Themed Numerical Values**: Improved visual hierarchy with color-coded values (success/info/warning/danger).
  - **Perfect Alignment**: Used a grid layout for consistent vertical alignment of all numerical values.
  - Clean, non-bold font consistent with the rest of the UI.
- **UI Uniformity and Alignment**:
  - Standardized heights for all buttons, entry boxes, and combo boxes across the toolbar.
  - Aligned the bottom rows of all toolbar blocks for a perfectly balanced, professional appearance.

### Fixed
- **Menu Alignment and Layout**:
  - Fixed a UI glitch where menu labels would shift to the right when a checkmark was displayed.
  - Implemented fixed-width checkmark labels for consistent alignment across all menus and sub-menus (including Themes).

## [v1.4.1] - 2026-01-03


### Added
- Asynchronous file scanning: UI remains responsive during large scans, with progress updates and cancellation support.
- **Enhanced status display**:
  - Split status into two rows with better visual hierarchy.
  - Status container now at top of window for better visibility.

### Changed
- Refactored main application to use a package structure; removed legacy monolithic files and added a new launcher (`run.py`), supporting `python -m rom_duplicate_manager`.
- Improved "All Files" filter: now ignores images unless "Scan Images" is selected; clarified tooltip for "Scan Images".
- Added comprehensive type hints to event handlers and UI components for better code clarity and editor support.
- **Improved UI layout and workflow**:
  - Reorganized button layout for more intuitive flow
- **Enhanced sorting behavior**:
  - Duplicate groups (multiple files) now always appear at top of list
  - Unique groups (single file) appear below duplicates
  - Both sections maintain selected sort order (filename/path, ascending/descending)
  - Sort resets to filename ascending on each new scan
  - Marked items (keep/delete) stay at top within each group

### Fixed
- Restored correct dual behavior for "Scan Images" (image inclusion and orphan cleanup).
- Minor bugfixes and improved error handling in scanning and UI.
- Sort state properly tracked for user-initiated vs programmatic sorts
- Fixed method signature inconsistencies in file list module

## [v1.4.0] - 2026-01-03

### Added
- **Custom menu bar system**:
  - Full theme integration with dark/light mode support
  - Windows-style hover-to-open menu behavior
  - Submenu support for theme selection
  - Consistent styling across all themes
- **Theme system overhaul**:
  - Integrated ttkbootstrap for modern, professional appearance
  - Multiple light themes: cosmo, flatly, journal, litera, lumen, minty, pulse, sandstone, united, yeti
  - Multiple dark themes: cyborg, darkly, solar, superhero, vapor
  - Theme selection saved to configuration
  - Proper color coordination across all UI elements
- **Update checker**:
  - Automatic version checking against GitHub releases
  - Platform-specific download links (Windows, macOS, Linux)
  - Pre-release support option
  - Direct browser launch for downloads

### Changed
- **Modular codebase structure** - Split monolithic file into organized modules:
  - `rom_duplicate_manager/config/` - Settings and defaults management
  - `rom_duplicate_manager/utils/` - Helper utilities, icons, and updater
  - `rom_duplicate_manager/core/` - Scanning, duplicate detection, and file operations
  - `rom_duplicate_manager/ui/` - All UI components (dialogs, file list, menu bar, themes)
- **Improved code organization**:
  - Mixin pattern for clean separation of concerns
  - Comprehensive docstrings for all functions and classes
  - Type hints throughout codebase
  - Reduced main file to ~690 lines (60% reduction from v1.3.5)
- **Enhanced UI layout**:
  - Status display moved to top of window in dedicated frame
  - Buttons reorganized into modern toolbar layout
  - Better visual grouping of related controls
  - Improved tooltips for all UI elements
- **Automated build system** - GitHub Actions workflow for cross-platform releases:
  - Windows: `ROM.Duplicate.Manager.v.X.X.X.zip` with .exe
  - Linux: `ROM.Duplicate.Manager.v.X.X.X.linux.tar.gz` with .AppImage
  - macOS: `ROM.Duplicate.Manager.v.X.X.X.macos.tar.gz` with .app
  - Automatic documentation bundling (README, CHANGELOG, LICENSE)
  - SHA256 checksums for verification

### Fixed
- Sorting now correctly maintains keep/delete items at top of each group
- Improved error handling and user feedback throughout application

## [v1.3.5] - 2026-01-03

### Added
- Pac-Man application icon plus refreshed tooltips and keyboard shortcuts (Ctrl+F to focus the filter, Ctrl+R to rescan, Space to toggle keep/delete, Delete to mark for removal).
- Status bar now reports how many items are marked for removal and their total size before you delete.

### Changed
- "Scan Images" now doubles as an image filter: when unchecked, wildcard scans skip image extensions; when checked, images are scanned and orphan cleanup runs.
- Wildcard scans strip 3-4 digit catalogue prefixes from ROM/system filenames to better align with archive names and reduce false mismatches.
- Button layout and selection handling tuned for smoother keyboard use with the new shortcuts.

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
