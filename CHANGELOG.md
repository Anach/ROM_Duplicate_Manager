# Changelog

All notable updates to this project are documented here.

## [v1.2.0] - 2026-01-01
### Added
- **Tooltip system**: Contextual tooltips are now shown for nearly every button and control in the interface, providing inline explanations and user help.
- **Orphaned image detection and deletion**:
  - Automatically detects image files (such as screenshots/covers) in an `images/` subfolder that do not have corresponding ROM/archive files.
  - Optionally deletes these orphaned images alongside regular duplicate file cleanup.
  - Option to enable/disable this with "Scan Images" checkbox.
  - Status bar displays the number of detected orphaned images after scan.
  - Deletion process moves both files and orphaned images to Recycle Bin/Trash.

### Improved
- Tooltip infrastructure: Handles widgets and complex controls, avoids duplication.
- More robust dark/light mode handling for tooltips and all UI rows.

### Changed
- Progress reporting now shows both ROM/archive and orphaned image deletions.

### Fixed
- Improved file extension matching for image types.
- Better naming/logic for image-orphan detection in `images/` folder.
- Smarter row color alternation and theme consistency.

---

## [v1.1.0] - 2026-01-01
### Added
- Sub-folder filter support
- Language selection filter
- File-type/extension filtering
- Progress bar during scanning and batch operations
- Color style for Smart Select (green=keep, red-strike=delete)
- Smart Select, language, dark mode, and row color options now saved to `.ini` file
- Simple left-click to switch/filter mode

### Changed
- Combined all main filtering into intelligent “Smart Select” for ease of use
- Manual filter now overrides Smart Select
- Reorganized Smart Select filter order
- Visual design update: removed grid lines for a cleaner look

### Fixed
- Improved saving/restoration of user display/settings between runs

---

## [v1.0.0] - 2026-01-01
- Initial public release
- Windows standalone executable available
- Basic duplicate scan, suggested file keep/delete, dark/light mode, row color, alternate coloring, and config file support

---

For full details and release assets, see the [Releases page](https://github.com/Anach/ROM_Duplicate_Manager/releases).