"""
Unit tests for CleanerService (PRINCIPLE-003, PRINCIPLE-007, PRINCIPLE-011)
"""

import os
import shutil
import tempfile
import unittest
from services.cleaner_service import CleanerService


class TestCleanerService(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_detect_empty_folders(self):
        empty1 = os.path.join(self.test_dir, "empty_folder_1")
        nested_empty = os.path.join(self.test_dir, "parent_folder", "child_empty")
        non_empty = os.path.join(self.test_dir, "has_files")

        os.makedirs(empty1)
        os.makedirs(nested_empty)
        os.makedirs(non_empty)

        with open(os.path.join(non_empty, "real_document.pdf"), "w") as f:
            f.write("Important document content")

        items = CleanerService.scan(self.test_dir, scan_empty_dirs=True, scan_zero_byte=False, scan_os_debris=False)
        empty_paths = [it.path for it in items if it.item_type == "empty_dir"]

        self.assertIn(empty1, empty_paths)
        self.assertIn(nested_empty, empty_paths)
        self.assertNotIn(non_empty, empty_paths)

    def test_detect_zero_byte_and_os_debris(self):
        folder = os.path.join(self.test_dir, "sub")
        os.makedirs(folder)

        zero_byte = os.path.join(folder, "empty.tmp")
        with open(zero_byte, "w") as f:
            pass  # 0 bytes

        thumbs = os.path.join(folder, "Thumbs.db")
        with open(thumbs, "w") as f:
            f.write("thumbnail binary cache")

        ds_store = os.path.join(folder, ".DS_Store")
        with open(ds_store, "w") as f:
            f.write("macOS metadata")

        real_file = os.path.join(folder, "user_photo.jpg")
        with open(real_file, "w") as f:
            f.write("Real photo data")

        items = CleanerService.scan(self.test_dir, scan_empty_dirs=False, scan_zero_byte=True, scan_os_debris=True)
        types = {it.path: it.item_type for it in items}

        self.assertEqual(types.get(zero_byte), "zero_byte_file")
        self.assertEqual(types.get(thumbs), "os_debris")
        self.assertEqual(types.get(ds_store), "os_debris")
        self.assertNotIn(real_file, types)

    def test_prune_removes_debris_and_empty_dirs(self):
        empty_folder = os.path.join(self.test_dir, "abandoned_empty")
        os.makedirs(empty_folder)

        zero_file = os.path.join(self.test_dir, "trash.tmp")
        with open(zero_file, "w") as f:
            pass

        items = CleanerService.scan(self.test_dir, scan_empty_dirs=True, scan_zero_byte=True, scan_os_debris=True)
        report = CleanerService.prune(items)

        self.assertFalse(os.path.exists(empty_folder))
        self.assertFalse(os.path.exists(zero_file))
        self.assertIn(empty_folder, report.empty_dirs_removed)
        self.assertIn(zero_file, report.zero_byte_files_removed)


if __name__ == "__main__":
    unittest.main()
