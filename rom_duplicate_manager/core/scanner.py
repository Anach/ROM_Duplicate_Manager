"""Core scanning and duplicate detection functionality with async support."""

import os
import threading
import queue
from typing import Dict, List, Set, Tuple, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

from ..utils.helpers import normalize_filename, get_partial_hash


class ScanStatus(Enum):
    """Status codes for scan operations."""
    PROGRESS = "progress"
    COMPLETE = "complete"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class ScanResult:
    """Result container for async scan operations."""
    status: ScanStatus
    duplicates: Optional[Dict[str, List[str]]] = None
    non_duplicates: Optional[Dict[str, List[str]]] = None
    progress: int = 0
    total: int = 0
    message: str = ""
    error: Optional[Exception] = None


class AsyncScanner:
    """Asynchronous file scanner that runs in a background thread.

    Provides non-blocking directory scanning with progress updates via a queue.
    The main thread can poll the queue to update UI without blocking.
    """

    def __init__(self):
        """Initialize the async scanner."""
        self._thread: Optional[threading.Thread] = None
        self._cancelled = threading.Event()
        self._result_queue: queue.Queue = queue.Queue()

    @property
    def is_running(self) -> bool:
        """Check if a scan is currently in progress."""
        return self._thread is not None and self._thread.is_alive()

    def cancel(self) -> None:
        """Request cancellation of the current scan."""
        self._cancelled.set()

    def get_result(self, timeout: float = 0.01) -> Optional[ScanResult]:
        """Get the next result from the queue without blocking.

        Args:
            timeout: Maximum time to wait for a result (default: 10ms)

        Returns:
            ScanResult if available, None if queue is empty
        """
        try:
            return self._result_queue.get_nowait()
        except queue.Empty:
            return None

    def start_scan(self, folder: str, recursive: bool = False,
                   extension_filter: Optional[Set[str]] = None,
                   match_size: bool = False,
                   system_extensions: Optional[Set[str]] = None,
                   ignore_system_prefix: bool = False,
                   exclude_extensions: Optional[Set[str]] = None) -> None:
        """Start an asynchronous scan in a background thread.

        Args:
            folder: Directory path to scan
            recursive: Whether to include subdirectories
            extension_filter: Set of file extensions to include (None = all files)
            match_size: Use size+hash matching instead of filename normalization
            system_extensions: Optional set of ROM/system extensions for prefix stripping
            ignore_system_prefix: Ignore 3-4 digit catalog prefixes on system ROMs
            exclude_extensions: Set of file extensions to skip when extension_filter is None
        """
        if self.is_running:
            return  # Don't start a new scan if one is already running

        # Clear any previous state
        self._cancelled.clear()
        while not self._result_queue.empty():
            try:
                self._result_queue.get_nowait()
            except queue.Empty:
                break

        # Start the scan thread
        self._thread = threading.Thread(
            target=self._scan_thread,
            args=(folder, recursive, extension_filter, match_size,
                  system_extensions, ignore_system_prefix, exclude_extensions),
            daemon=True
        )
        self._thread.start()

    def _scan_thread(self, folder: str, recursive: bool,
                     extension_filter: Optional[Set[str]],
                     match_size: bool,
                     system_extensions: Optional[Set[str]],
                     ignore_system_prefix: bool,
                     exclude_extensions: Optional[Set[str]]) -> None:
        """Internal thread function that performs the actual scan."""
        try:
            import time
            last_update_time = 0.0
            update_interval = 0.05  # 50ms between progress updates (20 updates/sec max)

            def progress_callback(current: int, total: int, msg: str) -> bool:
                """Report progress with time-based throttling."""
                nonlocal last_update_time
                if self._cancelled.is_set():
                    return False  # Signal to stop scanning

                # Throttle progress updates to reduce queue overhead
                now = time.perf_counter()
                if now - last_update_time >= update_interval or current == total:
                    last_update_time = now
                    self._result_queue.put(ScanResult(
                        status=ScanStatus.PROGRESS,
                        progress=current,
                        total=total,
                        message=msg
                    ))
                return True  # Continue scanning

            duplicates, non_duplicates = _scan_folder_internal(
                folder, recursive, extension_filter, match_size,
                progress_callback, system_extensions, ignore_system_prefix,
                exclude_extensions
            )

            if self._cancelled.is_set():
                self._result_queue.put(ScanResult(status=ScanStatus.CANCELLED))
            else:
                self._result_queue.put(ScanResult(
                    status=ScanStatus.COMPLETE,
                    duplicates=duplicates,
                    non_duplicates=non_duplicates
                ))

        except Exception as e:
            self._result_queue.put(ScanResult(
                status=ScanStatus.ERROR,
                error=e,
                message=str(e)
            ))


