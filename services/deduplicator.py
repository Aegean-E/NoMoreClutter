"""
Smart Duplicate File Finder & Storage Reclaimer (PRINCIPLE-007: Speed & Lean Architecture)
Performs fast O(N) two-stage deduplication (file size match + partial/full SHA-256 chunk hashing)
with zero external dependencies.
"""

import hashlib
import os
import shutil
from collections import defaultdict
from typing import List, Dict, Tuple, Optional, Callable
from models import DuplicateGroup


class DeduplicationService:
    """High-performance file deduplication engine."""

    HEADER_CHUNK_SIZE = 8192      # 8 KB initial header check
    BUFFER_CHUNK_SIZE = 65536     # 64 KB streaming buffer for full hash

    @staticmethod
    def format_bytes(size_bytes: int) -> str:
        """Format raw byte counts into human-readable strings."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    @classmethod
    def compute_header_hash(cls, file_path: str) -> str:
        """Fast 8KB header hash for quick pre-filtering."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            chunk = f.read(cls.HEADER_CHUNK_SIZE)
            hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def compute_full_hash(cls, file_path: str) -> str:
        """Buffered streaming SHA-256 calculation for exact match validation."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(cls.BUFFER_CHUNK_SIZE)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def scan_duplicates(
        cls,
        folder: str,
        recursive: bool = True,
        min_size_bytes: int = 1,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        on_group_found: Optional[Callable[[DuplicateGroup], None]] = None,
    ) -> List[DuplicateGroup]:
        """Scan directory and return list of duplicate groups.
        
        Args:
            folder: Target directory to scan.
            recursive: Whether to scan subdirectories recursively.
            min_size_bytes: Minimum file size to consider (defaults to 1 byte, ignoring empty files).
            progress_callback: Optional callback receiving (status_message, progress_fraction).
            on_group_found: Optional real-time callback invoked immediately when a duplicate group is verified.
            
        Returns:
            List[DuplicateGroup]: Duplicate clusters sorted by reclaimable size descending.
        """
        if not os.path.exists(folder) or not os.path.isdir(folder):
            return []

        # -------------------------------------------------------------
        # Stage 1: Fast O(N) File Size Indexing (Zero I/O Reads)
        # -------------------------------------------------------------
        if progress_callback:
            progress_callback("Scanning file sizes...", 0.05)

        size_map: Dict[int, List[str]] = defaultdict(list)
        all_candidate_paths: List[str] = []

        if recursive:
            for root, _, files in os.walk(folder):
                # Skip isolated duplicates folder from prior runs
                if os.path.basename(root).lower() == "_duplicates":
                    continue
                for f in files:
                    full_p = os.path.join(root, f)
                    try:
                        sz = os.path.getsize(full_p)
                        if sz >= min_size_bytes:
                            size_map[sz].append(full_p)
                            all_candidate_paths.append(full_p)
                    except (OSError, PermissionError):
                        continue
        else:
            try:
                for entry in os.scandir(folder):
                    if entry.is_file():
                        try:
                            sz = entry.stat().st_size
                            if sz >= min_size_bytes:
                                size_map[sz].append(entry.path)
                                all_candidate_paths.append(entry.path)
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                return []

        # Filter out sizes with only 1 file (they cannot be duplicates)
        size_collisions = {sz: paths for sz, paths in size_map.items() if len(paths) > 1}
        total_collision_files = sum(len(paths) for paths in size_collisions.values())

        if total_collision_files == 0:
            if progress_callback:
                progress_callback("No duplicate candidates found.", 1.0)
            return []

        # -------------------------------------------------------------
        # Stage 2: Partial Header Hash Filter (8KB Read)
        # -------------------------------------------------------------
        if progress_callback:
            progress_callback(f"Analyzing {total_collision_files} potential duplicates...", 0.20)

        header_collisions: Dict[Tuple[int, str], List[str]] = defaultdict(list)
        processed_files = 0

        for sz, paths in size_collisions.items():
            for p in paths:
                try:
                    h_hash = cls.compute_header_hash(p)
                    header_collisions[(sz, h_hash)].append(p)
                except (OSError, PermissionError):
                    continue
                processed_files += 1
                if progress_callback and total_collision_files > 0:
                    frac = 0.20 + 0.40 * (processed_files / total_collision_files)
                    progress_callback(f"Checking headers ({processed_files}/{total_collision_files})...", frac)

        # Filter out header groups with only 1 file
        confirmed_header_groups = {k: paths for k, paths in header_collisions.items() if len(paths) > 1}
        full_hash_candidates = sum(len(paths) for paths in confirmed_header_groups.values())

        # -------------------------------------------------------------
        # Stage 3: Full SHA-256 Hash Matching & Real-Time Discovery
        # -------------------------------------------------------------
        results: List[DuplicateGroup] = []
        hashed_files = 0

        def sort_key(filepath: str):
            try:
                mtime = os.path.getmtime(filepath)
            except (OSError, PermissionError):
                mtime = float("inf")
            return (mtime, len(filepath), filepath)

        for (sz, _), paths in confirmed_header_groups.items():
            bucket_exact_groups: Dict[str, List[str]] = defaultdict(list)
            for p in paths:
                try:
                    full_hash = cls.compute_full_hash(p)
                    bucket_exact_groups[full_hash].append(p)
                except (OSError, PermissionError):
                    continue
                hashed_files += 1
                if progress_callback and full_hash_candidates > 0:
                    frac = 0.60 + 0.35 * (hashed_files / full_hash_candidates)
                    progress_callback(f"Verifying exact hashes ({hashed_files}/{full_hash_candidates})...", frac)

            # Instantly materialize confirmed duplicate groups for this bucket
            for full_hash, exact_paths in bucket_exact_groups.items():
                if len(exact_paths) > 1:
                    sorted_paths = sorted(exact_paths, key=sort_key)
                    group = DuplicateGroup(
                        file_size=sz,
                        sha256=full_hash,
                        original=sorted_paths[0],
                        duplicates=sorted_paths[1:],
                    )
                    results.append(group)
                    if on_group_found:
                        try:
                            on_group_found(group)
                        except Exception:
                            pass

        # Sort groups by total reclaimable bytes descending for final return
        results.sort(key=lambda g: g.reclaimable_bytes, reverse=True)

        if progress_callback:
            progress_callback(f"Done! Found {len(results)} duplicate groups.", 1.0)

        return results

    @classmethod
    def isolate_duplicates(
        cls,
        duplicate_paths: List[str],
        base_folder: str,
        isolate_folder_name: str = "_Duplicates",
    ) -> Tuple[int, List[str]]:
        """Safely move selected duplicate files into a dedicated isolation folder.
        
        Preserves original relative structure or collision names safely.
        Returns:
            Tuple[int, List[str]]: (Count of files successfully moved, List of error messages)
        """
        target_dir = os.path.join(base_folder, isolate_folder_name)
        os.makedirs(target_dir, exist_ok=True)

        moved_count = 0
        errors: List[str] = []

        for path in duplicate_paths:
            if not os.path.exists(path):
                continue
            try:
                filename = os.path.basename(path)
                dest = os.path.join(target_dir, filename)

                # Collision-safe destination name
                counter = 1
                stem, ext = os.path.splitext(filename)
                while os.path.exists(dest):
                    dest = os.path.join(target_dir, f"{stem} ({counter}){ext}")
                    counter += 1

                shutil.move(path, dest)
                moved_count += 1
            except Exception as e:
                errors.append(f"{os.path.basename(path)}: {e}")

        return moved_count, errors

    @classmethod
    def delete_duplicates(cls, duplicate_paths: List[str]) -> Tuple[int, List[str]]:
        """Permanently delete specified duplicate files safely.
        
        Returns:
            Tuple[int, List[str]]: (Count of files deleted, List of error messages)
        """
        deleted_count = 0
        errors: List[str] = []

        for path in duplicate_paths:
            if not os.path.exists(path):
                continue
            try:
                os.remove(path)
                deleted_count += 1
            except Exception as e:
                errors.append(f"{os.path.basename(path)}: {e}")

        return deleted_count, errors
