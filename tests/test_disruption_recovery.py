"""
Unit tests for Disruption Recovery & Task Progress Ledger (PRINCIPLE-012, PRINCIPLE-013).
Validates atomic ledger writing, crash self-healing against corrupt JSON,
checkpoint tracking, and pre-flight disruption audit behavior.
Zero GUI dependencies (runs 100% headless in milliseconds).
"""

import os
import json
import tempfile
import unittest
from pathlib import Path

from scripts.disruption_recovery import (
    get_ledger_path,
    atomic_write_json,
    load_ledger,
    save_ledger,
    record_checkpoint,
    mark_task_completed,
    run_disruption_audit,
    format_audit_report,
)


class TestDisruptionRecovery(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        self.agents_dir = self.root / ".agents"
        self.ledger_file = self.agents_dir / "task_ledger.json"

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_ledger_initialization_on_missing_file(self):
        """Loading a non-existent ledger must return default empty structure."""
        ledger = load_ledger(self.ledger_file)
        self.assertEqual(ledger["version"], 1)
        self.assertIsNone(ledger["active_task"])
        self.assertEqual(ledger["checkpoints"], [])

    def test_atomic_write_and_reload(self):
        """Atomic write must safely persist valid JSON to disk."""
        data = {"version": 1, "active_task": {"task_id": "test_1", "status": "in_progress"}, "checkpoints": []}
        atomic_write_json(self.ledger_file, data)
        self.assertTrue(self.ledger_file.exists())

        loaded = load_ledger(self.ledger_file)
        self.assertEqual(loaded["active_task"]["task_id"], "test_1")

    def test_self_healing_quarantines_corrupt_json(self):
        """A half-written / corrupt JSON file from an electricity cut must be quarantined without crashing."""
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        with open(self.ledger_file, "w", encoding="utf-8") as f:
            f.write('{"version": 1, "active_task": {"task_id": "cut_mid_write"')  # Truncated JSON

        # Loading must not crash and must restore safe defaults
        ledger = load_ledger(self.ledger_file)
        self.assertEqual(ledger["version"], 1)
        self.assertIsNone(ledger["active_task"])

        # Corrupted artifact must have been quarantined with a .corrupt_ timestamp suffix
        corrupt_files = list(self.agents_dir.glob("task_ledger.json.corrupt_*"))
        self.assertGreaterEqual(len(corrupt_files), 1)

    def test_record_checkpoint_and_complete(self):
        """Recording checkpoints must track in-flight progress and final completion."""
        # Step 1: Record in-progress subtask
        record_checkpoint(
            task_id="feat_xyz",
            phase="service_layer",
            description="Implemented core service logic",
            files_affected=["services/new_service.py"],
            ledger_file=self.ledger_file,
        )

        ledger = load_ledger(self.ledger_file)
        self.assertEqual(ledger["active_task"]["task_id"], "feat_xyz")
        self.assertEqual(ledger["active_task"]["last_phase"], "service_layer")
        self.assertEqual(ledger["active_task"]["status"], "in_progress")
        self.assertEqual(len(ledger["checkpoints"]), 1)
        self.assertEqual(ledger["checkpoints"][0]["files_affected"], ["services/new_service.py"])

        # Step 2: Mark task completed
        mark_task_completed("feat_xyz", ledger_file=self.ledger_file)
        ledger_done = load_ledger(self.ledger_file)
        self.assertEqual(ledger_done["active_task"]["status"], "completed")
        self.assertEqual(len(ledger_done["checkpoints"]), 2)
        self.assertEqual(ledger_done["checkpoints"][1]["phase"], "completed")

    def test_run_disruption_audit(self):
        """Disruption audit must detect uncommitted files and interrupted ledger status."""
        record_checkpoint(
            task_id="interrupted_task_99",
            phase="ui_wiring",
            description="Wired UI buttons before power outage",
            status="in_progress",
            ledger_file=self.ledger_file,
        )

        audit = run_disruption_audit(workspace_dir=self.root)
        self.assertFalse(audit["clean_shutdown"])
        self.assertIsNotNone(audit["interrupted_task"])
        self.assertEqual(audit["interrupted_task"]["task_id"], "interrupted_task_99")

        report = format_audit_report(audit)
        self.assertIn("DISRUPTION & PROGRESS RECOVERY AUDIT", report)
        self.assertIn("interrupted_task_99", report)
        self.assertIn("ui_wiring", report)


if __name__ == "__main__":
    unittest.main()
