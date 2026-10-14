"""
Unit tests for In-App File Viewer & Visual Duplicate Inspector (PRINCIPLE-003, PRINCIPLE-007, PRINCIPLE-011).
Tests pure preview decoding, metadata formatting, hexdump generation, and aspect ratio scaling
without initializing GUI/Tkinter widgets (preventing headless memory exhaustion).
"""

import os
import tempfile
import unittest

from ui.file_viewer import (
    get_category_badge,
    get_file_meta_summary,
    compute_image_preview_size,
    read_text_preview,
    generate_hexdump,
    IMAGE_EXTENSIONS,
    TEXT_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
)


class TestFileViewerPureLogic(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.test_text_file = os.path.join(self.tmpdir.name, "sample.txt")
        with open(self.test_text_file, "w", encoding="utf-8") as f:
            f.write("Line 1: Hello NoMoreClutter\nLine 2: Testing File Viewer\nLine 3: Aesthetic Dark Mode\n")

        self.test_py_file = os.path.join(self.tmpdir.name, "script.py")
        with open(self.test_py_file, "w", encoding="utf-8") as f:
            f.write("def test():\n    return True\n")

        self.test_bin_file = os.path.join(self.tmpdir.name, "binary.dat")
        with open(self.test_bin_file, "wb") as f:
            f.write(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F" * 4)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_category_badges(self):
        self.assertEqual(get_category_badge(".png"), "🖼️ Image")
        self.assertEqual(get_category_badge(".jpg"), "🖼️ Image")
        self.assertEqual(get_category_badge(".webp"), "🖼️ Image")
        self.assertEqual(get_category_badge(".txt"), "📝 Text/Code")
        self.assertEqual(get_category_badge(".py"), "📝 Text/Code")
        self.assertEqual(get_category_badge(".json"), "📝 Text/Code")
        self.assertEqual(get_category_badge(".pdf"), "📄 Document")
        self.assertEqual(get_category_badge(".docx"), "📄 Document")
        self.assertEqual(get_category_badge(".mp4"), "🎬 Media")
        self.assertEqual(get_category_badge(".zip"), "📦 Archive")
        self.assertEqual(get_category_badge(".unknown_ext"), "📁 File")

    def test_file_meta_summary(self):
        summary = get_file_meta_summary(self.test_text_file)
        self.assertIn("Size:", summary)
        self.assertIn("Modified:", summary)
        self.assertIn("bytes", summary)

        missing_summary = get_file_meta_summary("non_existent_file_xyz.txt")
        self.assertEqual(missing_summary, "File does not exist on disk.")

    def test_binary_hexdump_generation(self):
        raw_bytes = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F"
        hexdump_text = generate_hexdump(raw_bytes)
        self.assertIn("00000000:", hexdump_text)
        self.assertIn("00 01 02 03", hexdump_text)
        self.assertIn("0F", hexdump_text)

        empty_hexdump = generate_hexdump(b"")
        self.assertEqual(empty_hexdump, "[0-byte Empty File]")

    def test_text_reading_logic(self):
        rendered_text = read_text_preview(self.test_text_file, max_lines=2)
        self.assertIn("Hello NoMoreClutter", rendered_text)
        self.assertIn("Testing File Viewer", rendered_text)
        self.assertNotIn("Aesthetic Dark Mode", rendered_text)  # Capped at 2 lines

        missing_text = read_text_preview("non_existent_file_xyz.txt")
        self.assertIn("File not found", missing_text)

    def test_image_dimension_scaling(self):
        # 1. Image fits within bounds (no downscale)
        w, h, scale = compute_image_preview_size(orig_w=200, orig_h=150, max_w=400, max_h=300)
        self.assertEqual((w, h), (200, 150))
        self.assertEqual(scale, 1.0)

        # 2. Wide landscape image downscaled
        w, h, scale = compute_image_preview_size(orig_w=800, orig_h=400, max_w=400, max_h=300)
        self.assertEqual(w, 400)
        self.assertEqual(h, 200)
        self.assertEqual(scale, 0.5)

        # 3. Tall portrait image downscaled
        w, h, scale = compute_image_preview_size(orig_w=400, orig_h=1200, max_w=400, max_h=300)
        self.assertEqual(h, 300)
        self.assertEqual(w, 100)
        self.assertEqual(scale, 0.25)

        # 4. Zero / invalid dimension guard
        w, h, scale = compute_image_preview_size(orig_w=0, orig_h=0, max_w=400, max_h=300)
        self.assertEqual((w, h), (1, 1))

    def test_compare_mode_determination(self):
        dup_file = os.path.join(self.tmpdir.name, "sample_copy.txt")
        with open(dup_file, "w", encoding="utf-8") as f:
            f.write("duplicate content")

        # Both files exist: compare mode is active
        is_compare = bool(dup_file and os.path.exists(dup_file))
        self.assertTrue(is_compare)

        # Non-existent comparison file: compare mode inactive
        missing_cmp = os.path.join(self.tmpdir.name, "missing.txt")
        is_compare_missing = bool(missing_cmp and os.path.exists(missing_cmp))
        self.assertFalse(is_compare_missing)


if __name__ == "__main__":
    unittest.main()
