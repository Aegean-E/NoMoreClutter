"""
Unit tests for FileExecutor (PRINCIPLE-007)
Tests collision avoidance, safe moves, and undo management.
"""

import os
import shutil
import tempfile
import unittest
from models import FileChange
from services.file_executor import FileExecutor


class TestFileExecutor(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.src_dir = os.path.join(self.test_dir, "source")
        self.dst_dir = os.path.join(self.test_dir, "dest")
        os.makedirs(self.src_dir, exist_ok=True)
        os.makedirs(self.dst_dir, exist_ok=True)
        
        # Isolate history file to temporary test directory
        self.orig_history_path = FileExecutor.history_file_path
        self.test_history_path = os.path.join(self.test_dir, "test_history.json")
        FileExecutor.history_file_path = self.test_history_path
        FileExecutor.clear_history()

    def tearDown(self):
        FileExecutor.clear_history()
        FileExecutor.history_file_path = self.orig_history_path
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_execute_move_and_undo(self):
        # Create test file
        src_file = os.path.join(self.src_dir, "sample.txt")
        with open(src_file, "w", encoding="utf-8") as f:
            f.write("hello world")

        dst_file = os.path.join(self.dst_dir, "Docs", "sample.txt")
        change = FileChange(original=src_file, action="move", new_path=dst_file)

        # 1. Execute move
        success, errors = FileExecutor.execute([change])
        self.assertEqual(success, 1)
        self.assertEqual(errors, 0)
        self.assertFalse(os.path.exists(src_file))
        self.assertTrue(os.path.exists(dst_file))
        self.assertTrue(FileExecutor.has_undo())

        # 2. Undo move
        reverted, undo_errors = FileExecutor.undo_last_batch()
        self.assertEqual(reverted, 1)
        self.assertEqual(undo_errors, 0)
        self.assertTrue(os.path.exists(src_file))
        self.assertFalse(os.path.exists(dst_file))

    def test_collision_avoidance(self):
        # Existing file at destination
        target_dir = os.path.join(self.dst_dir, "Docs")
        os.makedirs(target_dir, exist_ok=True)
        existing_target = os.path.join(target_dir, "conflict.txt")
        with open(existing_target, "w", encoding="utf-8") as f:
            f.write("existing content")

        # Source file with same name
        src_file = os.path.join(self.src_dir, "conflict.txt")
        with open(src_file, "w", encoding="utf-8") as f:
            f.write("new content")

        change = FileChange(original=src_file, action="move", new_path=existing_target)
        success, errors = FileExecutor.execute([change])

        self.assertEqual(success, 1)
        self.assertEqual(errors, 0)
        
        # Existing file must NOT be overwritten
        with open(existing_target, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "existing content")

        # New file should have been placed at conflict (1).txt
        expected_collision_path = os.path.join(target_dir, "conflict (1).txt")
        self.assertTrue(os.path.exists(expected_collision_path))
        with open(expected_collision_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "new content")

    def test_persistent_history_across_restarts(self):
        # 1. Execute a move
        src_file = os.path.join(self.src_dir, "persist_test.txt")
        with open(src_file, "w", encoding="utf-8") as f:
            f.write("persistence payload")

        dest_folder = os.path.join(self.dst_dir, "SubArchive")
        dst_file = os.path.join(dest_folder, "persist_test.txt")
        change = FileChange(original=src_file, action="move", new_path=dst_file)

        success, errors = FileExecutor.execute([change])
        self.assertEqual(success, 1)
        self.assertEqual(errors, 0)
        self.assertTrue(os.path.exists(self.test_history_path))

        # 2. Simulate application restart: purge in-memory cache and reset flag
        FileExecutor.reset_state()

        # Verify history reloaded from disk on access
        self.assertTrue(FileExecutor.has_undo())
        summaries = FileExecutor.get_history_summary()
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["count"], 1)

        # 3. Perform undo across restart
        reverted, undo_errors = FileExecutor.undo_last_batch()
        self.assertEqual(reverted, 1)
        self.assertEqual(undo_errors, 0)
        self.assertTrue(os.path.exists(src_file))
        self.assertFalse(os.path.exists(dst_file))
        # Empty created directory should have been cleaned up
        self.assertFalse(os.path.exists(dest_folder))

        # History should now be empty and persistent file cleaned up
        self.assertFalse(FileExecutor.has_undo())
        self.assertFalse(os.path.exists(self.test_history_path))

    def test_legacy_history_format_compatibility(self):
        import json
        # Write legacy format (list of list of tuples) directly to history file
        src_file = os.path.join(self.src_dir, "legacy.txt")
        dst_file = os.path.join(self.dst_dir, "Legacy", "legacy.txt")
        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
        with open(dst_file, "w", encoding="utf-8") as f:
            f.write("legacy content")

        legacy_data = [
            [[src_file, dst_file]]
        ]
        with open(self.test_history_path, "w", encoding="utf-8") as f:
            json.dump(legacy_data, f)

        # Reset in-memory cache to force loading legacy data
        FileExecutor.reset_state()

        self.assertTrue(FileExecutor.has_undo())
        summaries = FileExecutor.get_history_summary()
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["count"], 1)

        reverted, errors = FileExecutor.undo_last_batch()
        self.assertEqual(reverted, 1)
        self.assertEqual(errors, 0)
        self.assertTrue(os.path.exists(src_file))
        self.assertFalse(os.path.exists(dst_file))

    def test_crash_resilience_corrupted_history_quarantine(self):
        """A half-written/corrupt history file from a power outage must be quarantined safely without crashing."""
        # Simulate abrupt power outage producing a truncated corrupt JSON file
        with open(self.test_history_path, "w", encoding="utf-8") as f:
            f.write('[{"batch_id": "batch_partial", "timestamp": 12345, "moves": [["/path/a", "/path/b"]')  # Unterminated JSON

        FileExecutor.reset_state()

        # Loading history must not crash
        self.assertFalse(FileExecutor.has_undo())
        self.assertEqual(len(FileExecutor._history), 0)

        # Corrupt file must have been quarantined with a .corrupt_ timestamp suffix
        corrupt_files = [fn for fn in os.listdir(self.test_dir) if "corrupt_" in fn]
        self.assertGreater(len(corrupt_files), 0)

    def test_incremental_wal_journaling_recovers_interrupted_batch(self):
        """Incremental WAL records partial moves so an interrupted session can be undone."""
        src1 = os.path.join(self.src_dir, "wal1.txt")
        src2 = os.path.join(self.src_dir, "wal2.txt")
        dst1 = os.path.join(self.dst_dir, "wal1.txt")
        dst2 = os.path.join(self.dst_dir, "wal2.txt")

        with open(src1, "w", encoding="utf-8") as f:
            f.write("wal1")
        with open(src2, "w", encoding="utf-8") as f:
            f.write("wal2")

        changes = [
            FileChange(original=src1, action="move", new_path=dst1),
            FileChange(original=src2, action="move", new_path=dst2),
        ]

        success, errors = FileExecutor.execute(changes)
        self.assertEqual(success, 2)
        self.assertEqual(errors, 0)

        # Inspect disk representation: should have 'status': 'completed'
        with open(self.test_history_path, "r", encoding="utf-8") as f:
            import json
            disk_data = json.load(f)

        self.assertEqual(len(disk_data), 1)
        self.assertEqual(disk_data[0]["status"], "completed")
        self.assertEqual(len(disk_data[0]["moves"]), 2)

        # Simulate simulated power outage in-progress marker
        disk_data[0]["status"] = "in_progress"
        with open(self.test_history_path, "w", encoding="utf-8") as f:
            json.dump(disk_data, f)

        # Reset cache and reload as if app restarted after crash
        FileExecutor.reset_state()

        self.assertTrue(FileExecutor.has_undo())
        # Status must have transitioned to interrupted_recovered
        self.assertEqual(FileExecutor._history[0]["status"], "interrupted_recovered")

        # Must still undo cleanly
        reverted, undo_errors = FileExecutor.undo_last_batch()
        self.assertEqual(reverted, 2)
        self.assertEqual(undo_errors, 0)
        self.assertTrue(os.path.exists(src1))
        self.assertTrue(os.path.exists(src2))


if __name__ == "__main__":
    unittest.main()
