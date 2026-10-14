"""
Safe File Operations & Undo Management (PRINCIPLE-007: Performance & Reliability)
Guarantees collision avoidance, directory creation, and rollback capabilities.
"""

import os
import shutil
import time
from typing import List, Tuple, Dict, Optional
from models import FileChange


class FileExecutor:
    """Safe execution engine for file reorganization with collision avoidance and undo tracking."""

    # In-memory batch history: list of batches, each batch is list of (from_path, to_path)
    _history: List[List[Tuple[str, str]]] = []

    @classmethod
    def execute(cls, changes: List[FileChange]) -> Tuple[int, int]:
        """Safely execute a list of file changes with collision resolution and history tracking."""
        success = 0
        errors = 0
        current_batch_moves: List[Tuple[str, str]] = []

        for change in changes:
            try:
                if not os.path.exists(change.original):
                    print(f"FileExecutor Warning: Source file does not exist: {change.original}")
                    errors += 1
                    continue

                dest_dir = os.path.dirname(change.new_path)
                os.makedirs(dest_dir, exist_ok=True)

                # Collision safety: resolve conflicting target filenames
                safe_dest = cls._resolve_collision(change.new_path)

                if change.action == "move":
                    shutil.move(change.original, safe_dest)
                else:
                    shutil.copy2(change.original, safe_dest)
                    os.remove(change.original)

                # Update change object with actual path used
                change.new_path = safe_dest
                current_batch_moves.append((change.original, safe_dest))
                success += 1

            except Exception as e:
                errors += 1
                print(f"FileExecutor Error moving '{change.original}' -> '{change.new_path}': {e}")

        if current_batch_moves:
            cls._history.append(current_batch_moves)

        return success, errors

    @classmethod
    def undo_last_batch(cls) -> Tuple[int, int]:
        """Revert the most recent batch of moved files back to their original locations.
        
        Returns:
            Tuple[int, int]: (reverted_count, errors_count)
        """
        if not cls._history:
            return 0, 0

        last_batch = cls._history.pop()
        reverted = 0
        errors = 0

        # Undo in reverse order
        for original, executed in reversed(last_batch):
            try:
                if os.path.exists(executed):
                    orig_dir = os.path.dirname(original)
                    os.makedirs(orig_dir, exist_ok=True)
                    safe_orig = cls._resolve_collision(original)
                    shutil.move(executed, safe_orig)
                    reverted += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                print(f"Undo Error restoring '{executed}' -> '{original}': {e}")

        return reverted, errors

    @classmethod
    def has_undo(cls) -> bool:
        """Check if any operations can be undone."""
        return len(cls._history) > 0

    @classmethod
    def clear_history(cls):
        """Reset operation history."""
        cls._history.clear()

    @staticmethod
    def _resolve_collision(target_path: str) -> str:
        """If destination file exists, append a counter: 'file (1).ext' to avoid data loss."""
        if not os.path.exists(target_path):
            return target_path

        base_dir = os.path.dirname(target_path)
        base_name, ext = os.path.splitext(os.path.basename(target_path))
        
        counter = 1
        while True:
            candidate = os.path.join(base_dir, f"{base_name} ({counter}){ext}")
            if not os.path.exists(candidate):
                return candidate
            counter += 1
