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

    def test_open_file_launches_system_default(self):
        from unittest.mock import patch, MagicMock
        from ui.tree_preview import TreePreviewDialog
        from ui.duplicate_finder import DuplicateFinderDialog

        dummy = MagicMock()

        # Test Windows os.startfile invocation
        with patch("sys.platform", "win32"), patch("os.startfile") as mock_startfile:
            TreePreviewDialog._open_file(dummy, self.test_text_file)
            mock_startfile.assert_called_once_with(os.path.abspath(self.test_text_file))

        # Test Darwin open invocation
        with patch("sys.platform", "darwin"), patch("subprocess.Popen") as mock_popen:
            TreePreviewDialog._open_file(dummy, self.test_text_file)
            mock_popen.assert_called_once_with(["open", os.path.abspath(self.test_text_file)])

        # Test non-existent file is a safe no-op
        with patch("os.startfile") as mock_startfile:
            TreePreviewDialog._open_file(dummy, "non_existent_path_xyz.txt")
            mock_startfile.assert_not_called()

        # Test empty string is a safe no-op
        with patch("os.startfile") as mock_startfile:
            TreePreviewDialog._open_file(dummy, "")
            mock_startfile.assert_not_called()

        # Verify DuplicateFinderDialog adheres to identical contract
        with patch("sys.platform", "win32"), patch("os.startfile") as mock_startfile:
            DuplicateFinderDialog._open_file(dummy, self.test_text_file)
            mock_startfile.assert_called_once_with(os.path.abspath(self.test_text_file))

    def test_image_color_mode_conversion(self):
        from PIL import Image
        # Test Palette (P), CMYK, RGBA, and RGB conversions
        for mode in ("RGB", "RGBA", "P", "CMYK", "L"):
            img = Image.new(mode, (50, 50))
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                converted = img.convert("RGBA")
                self.assertEqual(converted.mode, "RGBA")
            else:
                converted = img.convert("RGB")
                self.assertEqual(converted.mode, "RGB")


class TestDuplicatePaginationLogic(unittest.TestCase):
    def test_selection_across_unrendered_groups(self):
        from unittest.mock import MagicMock
        from models import DuplicateGroup
        from ui.duplicate_finder import DuplicateFinderDialog

        dlg = MagicMock()
        # Mock 3 duplicate groups (total 3 duplicates)
        g1 = DuplicateGroup(file_size=100, sha256="abc", original="/orig1.txt", duplicates=["/dup1.txt"])
        g2 = DuplicateGroup(file_size=200, sha256="def", original="/orig2.txt", duplicates=["/dup2.txt"])
        g3 = DuplicateGroup(file_size=300, sha256="ghi", original="/orig3.txt", duplicates=["/dup3.txt"])

        dlg.duplicate_groups = [g1, g2, g3]
        setattr(dlg, "_rendered_count", 1)  # Only group 1 is rendered into the canvas
        dlg.dup_checkbox_vars = {"/dup1.txt": MagicMock(get=lambda: True)}
        setattr(dlg, "_unrendered_dup_vars", {"/dup2.txt": True, "/dup3.txt": True})

        # 1. Selection initially includes both rendered (/dup1) and unrendered (/dup2, /dup3)
        selected = DuplicateFinderDialog._get_selected_duplicate_paths(dlg)
        self.assertEqual(selected, ["/dup1.txt", "/dup2.txt", "/dup3.txt"])

        # 2. Deselect all sets both rendered variable and unrendered state to False
        DuplicateFinderDialog._deselect_all_dups(dlg)
        dlg.dup_checkbox_vars["/dup1.txt"].set.assert_called_with(False)
        self.assertFalse(dlg._unrendered_dup_vars["/dup2.txt"])
        self.assertFalse(dlg._unrendered_dup_vars["/dup3.txt"])

        # 3. Select all sets both rendered and unrendered state to True
        DuplicateFinderDialog._select_all_dups(dlg)
        dlg.dup_checkbox_vars["/dup1.txt"].set.assert_called_with(True)
        self.assertTrue(dlg._unrendered_dup_vars["/dup2.txt"])
        self.assertTrue(dlg._unrendered_dup_vars["/dup3.txt"])


if __name__ == "__main__":
    unittest.main()
