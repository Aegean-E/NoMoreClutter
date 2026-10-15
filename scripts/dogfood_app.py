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
        self.temp_dir = tempfile.mkdtemp(prefix="nmc_dogfood_")
        self.log(f"Created sandbox at {self.temp_dir}")
        
        # Create test files
        (Path(self.temp_dir) / "notes.txt").write_text("Meeting notes", encoding="utf-8")
        (Path(self.temp_dir) / "script.py").write_text("print('hello')", encoding="utf-8")
        (Path(self.temp_dir) / "data.csv").write_text("id,val\n1,10", encoding="utf-8")
        
        # Duplicates
        (Path(self.temp_dir) / "photo_a.jpg").write_bytes(b"EXIF_IMAGE_DUPLICATE_PAYLOAD_12345")
        (Path(self.temp_dir) / "photo_b.jpg").write_bytes(b"EXIF_IMAGE_DUPLICATE_PAYLOAD_12345")
        
        # Empty folder and junk
        os.makedirs(os.path.join(self.temp_dir, "empty_dir"), exist_ok=True)
        (Path(self.temp_dir) / "cache.tmp").write_text("temp junk", encoding="utf-8")

    def teardown_sandbox(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                self.log("Cleaned up sandbox.")
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


    def run_all(self) -> bool:
        start_time = time.time()
        self.setup_sandbox()
        all_passed = True
        
        tests = [
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
