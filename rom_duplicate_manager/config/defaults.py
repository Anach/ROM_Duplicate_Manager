"""Default configuration and constants for ROM Duplicate Manager."""

from typing import Dict, Set

# Keywords for specific ROM categories
UTILITY_KEYWORDS: Set[str] = {
    'camera', 'program', 'action replay', 'game genie', 'game shark', 'bible',
    'diagnostic', 'diagnosis', 'cartridge', 'magazine', 'multicart, cassette', "tester",
}

PROTO_KEYWORDS: Set[str] = {'proto', 'prototype', 'beta'}

DEMO_KEYWORDS: Set[str] = {'demo', 'sample', 'kiosk'}

AFTERMARKET_KEYWORDS: Set[str] = {'aftermarket', 'homebrew', 'hb', 'hack', 'unlicensed', 'unl', 'port'}

# Combined set of all non-standard game keywords for exclusion and deprioritization
NON_GAME_KEYWORDS: Set[str] = UTILITY_KEYWORDS | PROTO_KEYWORDS | DEMO_KEYWORDS | AFTERMARKET_KEYWORDS

# Default file type extensions
DEFAULT_FILE_TYPES: Dict[str, Set[str]] = {
    "Archives": {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.lzma', '.jar', '.lha', '.lzh'},
    "Disk-Img": {'.iso', '.bin', '.cue', '.img', '.mdf', '.mds', '.nrg', '.ccd', '.chd', '.gdi', '.cdi'},
    "System": {
        '.adf', '.hdf', '.cpc', '.dsk', '.cpr', '.do', '.po', '.apple2', '.a26', '.a52', '.a78', '.lnx',
        '.st', '.xfd', '.atr', '.atx', '.com', '.xex', '.cas', '.sap', '.d64', '.d71', '.d81', '.g64',
        '.prg', '.t64', '.tap', '.crt', '.gb', '.gbc', '.gba', '.md', '.smd', '.gen', '.60', '.sms',
        '.nes', '.fds', '.smc', '.sfc', '.fig', '.swc', '.n64', '.v64', '.z64', '.pbp', '.cso', '.neo',
        '.pce', '.sgx', '.ws', '.wsc', '.col', '.int', '.vec', '.min', '.sv', '.gg', '.ngp', '.ngc',
        '.vb', '.32x', '.p8', '.png', '.solarus', '.tic', '.love', '.scummvm', '.ldb', '.nx', '.v32'
    },
    "Images": {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp', '.svg', '.ico'},
    "Videos": {'.mp4', '.mpg', '.mpeg', '.avi', '.mov', '.wmv', '.mkv'},
    "All Files": set()  # Empty set means no filtering
}

# Category definitions for filtering
ROM_CATEGORIES: Dict[str, Set[str]] = {
    "All": set(),
    "Games": set(),  # Special case: excludes NON_GAME_KEYWORDS
    "Demos": DEMO_KEYWORDS,
    "Betas": PROTO_KEYWORDS,
    "Utilities": UTILITY_KEYWORDS,
    "Other": AFTERMARKET_KEYWORDS
}

# Tooltips for categories
CATEGORY_TOOLTIPS: Dict[str, str] = {
    "All": "Show all files matching the selected File Type.",
    "Games": "Show only standard games (excludes utilities, betas, etc.).",
    "Utilities": "Show non-game files like Action Replay, and diagnostic tools",
    "Betas": "Show only prototype and beta versions.",
    "Demos": "Show only demos, samples, and kiosk versions.",
    "Other": "Show homebrew, aftermarket, hacks, ports, and unlicensed releases."
}

# Default language priorities
DEFAULT_LANGUAGE_PRIORITIES: Dict[str, int] = {
    'English': 1, 'English-US': 2, 'English-EU': 3, 'World': 4,
    'Japanese': 5, 'French': 6, 'German': 7, 'Spanish': 8,
    'Italian': 9, 'Unknown': 10
}

# Default preferred languages (can be overridden by user)
DEFAULT_PREFERRED_LANGUAGES: Set[str] = {'English', 'English-US', 'World'}
