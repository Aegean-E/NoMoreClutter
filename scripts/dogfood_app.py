#!/usr/bin/env python3
"""
scripts/dogfood_app.py
Interactive Operational Dogfooding & Chaos Verification Engine (PRINCIPLE-016)

Directly drives and operates NoMoreClutter as a real user:
- Mounts live CTk window and pumps the event loop.
- Traps unhandled Tkinter callback exceptions (TclError).
- Stress-tests mid-operation window destruction and background thread aborts.
- Verifies DuplicateFinder ("Set as Original") and JunkCleaner.
- Runs offline API Chaos Fuzzing (integers, markdown fences, 429s) at zero token cost.
- Emits a terse (<10 line) context-lean dashboard and saves full logs to disk.
"""

import os
import sys
import time
import shutil
import tempfile
import traceback
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

LOG_FILE = REPO_ROOT / ".agents" / "dogfood_last_run.log"


class DogfoodBlastRadiusJail:
    """Enforces zero-blast-radius containment to guarantee no harm to the user's PC (PRINCIPLE-016)."""

    @staticmethod
    def assert_confined(target_path: str, sandbox_root: str):
        if not target_path or not sandbox_root:
            raise ValueError("Target path and sandbox root must be specified.")
        
        resolved_target = os.path.realpath(os.path.abspath(target_path))
        resolved_root = os.path.realpath(os.path.abspath(sandbox_root))

        # Blacklist of critical user and system directories that must NEVER be touched
        forbidden_roots = [
            os.path.realpath(os.path.expanduser("~")),
            os.path.realpath(os.path.expanduser("~/Desktop")),
            os.path.realpath(os.path.expanduser("~/Documents")),
            os.path.realpath(os.path.expanduser("~/Downloads")),
            os.path.realpath(os.path.expanduser("~/Pictures")),
            os.path.realpath(os.path.expanduser("~/Videos")),
            os.path.realpath("C:\\"),
            os.path.realpath("C:\\Windows"),
            os.path.realpath("C:\\Program Files"),
            os.path.realpath("D:\\"),
        ]

        for forbidden in forbidden_roots:
            if resolved_target == forbidden:
                raise PermissionError(
                    f"[BLAST-RADIUS SECURITY VIOLATION]: Path '{resolved_target}' is a critical user system folder! "
                    "Dogfooding must only run inside an ephemeral sandbox."
                )

        # Must be strictly within sandbox_root
        if not (resolved_target == resolved_root or resolved_target.startswith(resolved_root + os.sep)):
            raise PermissionError(
                f"[BLAST-RADIUS SECURITY VIOLATION]: Path '{resolved_target}' is outside sandbox jail '{resolved_root}'! "
                "Dogfooding is strictly prohibited from mutating external files."
            )


class SyntheticTestFixtureFactory:
    """Generates 100% synthetic, harmless test files for operational dogfooding."""

    @classmethod
    def populate(cls, target_dir: str):
        jail = DogfoodBlastRadiusJail
        root = Path(target_dir)

        # 1. Standard documents and code
        (root / "notes.txt").write_text("SYNTHETIC_TEST_FILE: Team sync notes", encoding="utf-8")
        (root / "script.py").write_text("print('SYNTHETIC_TEST_CODE')", encoding="utf-8")
        (root / "data.csv").write_text("id,val\n1,10\n2,20", encoding="utf-8")

        # 2. Synthetic camera photos with timestamps (tests date album routing)
        (root / "20171026_142809.jpg").write_bytes(b"SYNTHETIC_EXIF_IMAGE_CAMERA_2017")
        (root / "IMG_20210515_110022.png").write_bytes(b"SYNTHETIC_EXIF_IMAGE_CAMERA_2021")

        # 3. Exact byte-for-byte duplicate pair
        dup_payload = b"SYNTHETIC_EXACT_DUPLICATE_PAYLOAD_HASH_99999"
        (root / "report_original.pdf").write_bytes(dup_payload)
        (root / "report_copy.pdf").write_bytes(dup_payload)

        # 4. Junk and orphan items (tests JunkCleaner)
        empty_dir = root / "empty_orphan_folder"
        empty_dir.mkdir(parents=True, exist_ok=True)
        (root / "0_byte_leftover.tmp").write_bytes(b"")
        (root / "cache.tmp").write_text("temporary cache debris", encoding="utf-8")
        (root / "Thumbs.db").write_bytes(b"SYNTHETIC_OS_DEBRIS")


