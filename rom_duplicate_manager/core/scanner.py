"""Core scanning and duplicate detection functionality."""

import os
from typing import Dict, List, Set, Tuple, Optional, Callable

from ..utils.helpers import normalize_filename, get_partial_hash


def scan_folder(folder: str, recursive: bool = False, extension_filter: Optional[Set[str]] = None,
                match_size: bool = False, progress_callback: Optional[Callable] = None,
                system_extensions: Optional[Set[str]] = None, ignore_system_prefix: bool = False,
                exclude_extensions: Optional[Set[str]] = None) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Scan folder for duplicate files using name-based or size-based matching.

    Args:
        folder: Directory path to scan
        recursive: Whether to include subdirectories
        extension_filter: Set of file extensions to include (None = all files)
        exclude_extensions: Set of file extensions to skip when extension_filter is None
        match_size: Use size+hash matching instead of filename normalization
        progress_callback: Optional callback function for progress updates
        system_extensions: Optional set of ROM/system extensions for prefix stripping
        ignore_system_prefix: Ignore 3-4 digit catalog prefixes on system ROMs when True

    Returns:
        Tuple of (duplicates_dict, non_duplicates_dict) where keys are group names
        and values are lists of file paths
    """
    file_list = []
    if recursive:
        # Use os.walk for recursive scanning
        for root, dirs, files in os.walk(folder):
            for f in files:
                _, ext = os.path.splitext(f)
                ext_lower = ext.lower()
                if extension_filter and ext_lower not in extension_filter:
                    continue
                if not extension_filter and exclude_extensions and ext_lower in exclude_extensions:
                    continue
                file_list.append(os.path.join(root, f).replace('\\', '/'))
    else:
        # Use os.scandir for faster non-recursive directory listing
        if os.path.exists(folder):
            try:
                with os.scandir(folder) as entries:
                    for entry in entries:
                        if entry.is_file(follow_symlinks=False):
                            _, ext = os.path.splitext(entry.name)
                            ext_lower = ext.lower()
                            if extension_filter and ext_lower not in extension_filter:
                                continue
                            if not extension_filter and exclude_extensions and ext_lower in exclude_extensions:
                                continue
                            file_list.append(entry.path.replace('\\', '/'))
            except PermissionError:
                pass  # Skip directories we can't access

    groups = {}
    total = len(file_list)
    if total == 0:
        return {}, {}

    if not match_size:
        # Name-based grouping
        for i, full_path in enumerate(file_list):
            if progress_callback:
                progress_callback(i + 1, total, f"Scanning: {os.path.basename(full_path)}")
            base = normalize_filename(os.path.basename(full_path), system_extensions, ignore_system_prefix)
            groups.setdefault(base, []).append(full_path)
    else:
        # Size-based grouping with partial hashing
        size_map = {}
        # Batch size checking with minimal progress updates for speed
        batch_size = max(1, total // 20)  # Update progress every ~5%
        for i, full_path in enumerate(file_list):
            if progress_callback and (i % batch_size == 0 or i == total - 1):
                progress_callback(i + 1, total, f"Checking size: {os.path.basename(full_path)}")
            try:
                size = os.path.getsize(full_path)
                size_map.setdefault(size, []).append(full_path)
            except Exception:
                pass  # Skip files we can't access

        # Hash files that share the same size
        hashed_count = 0
        potential_dupes = [paths for paths in size_map.values() if len(paths) > 1]
        total_to_hash = sum(len(p) for p in potential_dupes)

        for size, paths in size_map.items():
            if len(paths) == 1:
                # Unique size - group by normalized name
                full_path = paths[0]
                base = normalize_filename(os.path.basename(full_path), system_extensions, ignore_system_prefix)
                groups.setdefault(base, []).append(full_path)
            else:
                # Multiple files with same size - group by hash
                for full_path in paths:
                    hashed_count += 1
                    if progress_callback:
                        progress_callback(hashed_count, total_to_hash, f"Hashing: {os.path.basename(full_path)}")
                    h = get_partial_hash(full_path)
                    _, ext = os.path.splitext(full_path)
                    if h:
                        base = f"Size: {size:,} bytes ({ext.lower()}) [Hash: {h[:8]}]"
                    else:
                        base = f"Size: {size:,} bytes ({ext.lower()})"
                    groups.setdefault(base, []).append(full_path)

    # Split into duplicates and unique files
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    non_duplicates = {k: v for k, v in groups.items() if len(v) == 1}

    return duplicates, non_duplicates


def find_orphaned_images(images_folder: str, keep_filenames: Set[str], file_types: Dict[str, Set[str]]) -> List[str]:
    """Find orphaned image files that don't correspond to any ROM files.

    Args:
        images_folder: Path to the images directory
        keep_filenames: Set of base filenames (without extensions) to keep
        file_types: Dictionary mapping file type categories to extension sets

    Returns:
        List of full paths to orphaned image files
    """
    if not os.path.exists(images_folder):
        return []

    image_extensions = file_types.get("Images", set())
    orphaned = []

    try:
        for f in os.listdir(images_folder):
            full_path = os.path.join(images_folder, f)
            if os.path.isfile(full_path):
                name, ext = os.path.splitext(f)
                if image_extensions and ext.lower() in image_extensions:
                    match_name = name.lower()
                    # Handle "-image" suffix convention
                    if match_name.endswith("-image"):
                        match_name = match_name[:-6]
                    if match_name not in keep_filenames:
                        orphaned.append(full_path)
    except OSError:
        pass  # Handle permission errors gracefully

    return orphaned