def _scan_folder_internal(folder: str, recursive: bool,
                          extension_filter: Optional[Set[str]],
                          match_size: bool,
                          progress_callback: Optional[Callable[[int, int, str], bool]],
                          system_extensions: Optional[Set[str]],
                          ignore_system_prefix: bool,
                          exclude_extensions: Optional[Set[str]]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Internal scanning implementation with cancellation support.

    The progress_callback returns True to continue, False to cancel.
    """
    file_list = []
    if recursive:
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
                pass

    groups = {}
    total = len(file_list)
    if total == 0:
        return {}, {}

    # Calculate batch size for progress updates (~100 updates max for smooth UI)
    batch_size = max(1, total // 100)

    if not match_size:
        # Name-based grouping
        for i, full_path in enumerate(file_list):
            if progress_callback and (i % batch_size == 0 or i == total - 1):
                if not progress_callback(i + 1, total, f"Scanning: {os.path.basename(full_path)}"):
                    return {}, {}  # Cancelled
            base = normalize_filename(os.path.basename(full_path), system_extensions, ignore_system_prefix)
            groups.setdefault(base, []).append(full_path)
    else:
        # Size-based grouping with partial hashing
        size_map = {}
        for i, full_path in enumerate(file_list):
            if progress_callback and (i % batch_size == 0 or i == total - 1):
                if not progress_callback(i + 1, total, f"Checking size: {os.path.basename(full_path)}"):
                    return {}, {}  # Cancelled
            try:
                size = os.path.getsize(full_path)
                size_map.setdefault(size, []).append(full_path)
            except Exception:
                pass

        hashed_count = 0
        potential_dupes = [paths for paths in size_map.values() if len(paths) > 1]
        total_to_hash = sum(len(p) for p in potential_dupes)

        for size, paths in size_map.items():
            if len(paths) == 1:
                full_path = paths[0]
                base = normalize_filename(os.path.basename(full_path), system_extensions, ignore_system_prefix)
                groups.setdefault(base, []).append(full_path)
            else:
                for full_path in paths:
                    hashed_count += 1
                    if progress_callback:
                        if not progress_callback(hashed_count, total_to_hash, f"Hashing: {os.path.basename(full_path)}"):
                            return {}, {}  # Cancelled
                    h = get_partial_hash(full_path)
                    _, ext = os.path.splitext(full_path)
                    if h:
                        base = f"Size: {size:,} bytes ({ext.lower()}) [Hash: {h[:8]}]"
                    else:
                        base = f"Size: {size:,} bytes ({ext.lower()})"
                    groups.setdefault(base, []).append(full_path)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    non_duplicates = {k: v for k, v in groups.items() if len(v) == 1}

    return duplicates, non_duplicates


def scan_folder(folder: str, recursive: bool = False, extension_filter: Optional[Set[str]] = None,
                match_size: bool = False, progress_callback: Optional[Callable] = None,
                system_extensions: Optional[Set[str]] = None, ignore_system_prefix: bool = False,
                exclude_extensions: Optional[Set[str]] = None) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Scan folder for duplicate files using name-based or size-based matching.

    This is the synchronous API for backwards compatibility.

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
    # Wrap the old-style callback to match the new internal format
    def wrapped_callback(current: int, total: int, msg: str) -> bool:
        if progress_callback:
            progress_callback(current, total, msg)
        return True  # Always continue (no cancellation in sync mode)

    return _scan_folder_internal(
        folder, recursive, extension_filter, match_size,
        wrapped_callback, system_extensions, ignore_system_prefix,
        exclude_extensions
    )


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
                    if match_name.endswith("-image"):
                        match_name = match_name[:-6]
                    if match_name not in keep_filenames:
                        orphaned.append(full_path)
    except OSError:
        pass

    return orphaned