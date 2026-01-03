"""File operations module for ROM Duplicate Manager."""

import os
from typing import List
from send2trash import send2trash


def delete_files(file_paths: List[str], permanent: bool = False) -> tuple[int, List[str]]:
    """Delete a list of files either permanently or to recycle bin.

    Args:
        file_paths: List of file paths to delete
        permanent: If True, delete permanently; if False, send to recycle bin

    Returns:
        Tuple of (successful_count, failed_files)
    """
    successful_count = 0
    failed_files = []

    for file_path in file_paths:
        try:
            if permanent:
                os.remove(file_path)
            else:
                send2trash(file_path)
            successful_count += 1
        except Exception as e:
            failed_files.append(f"{file_path}: {str(e)}")

    return successful_count, failed_files


def calculate_total_size(file_paths: List[str]) -> int:
    """Calculate total size of files in bytes.

    Args:
        file_paths: List of file paths

    Returns:
        Total size in bytes
    """
    total_size = 0
    for file_path in file_paths:
        try:
            total_size += os.path.getsize(file_path)
        except (OSError, FileNotFoundError):
            pass  # Skip files we can't access
    return total_size