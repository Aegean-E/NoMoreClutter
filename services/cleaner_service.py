"""
Orphan Folder & Junk Pruner Service (PRINCIPLE-003: Modularity, PRINCIPLE-007: Speed & Safety)
Recursively identifies and safely removes empty directories, zero-byte junk files,
and OS debris (Thumbs.db, .DS_Store, desktop.ini) with zero external dependencies.
"""

import os
from typing import Any, List, Optional, Callable
from models import CleanupItem, CleanupReport


class CleanerService:
    """Safely cleans empty folders, zero-byte artifacts, and system junk."""

    OS_DEBRIS_FILENAMES = {
        "thumbs.db",
        ".ds_store",
        "desktop.ini",
        "ehthumbs.db",
        "ehthumbs_vista.db",
        ".spotlight-v100",
        ".trashes",
    }

    OS_DEBRIS_EXTENSIONS = {
        ".crdownload",  # Incomplete browser download leftover if 0-byte or orphaned
    }

    @classmethod
    def is_os_debris(cls, filename: str) -> bool:
        """Check if a filename is known operating system debris or thumbnail cache."""
        lower = filename.lower().strip()
        if lower in cls.OS_DEBRIS_FILENAMES:
            return True
        if lower.startswith("~$"):  # Temporary MS Office lock file
            return True
        return False

    @classmethod
    def scan(
        cls,
        folder: str,
        scan_empty_dirs: bool = True,
        scan_zero_byte: bool = True,
        scan_os_debris: bool = True,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        cancel_event: Optional[Any] = None,
    ) -> List[CleanupItem]:
        """Scan directory and return a structured list of cleanup candidates.
        
        Args:
            folder: Target directory to clean.
            scan_empty_dirs: Flag to detect empty folders.
            scan_zero_byte: Flag to detect 0-byte orphaned files.
            scan_os_debris: Flag to detect OS metadata/debris (Thumbs.db, .DS_Store).
            progress_callback: Optional progress reporter.
            cancel_event: Optional threading.Event to signal abort.
            
        Returns:
            List[CleanupItem]: List of proposed cleanup items.
        """
        if not os.path.exists(folder) or not os.path.isdir(folder):
            return []

        if progress_callback:
            progress_callback("Analyzing directory tree for junk and empty folders...", 0.1)

        cleanup_items: List[CleanupItem] = []
        all_dirs: List[str] = []

        # 1. Walk top-down to find OS debris and zero-byte files
        for root, dirs, files in os.walk(folder):
            if cancel_event and cancel_event.is_set():
                return cleanup_items

            all_dirs.append(root)

            for f in files:
                if cancel_event and cancel_event.is_set():
                    return cleanup_items

                full_path = os.path.join(root, f)
                try:
                    size = os.path.getsize(full_path)
                except (OSError, PermissionError):
                    continue

                # Check OS debris
                if scan_os_debris and cls.is_os_debris(f):
                    cleanup_items.append(CleanupItem(
                        path=full_path,
                        item_type="os_debris",
                        size_bytes=size,
                        reason=f"System artifact / cache ({f})",
                    ))
                    continue

                # Check zero-byte orphaned files
                if scan_zero_byte and size == 0:
                    cleanup_items.append(CleanupItem(
                        path=full_path,
                        item_type="zero_byte_file",
                        size_bytes=0,
                        reason="Zero-byte empty file",
                    ))

        # 2. Walk bottom-up (deepest directories first) to find truly empty directories
        if scan_empty_dirs:
            if progress_callback:
                progress_callback("Checking for empty orphan folders...", 0.5)

            # To accurately identify directories that become empty after deleting junk files,
            # we track files slated for deletion
            pending_deleted_files = {item.path for item in cleanup_items if item.item_type != "empty_dir"}
            pending_deleted_dirs = set()

            # Sort directories by path depth descending so we check leaves first
            sorted_dirs = sorted(all_dirs, key=lambda p: p.count(os.sep), reverse=True)

            for d in sorted_dirs:
                if cancel_event and cancel_event.is_set():
                    return cleanup_items
                # Do not delete the root scan directory itself
                if os.path.abspath(d) == os.path.abspath(folder):
                    continue

                try:
                    entries = os.listdir(d)
                except (OSError, PermissionError):
                    continue

                # An entry is considered "remaining" if it's neither an empty dir nor a junk file
                active_entries = []
                for entry in entries:
                    entry_path = os.path.join(d, entry)
                    if entry_path in pending_deleted_files:
                        continue
                    if entry_path in pending_deleted_dirs:
                        continue
                    active_entries.append(entry)

                if len(active_entries) == 0:
                    # Directory is empty or will be empty once debris is pruned
                    pending_deleted_dirs.add(d)
                    cleanup_items.append(CleanupItem(
                        path=d,
                        item_type="empty_dir",
                        size_bytes=0,
                        reason="Empty directory (no user files)",
                    ))

        if progress_callback:
            progress_callback(f"Found {len(cleanup_items)} cleanup candidates.", 1.0)

        return cleanup_items

    @classmethod
    def prune(
        cls,
        items: List[CleanupItem],
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> CleanupReport:
        """Execute cleanup on specified items safely.
        
        Files (debris, zero-byte) are removed first.
        Empty directories are removed bottom-up using os.rmdir() (which safely fails if not empty).
        
        Returns:
            CleanupReport: Summary of deleted files and folders.
        """
        report = CleanupReport(scanned_items=len(items))

        # Partition items
        files_to_remove = [it for it in items if it.item_type in ("os_debris", "zero_byte_file")]
        dirs_to_remove = [it for it in items if it.item_type == "empty_dir"]

        # Sort directories leaf-first (deepest path first)
        dirs_to_remove.sort(key=lambda it: it.path.count(os.sep), reverse=True)

        total_actions = len(files_to_remove) + len(dirs_to_remove)
        current_step = 0

        # Step 1: Remove junk files
        for it in files_to_remove:
            current_step += 1
            if not os.path.exists(it.path):
                continue
            try:
                sz = os.path.getsize(it.path)
                os.remove(it.path)
                report.reclaimed_bytes += sz
                if it.item_type == "os_debris":
                    report.os_debris_removed.append(it.path)
                else:
                    report.zero_byte_files_removed.append(it.path)
            except (OSError, PermissionError):
                continue

            if progress_callback and total_actions > 0:
                progress_callback(f"Removing files ({current_step}/{total_actions})...", current_step / total_actions)

        # Step 2: Remove empty directories
        for it in dirs_to_remove:
            current_step += 1
            if not os.path.exists(it.path) or not os.path.isdir(it.path):
                continue
            try:
                # os.rmdir() only removes empty directories, ensuring zero accidental data loss
                os.rmdir(it.path)
                report.empty_dirs_removed.append(it.path)
            except (OSError, PermissionError):
                # Directory wasn't empty or permission denied - safe skip
                continue

            if progress_callback and total_actions > 0:
                progress_callback(f"Pruning folders ({current_step}/{total_actions})...", current_step / total_actions)

        if progress_callback:
            progress_callback("Cleanup complete!", 1.0)

        return report
