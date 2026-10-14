"""
Unit tests for DeduplicationService (PRINCIPLE-007, PRINCIPLE-011)
"""

import os
import shutil
import tempfile
import unittest
from services.deduplicator import DeduplicationService


class TestDeduplicationService(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_format_bytes(self):
        self.assertEqual(DeduplicationService.format_bytes(500), "500 B")
        self.assertEqual(DeduplicationService.format_bytes(2048), "2.0 KB")
        self.assertEqual(DeduplicationService.format_bytes(1048576 * 5), "5.00 MB")
        self.assertEqual(DeduplicationService.format_bytes(1073741824 * 2), "2.00 GB")

    def test_no_duplicates(self):
        f1 = os.path.join(self.test_dir, "file1.txt")
        f2 = os.path.join(self.test_dir, "file2.txt")
        with open(f1, "w") as f:
            f.write("Alpha content")
        with open(f2, "w") as f:
            f.write("Beta longer content")

        groups = DeduplicationService.scan_duplicates(self.test_dir)
        self.assertEqual(len(groups), 0)

    def test_exact_duplicates_detected(self):
        content = "Identical payload content replicated across files!" * 10
        f1 = os.path.join(self.test_dir, "original.pdf")
        f2 = os.path.join(self.test_dir, "copy1.pdf")
        f3 = os.path.join(self.test_dir, "copy2.pdf")

        for p in [f1, f2, f3]:
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)

        groups = DeduplicationService.scan_duplicates(self.test_dir)
        self.assertEqual(len(groups), 1)
        group = groups[0]
        self.assertEqual(group.file_size, len(content.encode("utf-8")))
        self.assertEqual(len(group.duplicates), 2)
        self.assertEqual(group.reclaimable_bytes, group.file_size * 2)
        self.assertIn(f1, group.all_files)
        self.assertIn(f2, group.all_files)
        self.assertIn(f3, group.all_files)

    def test_same_size_different_content_not_flagged(self):
        # Two files with identical length but different content
        f1 = os.path.join(self.test_dir, "f1.bin")
        f2 = os.path.join(self.test_dir, "f2.bin")
        with open(f1, "wb") as f:
            f.write(b"A" * 1000)
        with open(f2, "wb") as f:
            f.write(b"B" * 1000)

        groups = DeduplicationService.scan_duplicates(self.test_dir)
        self.assertEqual(len(groups), 0)

    def test_isolate_duplicates(self):
        content = "Data to duplicate"
        f1 = os.path.join(self.test_dir, "doc.txt")
        f2 = os.path.join(self.test_dir, "doc (1).txt")
        with open(f1, "w") as f:
            f.write(content)
        with open(f2, "w") as f:
            f.write(content)

        groups = DeduplicationService.scan_duplicates(self.test_dir)
        self.assertEqual(len(groups), 1)

        moved, errors = DeduplicationService.isolate_duplicates(groups[0].duplicates, self.test_dir)
        self.assertEqual(moved, 1)
        self.assertEqual(len(errors), 0)

        iso_dir = os.path.join(self.test_dir, "_Duplicates")
        self.assertTrue(os.path.exists(iso_dir))
        self.assertTrue(os.path.exists(os.path.join(iso_dir, "doc (1).txt")))
        self.assertTrue(os.path.exists(f1))  # Original preserved

    def test_delete_duplicates(self):
        content = "Data to delete"
        f1 = os.path.join(self.test_dir, "file_a.txt")
        f2 = os.path.join(self.test_dir, "file_b.txt")
        with open(f1, "w") as f:
            f.write(content)
        with open(f2, "w") as f:
            f.write(content)

        groups = DeduplicationService.scan_duplicates(self.test_dir)
        self.assertEqual(len(groups), 1)

        deleted, errors = DeduplicationService.delete_duplicates(groups[0].duplicates)
        self.assertEqual(deleted, 1)
        self.assertEqual(len(errors), 0)
        self.assertFalse(os.path.exists(groups[0].duplicates[0]))
        self.assertTrue(os.path.exists(groups[0].original))

    def test_realtime_on_group_found_callback(self):
        """DeduplicationService must invoke on_group_found in real-time as duplicate clusters are identified."""
        content1 = "Alpha duplicate payload" * 10
        content2 = "Beta duplicate payload with different size" * 15

        # Group 1 (3 identical files)
        for i in range(3):
            with open(os.path.join(self.test_dir, f"grp1_{i}.txt"), "w", encoding="utf-8") as f:
                f.write(content1)

        # Group 2 (2 identical files)
        for i in range(2):
            with open(os.path.join(self.test_dir, f"grp2_{i}.txt"), "w", encoding="utf-8") as f:
                f.write(content2)

        discovered_groups = []
        def on_group(group):
            discovered_groups.append(group)

        returned_groups = DeduplicationService.scan_duplicates(
            self.test_dir,
            on_group_found=on_group,
        )

        self.assertEqual(len(returned_groups), 2)
        self.assertEqual(len(discovered_groups), 2)
        self.assertEqual({g.sha256 for g in returned_groups}, {g.sha256 for g in discovered_groups})


if __name__ == "__main__":
    unittest.main()
