"""
Unit tests for FileScanner (PRINCIPLE-011).
Tests shallow and recursive scanning, extension filtering, and category lookups.
"""

import os
import tempfile
import unittest
from services.file_scanner import FileScanner


class TestFileScanner(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.root = self.test_dir.name

        # Create test directory structure:
        # root/
        #   img1.jpg
        #   doc1.pdf
        #   subfolder/
        #     img2.png
        #     doc2.txt
        #     nested/
        #       script.py
        self.img1 = os.path.join(self.root, "img1.jpg")
        self.doc1 = os.path.join(self.root, "doc1.pdf")
        with open(self.img1, "w") as f:
            f.write("image1")
        with open(self.doc1, "w") as f:
            f.write("doc1")

        self.subfolder = os.path.join(self.root, "subfolder")
        os.makedirs(self.subfolder)
        self.img2 = os.path.join(self.subfolder, "img2.png")
        self.doc2 = os.path.join(self.subfolder, "doc2.txt")
        with open(self.img2, "w") as f:
            f.write("image2")
        with open(self.doc2, "w") as f:
            f.write("doc2")

        self.nested = os.path.join(self.subfolder, "nested")
        os.makedirs(self.nested)
        self.script = os.path.join(self.nested, "script.py")
        with open(self.script, "w") as f:
            f.write("print('hello')")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_scan_folder_shallow(self):
        """Shallow scan should only return matching files in the root folder."""
        results = FileScanner.scan_folder(self.root, [".jpg", ".pdf"], include_subfolders=False)
        self.assertEqual(len(results), 2)
        self.assertIn(self.img1, results)
        self.assertIn(self.doc1, results)

    def test_scan_folder_shallow_filters_extensions(self):
        """Only specified extensions should be returned."""
        results = FileScanner.scan_folder(self.root, [".jpg"], include_subfolders=False)
        self.assertEqual(len(results), 1)
        self.assertIn(self.img1, results)
        self.assertNotIn(self.doc1, results)

    def test_scan_folder_recursive(self):
        """Recursive scan should include files across all subdirectories."""
        results = FileScanner.scan_folder(self.root, [".jpg", ".png", ".py"], include_subfolders=True)
        self.assertEqual(len(results), 3)
        self.assertIn(self.img1, results)
        self.assertIn(self.img2, results)
        self.assertIn(self.script, results)

    def test_scan_empty_or_invalid_folder(self):
        """Scanning an empty folder or with empty extensions should return an empty list."""
        self.assertEqual(FileScanner.scan_folder("", [".jpg"]), [])
        self.assertEqual(FileScanner.scan_folder(self.root, []), [])

    def test_get_extension(self):
        """Extension extraction should be lowercase with leading dot."""
        self.assertEqual(FileScanner.get_extension("TEST.PNG"), ".png")
        self.assertEqual(FileScanner.get_extension("archive.tar.gz"), ".gz")
        self.assertEqual(FileScanner.get_extension("no_ext"), "")

    def test_get_category(self):
        """Category matching should return the correct category name or 'Other'."""
        categories = {
            "Images": [".jpg", ".png"],
            "Documents": [".pdf", ".txt"]
        }
        self.assertEqual(FileScanner.get_category(".jpg", categories), "Images")
        self.assertEqual(FileScanner.get_category(".pdf", categories), "Documents")
        self.assertEqual(FileScanner.get_category(".exe", categories), "Other")


if __name__ == "__main__":
    unittest.main()
