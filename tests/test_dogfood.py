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

    def test_full_dogfood_run(self):
        """Verify that full harness execution reports 100% operational success."""
        harness = DogfoodHarness(verbose=False)
        success = harness.run_all()
        self.assertTrue(success)
        self.assertEqual(len(harness.captured_exceptions), 0)


if __name__ == "__main__":
    unittest.main()
