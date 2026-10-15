"""
Unit and integration tests for the interactive dogfooding harness (PRINCIPLE-016).
Verifies that the dogfood engine executes, captures errors, and cleans up properly.
"""

import unittest
from scripts.dogfood_app import DogfoodHarness


class TestDogfoodHarness(unittest.TestCase):
    def setUp(self):
        self.harness = DogfoodHarness(verbose=False)
        self.harness.setup_sandbox()

    def tearDown(self):
        self.harness.teardown_sandbox()

    def test_offline_api_chaos_fuzzing(self):
        """Verify that offline chaos fuzzing handles dirty LLM outputs cleanly."""
        self.harness.test_offline_api_chaos_fuzzing()
        self.assertEqual(self.harness.results.get("api_chaos_fuzzing"), "PASS")

    def test_junk_cleaner_chaos_abort(self):
        """Verify that JunkCleanerDialog aborts cleanly without unhandled TclError."""
        self.harness.test_junk_cleaner_and_chaos_abort()
        self.assertEqual(self.harness.results.get("junk_cleaner_chaos"), "PASS")
        self.assertEqual(len(self.harness.captured_exceptions), 0)

    def test_gui_lifecycle_and_quick_organize(self):
        """Verify that GUI mounts, sets folders, and organizes files."""
        self.harness.test_gui_lifecycle_and_quick_organize()
        self.assertEqual(self.harness.results.get("gui_lifecycle"), "PASS")

    def test_duplicate_finder_and_set_original(self):
        """Verify that DuplicateFinderDialog handles Set as Original cleanly."""
        self.harness.test_duplicate_finder_and_set_original()
        self.assertEqual(self.harness.results.get("duplicate_finder"), "PASS")

    def test_blast_radius_security_jail(self):
        """Verify that blast-radius jail blocks external user directories."""
        self.harness.test_blast_radius_security_jail()
        self.assertEqual(self.harness.results.get("blast_radius_jail"), "PASS")

    def test_blast_radius_jail_blocks_critical_paths(self):
        """Verify that the jail raises PermissionError when critical paths are targeted."""
        from scripts.dogfood_app import DogfoodBlastRadiusJail
        import os
        
        with self.assertRaises(PermissionError):
            DogfoodBlastRadiusJail.assert_confined(os.path.expanduser("~"), self.harness.temp_dir)
            
        with self.assertRaises(PermissionError):
            DogfoodBlastRadiusJail.assert_confined("C:\\Windows", self.harness.temp_dir)

    def test_synthetic_fixture_factory(self):
        """Verify that synthetic test fixtures are created and 100% synthetic."""
        from pathlib import Path
        root = Path(self.harness.temp_dir)
        self.assertTrue((root / "notes.txt").exists())
        self.assertTrue((root / "20171026_142809.jpg").exists())
        self.assertTrue((root / "report_original.pdf").exists())
        self.assertTrue((root / "report_copy.pdf").exists())
        self.assertTrue((root / "0_byte_leftover.tmp").exists())

    def test_tree_preview_and_undo_rollback(self):
        """Verify that TreePreviewDialog unchecking, execution, and undo work cleanly."""
        self.harness.test_tree_preview_and_undo_rollback()
        self.assertEqual(self.harness.results.get("tree_preview_and_undo"), "PASS")

    def test_file_viewer_dialog_rendering(self):
        """Verify that FileViewerDialog renders images, text, and documents cleanly."""
        self.harness.test_file_viewer_dialog_rendering()
        self.assertEqual(self.harness.results.get("file_viewer"), "PASS")

    def test_junk_cleaner_full_purge(self):
        """Verify that JunkCleanerDialog performs complete purge without crashing."""
        self.harness.test_junk_cleaner_full_purge()
        self.assertEqual(self.harness.results.get("junk_cleaner_purge"), "PASS")

    def test_duplicate_isolation_action(self):
        """Verify that duplicate isolation action moves copies cleanly to target folder."""
        self.harness.test_duplicate_isolation_action()
        self.assertEqual(self.harness.results.get("duplicate_isolation"), "PASS")

    def test_settings_and_slider_persistence(self):
        """Verify that settings sliders persist values atomically to disk with fsync."""
        self.harness.test_settings_and_slider_persistence()
        self.assertEqual(self.harness.results.get("settings_persistence"), "PASS")

    def test_quick_deploy_window_navigation(self):
        """Verify that 1-Click Quick Deploy window mounts cleanly."""
        self.harness.test_quick_deploy_window_navigation()
        self.assertEqual(self.harness.results.get("quick_deploy_window"), "PASS")

    def test_live_or_simulated_ai_organization(self):
        """Verify that AI organization pass completes successfully on synthetic fixtures."""
        self.harness.test_live_or_simulated_ai_organization()
        self.assertEqual(self.harness.results.get("ai_organization_pass"), "PASS")

    def test_full_dogfood_run(self):
        """Verify that full harness execution reports 100% operational success."""
        harness = DogfoodHarness(verbose=False)
        success = harness.run_all()
        self.assertTrue(success)
        self.assertEqual(len(harness.captured_exceptions), 0)


if __name__ == "__main__":
    unittest.main()
