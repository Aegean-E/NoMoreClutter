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
        with open(src_file, "w") as f:
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
        with open(existing_target, "w") as f:
            f.write("existing content")

        # Source file with same name
        src_file = os.path.join(self.src_dir, "conflict.txt")
        with open(src_file, "w") as f:
            f.write("new content")

        change = FileChange(original=src_file, action="move", new_path=existing_target)
        success, errors = FileExecutor.execute([change])

        self.assertEqual(success, 1)
        self.assertEqual(errors, 0)
        
        # Existing file must NOT be overwritten
        with open(existing_target, "r") as f:
            self.assertEqual(f.read(), "existing content")

        # New file should have been placed at conflict (1).txt
        expected_collision_path = os.path.join(target_dir, "conflict (1).txt")
        self.assertTrue(os.path.exists(expected_collision_path))
        with open(expected_collision_path, "r") as f:
            self.assertEqual(f.read(), "new content")

    def test_persistent_history_across_restarts(self):
        # 1. Execute a move
        src_file = os.path.join(self.src_dir, "persist_test.txt")
        with open(src_file, "w") as f:
            f.write("persistence payload")

        dest_folder = os.path.join(self.dst_dir, "SubArchive")
        dst_file = os.path.join(dest_folder, "persist_test.txt")
        change = FileChange(original=src_file, action="move", new_path=dst_file)

        success, errors = FileExecutor.execute([change])
        self.assertEqual(success, 1)
        self.assertEqual(errors, 0)
        self.assertTrue(os.path.exists(self.test_history_path))

        # 2. Simulate application restart: purge in-memory cache and reset flag
        FileExecutor._history = []
        FileExecutor._loaded = False

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
        with open(dst_file, "w") as f:
            f.write("legacy content")

        legacy_data = [
            [[src_file, dst_file]]
        ]
        with open(self.test_history_path, "w", encoding="utf-8") as f:
            json.dump(legacy_data, f)

        # Reset in-memory cache to force loading legacy data
        FileExecutor._history = []
        FileExecutor._loaded = False

        self.assertTrue(FileExecutor.has_undo())
        summaries = FileExecutor.get_history_summary()
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["count"], 1)

        reverted, errors = FileExecutor.undo_last_batch()
        self.assertEqual(reverted, 1)
        self.assertEqual(errors, 0)
        self.assertTrue(os.path.exists(src_file))
        self.assertFalse(os.path.exists(dst_file))


if __name__ == "__main__":
    unittest.main()
