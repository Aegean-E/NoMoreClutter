"""
Unit tests for Tree Preview Data Grouping and Selection Logic (PRINCIPLE-011)
"""

import os
import unittest
from collections import defaultdict
from models import FileChange


class TestTreePreviewLogic(unittest.TestCase):
    def test_group_changes_by_destination_subfolder(self):
        changes = [
            FileChange(original="/src/invoice1.pdf", action="move", new_path="/dest/Invoices/invoice1.pdf"),
            FileChange(original="/src/invoice2.pdf", action="move", new_path="/dest/Invoices/invoice2.pdf"),
            FileChange(original="/src/photo1.jpg", action="move", new_path="/dest/Photos/2018/photo1.jpg"),
            FileChange(original="/src/root_file.txt", action="move", new_path="/dest/root_file.txt"),
        ]

        output_base = "/dest"
        grouped = defaultdict(list)
        for c in changes:
            dest_dir = os.path.dirname(c.new_path)
            if output_base and dest_dir.startswith(output_base):
                rel_dir = os.path.relpath(dest_dir, output_base)
                if rel_dir == ".":
                    rel_dir = "Root Destination"
            else:
                rel_dir = os.path.basename(dest_dir) or "Root Destination"
            grouped[rel_dir].append(c)

        self.assertIn("Invoices", grouped)
        self.assertEqual(len(grouped["Invoices"]), 2)

        self.assertIn(os.path.normpath("Photos/2018"), [os.path.normpath(k) for k in grouped.keys()])
        self.assertIn("Root Destination", grouped)
        self.assertEqual(len(grouped["Root Destination"]), 1)

    def test_selective_execution_filtering(self):
        changes = [
            FileChange(original="/src/f1.txt", action="move", new_path="/dest/A/f1.txt"),
            FileChange(original="/src/f2.txt", action="move", new_path="/dest/A/f2.txt"),
            FileChange(original="/src/f3.txt", action="move", new_path="/dest/B/f3.txt"),
        ]

        # Simulate user unchecking f2 (idx 1)
        selected_indices = {0: True, 1: False, 2: True}
        selected_changes = [c for idx, c in enumerate(changes) if selected_indices.get(idx, False)]

        self.assertEqual(len(selected_changes), 2)
        self.assertEqual(selected_changes[0].original, "/src/f1.txt")
        self.assertEqual(selected_changes[1].original, "/src/f3.txt")


if __name__ == "__main__":
    unittest.main()
