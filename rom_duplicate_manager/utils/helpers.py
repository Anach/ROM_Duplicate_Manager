"""Helper utilities for ROM Duplicate Manager."""

import os
import re
import math
import hashlib
from typing import Set, Tuple, Optional, Dict, List, Callable, Any


def normalize_filename(filename: str, system_extensions: Optional[Set[str]] = None,
                       ignore_system_prefix: bool = False) -> str:
    """Normalize filename by removing copy indicators and version suffixes.

    Removes patterns like " - Copy", " - Copy (n)", and trailing parentheses/brackets
    to create a base name for comparison. Can also strip 3-4 digit catalog
    prefixes from ROM filenames when wildcard scanning is enabled to align
    numbered system files with unnumbered archives.

    Args:
        filename: The filename to normalize
        system_extensions: Set of ROM/system extensions to check for catalog prefixes
        ignore_system_prefix: Whether to strip leading 3-4 digit prefixes for ROMs

    Returns:
        Normalized filename without extension
    """
    name, ext = os.path.splitext(filename)
    if ignore_system_prefix and system_extensions and ext.lower() in system_extensions:
        name = re.sub(r'^\d{3,4}\s+', '', name)

    while True:
        old_name = name
        name = re.sub(r'\s*-\s*Copy(?:\s*\(\d+\))?$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*[\(\[].*?[\)\]]$', '', name)
        name = name.strip()
        if name == old_name:
            break
    return name


def extract_version(filename: str) -> Tuple[int, ...]:
    """Extract version information from filename for comparison.

    Identifies and extracts version numbers, dates, and other version indicators
    to enable intelligent version comparison for duplicate detection.

    Supports formats:
    - Dates: YYYY-MM-DD, YYYY.MM.DD, YYYY_MM_DD, YYYYMMDD
    - Version numbers: v1.0, version 2.1, etc.
    - Proto/Beta indicators: (proto 1), (beta 2)
    - Numeric suffixes in parentheses or at end

    Args:
        filename: The filename to analyze

    Returns:
        Tuple of version components for comparison (higher values = newer)
    """
    filename_lower = filename.lower()
    name_no_ext, _ = os.path.splitext(filename)

    # Extract dates in various formats
    date_val = (0, 0, 0)
    date_match = re.search(r'(20\d{2}|19\d{2})[.\-_](\d{1,2})[.\-_](\d{1,2})', name_no_ext)
    if date_match:
        try:
            date_val = tuple(map(int, date_match.groups()))
        except ValueError:
            pass
    else:
        date_match = re.search(r'(?<!\d)(20\d{2}|19\d{2})(\d{2})(\d{2})(?!\d)', name_no_ext)
        if date_match:
            try:
                date_val = tuple(map(int, date_match.groups()))
            except ValueError:
                pass

    # Extract explicit version numbers
    v_val = (0,)
    v_matches = re.findall(r'v(?:er(?:sion)?)?[\s\-_]?(\d+(?:\.\d+)*)', name_no_ext, re.IGNORECASE)
    if v_matches:
        try:
            v_val = tuple(map(int, v_matches[-1].split('.')))
        except ValueError:
            pass
    # Extract proto/beta version indicators
    proto_val = (0,)
    proto_match = re.search(r'\((?:proto|beta)\s*(\d+)\)', filename_lower)
    if proto_match:
        try:
            proto_val = (int(proto_match.group(1)),)
        except ValueError:
            pass

    # Extract other numeric indicators
    other_val = (0,)
    p_match = re.search(r'\((\d+)\)', name_no_ext)
    if p_match:
        try:
            other_val = (int(p_match.group(1)),)
        except ValueError:
            pass
    else:
        t_match = re.search(r'[_\s\-](\d+(?:\.\d+)*)$', name_no_ext)
        if t_match:
            try:
                other_val = tuple(map(int, t_match.group(1).split('.')))
            except ValueError:
                pass

    return date_val + v_val + proto_val + other_val


def extract_languages(filename: str) -> Set[str]:
    """Extract language codes and video formats from filename.

    Analyzes filename patterns to identify language preferences and video formats
    for ROM files, supporting various naming conventions commonly used in ROM sets.

    Args:
        filename: The filename to analyze

    Returns:
        Set of detected language/region identifiers, or {'Unknown'} if none found
    """
    languages = set()

    # Language and region mappings
    lang_map = {
        'en': 'English', 'english': 'English',
        'ja': 'Japanese', 'japan': 'Japanese',
        'fr': 'French', 'france': 'French',
        'de': 'German', 'germany': 'German',
        'es': 'Spanish', 'spain': 'Spanish',
        'it': 'Italian', 'italy': 'Italian',
        'nl': 'Dutch', 'netherlands': 'Dutch',
        'pt': 'Portuguese', 'portugal': 'Portuguese',
        'sv': 'Swedish', 'sweden': 'Swedish',
        'zh': 'Chinese', 'taiwan': 'Chinese', 'china': 'Chinese',
        'ko': 'Korean', 'korea': 'Korean'
    }

    region_map = {
        'usa': 'English-US', 'europe': 'English-EU', 'australia': 'English-EU',
        'uk': 'English-EU', 'world': 'World', 'global': 'World'
    }

    format_map = {'ntsc': 'NTSC', 'pal': 'PAL', 'secam': 'SECAM'}

    filename_lower = filename.lower()

    # Extract language information from parentheses
    paren_matches = re.findall(r'\(([^)]+)\)', filename)
    for match in paren_matches:
        parts = re.split(r'[,\s]+', match.lower())
        for part in parts:
            part = part.strip()
            if part in lang_map:
                languages.add(lang_map[part])
            elif part in region_map:
                languages.add(region_map[part])
            elif part in format_map:
                languages.add(format_map[part])

    return languages if languages else {'Unknown'}


def get_partial_hash(filepath: str) -> Optional[str]:
    """Generate a fast partial hash for file content comparison.

    Uses a three-point sampling strategy for optimal balance between speed
    and accuracy:
    - First 128KB (header/metadata)
    - Middle 128KB (content sample)
    - Last 128KB (footer/trailer)

    This catches differences in file structure while keeping hash time minimal
    even for multi-GB files.

    Args:
        filepath: Path to the file to hash

    Returns:
        Hex digest of partial hash, "empty" for zero-byte files, or None on error
    """
    try:
        size = os.path.getsize(filepath)
        if size == 0:
            return "empty"

        chunk_size = 131072  # 128KB chunks for better sampling
        hasher = hashlib.md5()

        with open(filepath, "rb") as f:
            # Read first chunk
            hasher.update(f.read(chunk_size))

            # For larger files, add middle and end chunks
            if size > chunk_size * 2:
                try:
                    # Read middle chunk
                    f.seek(size // 2 - chunk_size // 2)
                    hasher.update(f.read(chunk_size))

                    # Read end chunk
                    f.seek(-chunk_size, os.SEEK_END)
                    hasher.update(f.read(chunk_size))
                except OSError:
                    pass  # Handle files that can't seek

        return hasher.hexdigest()
    except Exception:
        return None


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string (e.g. "1.5 MB", "234 KB")
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"