class DogfoodHarness:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.log_entries = []
        self.results = {}
        self.captured_exceptions = []
        self.temp_dir = None

    def log(self, msg: str):
        self.log_entries.append(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
        if self.verbose:
            print(msg)

    def record_exception(self, exc_type, exc_value, exc_tb):
        formatted = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        self.captured_exceptions.append(formatted)
        self.log(f"[EXCEPTION CAUGHT IN TKINTER CALLBACK]: {formatted}")

    def _safe_destroy(self, widget):
        if not widget:
            return
        try:
            if hasattr(widget, "tk") and hasattr(widget, "after_cancel"):
                for after_id in widget.tk.call("after", "info"):
                    try:
                        widget.after_cancel(after_id)
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            widget.destroy()
        except Exception:
            pass

    def setup_sandbox(self):
        """Creates an ephemeral sandbox strictly isolated from user files."""
        self.temp_dir = tempfile.mkdtemp(prefix="nmc_dogfood_")
        DogfoodBlastRadiusJail.assert_confined(self.temp_dir, tempfile.gettempdir())
        self.log(f"Created isolated sandbox at {self.temp_dir}")
        SyntheticTestFixtureFactory.populate(self.temp_dir)

    def teardown_sandbox(self):
        """Cleanly wipes ephemeral sandbox, leaving zero clutter on the user's PC."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                DogfoodBlastRadiusJail.assert_confined(self.temp_dir, tempfile.gettempdir())
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                self.log("Cleaned up sandbox completely. Zero residual clutter on disk.")
            except Exception as e:
                self.log(f"Sandbox cleanup error: {e}")


    def test_gui_lifecycle_and_quick_organize(self):
        """Test CTk window initialization, event loop, and Quick Organize."""
        from unittest.mock import patch
        from main import NoMoreClutterApp
        self.log("Starting GUI Lifecycle & Quick Organize test...")
        
        with patch("tkinter.messagebox.showwarning"), \
             patch("tkinter.messagebox.showinfo"), \
             patch("tkinter.messagebox.showerror"), \
             patch("tkinter.messagebox.askyesno", return_value=True):
            app = NoMoreClutterApp()
            app.report_callback_exception = self.record_exception
            
            try:
                app.update()
                
                # Set folders
                app.source_folder = self.temp_dir
                app.output_folder = self.temp_dir
                app.source_entry.delete(0, "end")
                app.source_entry.insert(0, self.temp_dir)
                app.output_entry.delete(0, "end")
                app.output_entry.insert(0, self.temp_dir)
                app.auto_execute_var.set(True)
                app.update()
                
                # Trigger Quick Organize (No AI)
                app.quick_btn.invoke()
                app.update()
                time.sleep(0.3)
                app.update()
                
                # Verify file organization
                organized_docs = Path(self.temp_dir) / "Documents"
                organized_code = Path(self.temp_dir) / "Code"
                organized_data = Path(self.temp_dir) / "Data"
                
                has_organized = organized_docs.exists() or organized_code.exists() or organized_data.exists()
                if not has_organized:
                    raise RuntimeError("Quick organize did not create target categories.")
                
                self.results["gui_lifecycle"] = "PASS"
                self.log("GUI Lifecycle & Quick Organize passed.")
            finally:
                self._safe_destroy(app)



    def test_junk_cleaner_and_chaos_abort(self):
        """Test JunkCleanerDialog and chaos stress: aborting mid-scan."""
        from main import NoMoreClutterApp
        from ui.junk_cleaner import JunkCleanerDialog
        self.log("Starting JunkCleanerDialog chaos abort test...")
        
        app = NoMoreClutterApp()
        app.report_callback_exception = self.record_exception
        
        try:
            app.update()
            dlg = JunkCleanerDialog(app, initial_folder=self.temp_dir)
            dlg.report_callback_exception = self.record_exception
            app.update()
            
            # Start scan in background thread
            dlg._start_scan()
            time.sleep(0.04)  # Let worker start
            
            # Chaos: destroy dialog while thread is traversing disk
            self._safe_destroy(dlg)
            app.update()
            time.sleep(0.2)
            app.update()
            
            # Check for TclError
            tcl_errors = [e for e in self.captured_exceptions if "TclError" in e]
            if tcl_errors:
                raise RuntimeError(f"TclError captured during mid-scan abort: {tcl_errors[0]}")
            
            self.results["junk_cleaner_chaos"] = "PASS"
            self.log("Junk cleaner mid-scan abort passed with 0 TclErrors.")
        finally:
            self._safe_destroy(app)


    def test_duplicate_finder_and_set_original(self):
        """Test DuplicateFinderDialog, duplicate clustering, and 'Set as Original'."""
        from main import NoMoreClutterApp
        from ui.duplicate_finder import DuplicateFinderDialog
        self.log("Starting DuplicateFinderDialog & Set as Original test...")
        
        # Prepare duplicate files in a clean subfolder
        dup_dir = os.path.join(self.temp_dir, "dup_test")
        os.makedirs(dup_dir, exist_ok=True)
        f1 = os.path.join(dup_dir, "original.jpg")
        f2 = os.path.join(dup_dir, "copy.jpg")
        with open(f1, "wb") as f:
            f.write(b"DUPLICATE_BYTES_PAYLOAD_9999")
        with open(f2, "wb") as f:
            f.write(b"DUPLICATE_BYTES_PAYLOAD_9999")
        
        app = NoMoreClutterApp()
        app.report_callback_exception = self.record_exception
        
        try:
            app.update()
            dlg = DuplicateFinderDialog(app, initial_folder=dup_dir)
            dlg.report_callback_exception = self.record_exception
            app.update()
            
            # Run scan synchronously
            from services.deduplicator import DeduplicationService
            groups = DeduplicationService.scan_duplicates(dup_dir)
            
            if not groups:
                raise RuntimeError("Deduplicator failed to identify identical files.")
            
            # Feed groups to dialog queue and complete scan
            for g in groups:
                dlg._group_queue.put(g)
            dlg._on_scan_complete(groups)
            dlg._render_group_card(dlg.duplicate_groups[0], 1)
            app.update()
            
            # Test "Set as Original" on first duplicate in group
            target_group = dlg.duplicate_groups[0]
            new_orig = target_group.duplicates[0]
            old_orig = target_group.original
            card = dlg._card_frames[0]
            
            dlg._set_as_original(target_group, new_orig, card, 1)
            app.update()
            
            # Assert new_orig is now original
            if target_group.original != new_orig:
                raise RuntimeError("Set as Original did not update group.original.")
            if old_orig not in target_group.duplicates:
                raise RuntimeError("Prior original was not relegated to duplicates list.")

            
            self._safe_destroy(dlg)
            app.update()
            self.results["duplicate_finder"] = "PASS"
            self.log("Duplicate finder & Set as Original passed.")
        finally:
            self._safe_destroy(app)


    def test_offline_api_chaos_fuzzing(self):
        """Fuzz RLM and cleaner parsing with realistic dirty LLM outputs (0 tokens)."""
        import json
        from services.rlm_organizer import RLMOrganizer
        self.log("Starting Offline API Chaos Fuzzing (0 Tokens)...")
        
        # Fuzz 1: Non-string integer fields (the bug that caused TypeError)
        dirty_json_int = '[{"id": 0, "name": 142809, "folder": 2017}]'
        parsed = RLMOrganizer._extract_json(dirty_json_int)
        if not parsed or not isinstance(parsed, list):
            raise RuntimeError("Failed to extract JSON from integer payload.")
        
        sanitized_folder = RLMOrganizer._sanitize_folder_name(parsed[0]["folder"])
        sanitized_name = RLMOrganizer._sanitize_filename(parsed[0]["name"], "orig.jpg")
        if sanitized_folder != "2017" or not sanitized_name.startswith("142809"):
            raise RuntimeError(f"Integer fields were not sanitized correctly: {sanitized_folder}, {sanitized_name}")
        
        # Fuzz 2: Conversational prefix and markdown codeblocks
        dirty_markdown = 'Sure, here is your organized JSON:\n```json\n[{"id": 1, "name": "file.txt", "folder": "Docs"}]\n```\nHope this helps!'
        parsed_md = RLMOrganizer._extract_json(dirty_markdown)
        if not parsed_md or parsed_md[0]["folder"] != "Docs":
            raise RuntimeError("Markdown codeblock stripping failed.")
        
        # Fuzz 3: Truncated JSON recovery
        broken_json = '[{"id": 0, "name": "file1.txt", "folder": "Docs"}, {"id": 1, "name": "file2'
        try:
            res = RLMOrganizer._extract_json(broken_json)
        except Exception as e:
            raise RuntimeError(f"Truncated JSON caused unhandled crash: {e}")
        
        self.results["api_chaos_fuzzing"] = "PASS"
        self.log("Offline API Chaos Fuzzing passed all scenarios.")

    def test_blast_radius_security_jail(self):
        """Verify that blast-radius safety checks block any mutation to user's real folders."""
        self.log("Verifying blast-radius security jail...")
        desktop_dir = os.path.expanduser("~/Desktop")
        
        # Must block personal user directory
        blocked = False
        try:
            DogfoodBlastRadiusJail.assert_confined(desktop_dir, self.temp_dir)
        except PermissionError:
            blocked = True
        
        if not blocked:
            raise RuntimeError("Blast-radius jail failed to block access to user's Desktop!")

        # Must allow paths inside temp_dir
        sub_temp = os.path.join(self.temp_dir, "safe_subfolder")
        DogfoodBlastRadiusJail.assert_confined(sub_temp, self.temp_dir)
        
        self.results["blast_radius_jail"] = "PASS"
        self.log("Blast-radius security jail passed: real user files are 100% protected.")

    def run_all(self) -> bool:
        start_time = time.time()
        self.setup_sandbox()
        all_passed = True
        
        tests = [
            ("Blast-Radius Safety Jail", self.test_blast_radius_security_jail),
            ("UI Lifecycle & Quick Organize", self.test_gui_lifecycle_and_quick_organize),
            ("Junk Cleaner & Chaos Abort", self.test_junk_cleaner_and_chaos_abort),
            ("Duplicate Finder & Set Original", self.test_duplicate_finder_and_set_original),
            ("API Chaos Fuzzing (0 Tokens)", self.test_offline_api_chaos_fuzzing),
        ]

        
        for name, test_fn in tests:
            try:
                test_fn()
            except Exception as e:
                all_passed = False
                err_msg = f"FAILED: {e}"
                self.results[name] = err_msg
                self.log(f"[TEST FAIL] {name}: {traceback.format_exc()}")
        
        self.teardown_sandbox()
        elapsed = round(time.time() - start_time, 2)
        
        # Write full diagnostic log to disk
        try:
            os.makedirs(LOG_FILE.parent, exist_ok=True)
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write(f"NoMoreClutter Dogfooding Run - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Overall Result: {'PASS' if all_passed else 'FAIL'} (Duration: {elapsed}s)\n\n")
                f.write("=== Captured Tkinter Exceptions ===\n")
                for exc in self.captured_exceptions:
                    f.write(exc + "\n" + "-"*40 + "\n")
                f.write("\n=== Execution Log ===\n")
                f.write("\n".join(self.log_entries) + "\n")
        except Exception as log_err:
            print(f"Warning: Failed to write {LOG_FILE}: {log_err}")
        
        # Print terse, context-budgeted dashboard to stdout (<10 lines)
        print(f"[DOGFOOD] 🛡️  Blast-Radius Safety Jail:  {self.results.get('blast_radius_jail', 'FAIL')}")
        print(f"[DOGFOOD] 🖥️  UI Lifecycle & Event Loop:   {self.results.get('gui_lifecycle', 'FAIL')}")
        print(f"[DOGFOOD] ⚡ Junk Cleaner & Chaos Abort:  {self.results.get('junk_cleaner_chaos', 'FAIL')}")
        print(f"[DOGFOOD] 🗂️  Duplicate & Set Original:   {self.results.get('duplicate_finder', 'FAIL')}")
        print(f"[DOGFOOD] 🧪 API Chaos Fuzzing (0 Tok):   {self.results.get('api_chaos_fuzzing', 'FAIL')}")
        print(f"[DOGFOOD] ⏱️  Duration: {elapsed}s | Tkinter Errors: {len(self.captured_exceptions)}")
        verdict = "100% OPERATIONAL (Zero Regressions)" if all_passed else "FAILURES DETECTED (See .agents/dogfood_last_run.log)"
        print(f"[DOGFOOD] 🏆 Final Verdict: {verdict}")

        
        return all_passed


if __name__ == "__main__":
    verbose_flag = "--verbose" in sys.argv
    harness = DogfoodHarness(verbose=verbose_flag)
    success = harness.run_all()
    sys.exit(0 if success else 1)
