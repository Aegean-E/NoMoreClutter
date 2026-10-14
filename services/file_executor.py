"""
Safe File Operations & Persistent Multi-Session Undo Management (PRINCIPLE-007: Reliability)
Guarantees collision avoidance, directory creation, atomic persistent history logging,
and multi-session rollback capabilities that survive application restarts.
"""

import json
import os
import shutil
import time
from datetime import datetime
from typing import List, Tuple, Dict, Optional, Any
from models import FileChange


class FileExecutor:
    """Safe execution engine with persistent multi-session undo tracking and collision resolution."""

    # Path to persistent history file
    history_file_path: str = "history.json"

    # In-memory batch history: list of batch dicts
    # Each batch dict: {"batch_id": str, "timestamp": float, "timestamp_str": str, "moves": List[Tuple[str, str]]}
    _history: List[Dict[str, Any]] = []
    _loaded: bool = False

    @classmethod
    def _ensure_loaded(cls):
        """Lazy load history from disk on first access."""
        if not cls._loaded:
            cls._load_history()
            cls._loaded = True

    @classmethod
    def _load_history(cls):
        """Load persistent history from disk."""
        if os.path.exists(cls.history_file_path):
            try:
                with open(cls.history_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        cls._history = data
                    else:
                        cls._history = []
            except Exception as e:
                print(f"FileExecutor Warning: Failed to load history from {cls.history_file_path}: {e}")
                cls._history = []
        else:
            cls._history = []

    @classmethod
    def _save_history(cls):
        """Atomically persist operation history to disk."""
        try:
            if not cls._history:
                if os.path.exists(cls.history_file_path):
                    try:
                        os.remove(cls.history_file_path)
                    except Exception:
                        pass
                return

            tmp_path = cls.history_file_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(cls._history, f, indent=2, ensure_ascii=False)
            
            # Atomic file replacement
            if os.path.exists(cls.history_file_path):
                os.replace(tmp_path, cls.history_file_path)
            else:
                os.rename(tmp_path, cls.history_file_path)
        except Exception as e:
            print(f"FileExecutor Error: Failed to save history to {cls.history_file_path}: {e}")

    @classmethod
    def execute(cls, changes: List[FileChange]) -> Tuple[int, int]:
        """Safely execute a list of file changes with collision resolution and persistent tracking."""
        cls._ensure_loaded()
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
            now = time.time()
            now_str = datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S")
            batch_id = f"batch_{int(now)}_{len(current_batch_moves)}"
            
            cls._history.append({
                "batch_id": batch_id,
                "timestamp": now,
                "timestamp_str": now_str,
                "moves": current_batch_moves
            })
            cls._save_history()

        return success, errors

    @classmethod
    def undo_last_batch(cls) -> Tuple[int, int]:
        """
        Revert the most recent batch of moved files back to their original locations.
        Persists updated history and cleans up newly empty destination directories.
        
        Returns:
            Tuple[int, int]: (reverted_count, errors_count)
        """
        cls._ensure_loaded()
        if not cls._history:
            return 0, 0

        last_batch_record = cls._history.pop()
        
        # Support both legacy raw list format and new dictionary format
        if isinstance(last_batch_record, dict):
            last_batch_moves = last_batch_record.get("moves", [])
        else:
            last_batch_moves = last_batch_record

        reverted = 0
        errors = 0
        destination_dirs_to_check = set()

        # Undo in reverse order
        for original, executed in reversed(last_batch_moves):
            try:
                if os.path.exists(executed):
                    orig_dir = os.path.dirname(original)
                    os.makedirs(orig_dir, exist_ok=True)
                    safe_orig = cls._resolve_collision(original)
                    shutil.move(executed, safe_orig)
                    reverted += 1
                    
                    # Track destination folder for empty folder cleanup
                    dest_parent = os.path.dirname(executed)
                    destination_dirs_to_check.add(dest_parent)
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                print(f"Undo Error restoring '{executed}' -> '{original}': {e}")

        # Clean up empty created folders
        for folder in destination_dirs_to_check:
            try:
                if os.path.exists(folder) and not os.listdir(folder):
                    os.rmdir(folder)
            except Exception:
                pass

        cls._save_history()
        return reverted, errors

    @classmethod
    def has_undo(cls) -> bool:
        """Check if any operations can be undone (including from previous sessions)."""
        cls._ensure_loaded()
        return len(cls._history) > 0

    @classmethod
    def get_history_summary(cls) -> List[Dict[str, Any]]:
        """Return a user-readable summary of past batches for UI display."""
        cls._ensure_loaded()
        summaries = []
        for b in reversed(cls._history):
            if isinstance(b, dict):
                summaries.append({
                    "batch_id": b.get("batch_id", "unknown"),
                    "timestamp_str": b.get("timestamp_str", "unknown"),
                    "count": len(b.get("moves", []))
                })
            elif isinstance(b, list):
                summaries.append({
                    "batch_id": "legacy_batch",
                    "timestamp_str": "earlier session",
                    "count": len(b)
                })
        return summaries

    @classmethod
    def clear_history(cls):
        """Reset in-memory and persistent operation history."""
        cls._history.clear()
        cls._loaded = True
        if os.path.exists(cls.history_file_path):
            try:
                os.remove(cls.history_file_path)
            except Exception:
                pass

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
