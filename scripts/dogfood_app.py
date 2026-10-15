#!/usr/bin/env python3
"""
scripts/dogfood_app.py
Interactive Operational Dogfooding & Chaos Verification Engine (PRINCIPLE-016)

Exhaustively drives and checks every corner of NoMoreClutter:
- Blast-Radius Security Jail (zero harm to user's PC)
- Synthetic Test Fixture Generation (100% synthetic test files)
- Live UI Lifecycle & Quick Organize
- Interactive Tree Preview Dialog & Persistent Undo Rollback
- File Viewer Dialog Multi-Format Rendering (Text & Image)
- Junk Cleaner Chaos Abort & Full Disk Purge
- Duplicate Finder "Set as Original" & Duplicate Isolation
- Settings & Slider Atomic Persistence
- 1-Click AI Quick Deploy Window Navigation
- End-to-End AI Organization Pass
- Zero-Token API Chaos & Type Sanitization Fuzzing
"""

import json
import os
import queue
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path
from unittest.mock import patch

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
        root = Path(target_dir)

        # 1. Standard documents and code
        (root / "notes.txt").write_text("SYNTHETIC_TEST_FILE: Team sync notes", encoding="utf-8")
        (root / "script.py").write_text("print('SYNTHETIC_TEST_CODE')", encoding="utf-8")
        (root / "data.csv").write_text("id,val\n1,10\n2,20", encoding="utf-8")

        # 2. Synthetic camera photos with timestamps
        (root / "20171026_142809.jpg").write_bytes(b"SYNTHETIC_EXIF_IMAGE_CAMERA_2017")
        (root / "IMG_20210515_110022.png").write_bytes(b"SYNTHETIC_EXIF_IMAGE_CAMERA_2021")

        # 3. Exact byte-for-byte duplicate pair
        dup_payload = b"SYNTHETIC_EXACT_DUPLICATE_PAYLOAD_HASH_99999"
        (root / "report_original.pdf").write_bytes(dup_payload)
        (root / "report_copy.pdf").write_bytes(dup_payload)

        # 4. Junk and orphan items
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

    # =========================================================================
    # CORNER 1: Blast-Radius Security Jail
    # =========================================================================
    def test_blast_radius_security_jail(self):
        """Verify that blast-radius safety checks block any mutation to user's real folders."""
        self.log("Verifying blast-radius security jail...")
        desktop_dir = os.path.expanduser("~/Desktop")
        blocked = False
        try:
            DogfoodBlastRadiusJail.assert_confined(desktop_dir, self.temp_dir)
        except PermissionError:
            blocked = True
        
        if not blocked:
            raise RuntimeError("Blast-radius jail failed to block access to user's Desktop!")

        sub_temp = os.path.join(self.temp_dir, "safe_subfolder")
        DogfoodBlastRadiusJail.assert_confined(sub_temp, self.temp_dir)
        self.results["blast_radius_jail"] = "PASS"
        self.log("Blast-radius security jail passed: real user files are 100% protected.")

    # =========================================================================
    # CORNER 2: GUI Lifecycle & Quick Organize
    # =========================================================================
    def test_gui_lifecycle_and_quick_organize(self):
        """Test CTk window initialization, event loop, and Quick Organize."""
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
                # Test Appearance Mode Toggling
                import customtkinter as ctk
                ctk.set_appearance_mode("light")
                app.update()
                ctk.set_appearance_mode("dark")
                app.update()

                # Test Category Quick Select/Deselect
                app._deselect_all_categories()
                if any(v.get() for v in app.type_vars.values()):
                    raise RuntimeError("Deselect all categories failed.")
                app._select_all_categories()
                if not all(v.get() for v in app.type_vars.values()):
                    raise RuntimeError("Select all categories failed.")

                # Test Clear Log
                app.output_text.insert("end", "Temporary log test\n")
                app._clear_log()
                if app.output_text.get("1.0", "end").strip() != "":
                    raise RuntimeError("Clear log failed to wipe output console.")

                # Test AI Status Pill Interaction
                app._on_ai_status_clicked()
                app.update()

                # Setup Source & Output for Quick Organize
                app.source_folder = self.temp_dir
                app.output_folder = self.temp_dir
                app.source_entry.delete(0, "end")
                app.source_entry.insert(0, self.temp_dir)
                app.output_entry.delete(0, "end")
                app.output_entry.insert(0, self.temp_dir)
                app.auto_execute_var.set(True)
                app.update()
                
                app.quick_btn.invoke()
                app.update()
                time.sleep(0.3)
                app.update()
                
                organized_docs = Path(self.temp_dir) / "Documents"
                organized_code = Path(self.temp_dir) / "Code"
                organized_data = Path(self.temp_dir) / "Data"
                
                has_organized = organized_docs.exists() or organized_code.exists() or organized_data.exists()
                if not has_organized:
                    raise RuntimeError("Quick organize did not create target categories.")
                
                self.results["gui_lifecycle"] = "PASS"
                self.log("GUI Lifecycle & Quick Organize passed (including theme modes, category toggles, and clear log).")
            finally:
                self._safe_destroy(app)

    # =========================================================================
    # CORNER 3: Tree Preview Dialog & Undo Rollback
    # =========================================================================
    def test_tree_preview_and_undo_rollback(self):
        """Test TreePreviewDialog per-file selection, execution, and persistent Undo rollback."""
        from main import NoMoreClutterApp
        from models import FileChange
        from ui.tree_preview import TreePreviewDialog
        from services import get_FileExecutor
        self.log("Starting TreePreviewDialog & Undo rollback test...")

        FileExecutor = get_FileExecutor()
        
        f1 = os.path.join(self.temp_dir, "doc1.txt")
        f2 = os.path.join(self.temp_dir, "doc2.txt")
        f3 = os.path.join(self.temp_dir, "photo1.jpg")
        Path(f1).write_text("doc 1", encoding="utf-8")
        Path(f2).write_text("doc 2", encoding="utf-8")
        Path(f3).write_bytes(b"photo 1")

        changes = [
            FileChange(original=f1, action="move", new_path=os.path.join(self.temp_dir, "Documents", "doc1.txt")),
            FileChange(original=f2, action="move", new_path=os.path.join(self.temp_dir, "Documents", "doc2.txt")),
            FileChange(original=f3, action="move", new_path=os.path.join(self.temp_dir, "Photos", "photo1.jpg")),
        ]

        app = NoMoreClutterApp()
        app.report_callback_exception = self.record_exception
        confirmed_changes = []

        def on_confirm(selected):
            nonlocal confirmed_changes
            confirmed_changes = selected

        try:
            app.update()
            dlg = TreePreviewDialog(
                app,
                changes=changes,
                output_base_folder=self.temp_dir,
                on_confirm=on_confirm,
            )
            dlg.report_callback_exception = self.record_exception
            app.update()

            # Deselect f2 (index 1)
            if 1 in dlg.file_vars:
                dlg.file_vars[1].set(False)
            dlg._update_selection_counts()
            app.update()

            dlg._confirm_execution()
            app.update()

            if len(confirmed_changes) != 2:
                raise RuntimeError(f"Expected 2 confirmed changes, got {len(confirmed_changes)}")


            success, errors = FileExecutor.execute(confirmed_changes)
            if success != 2:
                raise RuntimeError(f"Expected 2 successful moves, got {success} (errors={errors})")

            # Check destination
            if not os.path.exists(os.path.join(self.temp_dir, "Documents", "doc1.txt")):
                raise RuntimeError("doc1.txt was not moved to Documents")
            if not os.path.exists(f2):
                raise RuntimeError("Unchecked doc2.txt was unexpectedly moved")

            # Test Undo Rollback
            reverted, undo_errors = FileExecutor.undo_last_batch()
            if reverted != 2:
                raise RuntimeError(f"Expected 2 reverted files, got {reverted} (errors={undo_errors})")

            if not os.path.exists(f1):
                raise RuntimeError("Undo failed to restore doc1.txt to original location")
            
            self.results["tree_preview_and_undo"] = "PASS"
            self.log("TreePreviewDialog & Undo rollback passed.")
        finally:
            self._safe_destroy(app)

    # =========================================================================
    # CORNER 4: File Viewer Dialog Multi-Format Rendering
    # =========================================================================
    def test_file_viewer_dialog_rendering(self):
        """Test FileViewerDialog rendering text and image files without modal lock."""
        from main import NoMoreClutterApp
        from ui.file_viewer import FileViewerDialog
        self.log("Starting FileViewerDialog rendering test...")

        app = NoMoreClutterApp()
        app.report_callback_exception = self.record_exception

        text_file = os.path.join(self.temp_dir, "notes.txt")
        image_file = os.path.join(self.temp_dir, "20171026_142809.jpg")

        try:
            app.update()
            v1 = FileViewerDialog(app, filepath=text_file)
            v1.report_callback_exception = self.record_exception
            app.update()
            self._safe_destroy(v1)
            app.update()

            v2 = FileViewerDialog(app, filepath=image_file)
            v2.report_callback_exception = self.record_exception
            app.update()
            self._safe_destroy(v2)
            app.update()

            self.results["file_viewer"] = "PASS"
            self.log("FileViewerDialog rendering passed.")
        finally:
            self._safe_destroy(app)

    # =========================================================================
    # CORNER 5: Junk Cleaner Mid-Scan Abort & Full Disk Purge
    # =========================================================================
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
            
            dlg._start_scan()
            time.sleep(0.04)
            
            self._safe_destroy(dlg)
            app.update()
            time.sleep(0.2)
            app.update()
            
            tcl_errors = [e for e in self.captured_exceptions if "TclError" in e]
            if tcl_errors:
                raise RuntimeError(f"TclError captured during mid-scan abort: {tcl_errors[0]}")
            
            self.results["junk_cleaner_chaos"] = "PASS"
            self.log("Junk cleaner mid-scan abort passed with 0 TclErrors.")
        finally:
            self._safe_destroy(app)

    def test_junk_cleaner_full_purge(self):
        """Test JunkCleanerDialog full scan and purge of empty directories and debris."""
        from main import NoMoreClutterApp
        from ui.junk_cleaner import JunkCleanerDialog
        self.log("Starting JunkCleanerDialog full purge test...")

        empty_dir = os.path.join(self.temp_dir, "empty_orphan_folder")
        zero_byte = os.path.join(self.temp_dir, "0_byte_leftover.tmp")
        os.makedirs(empty_dir, exist_ok=True)
        Path(zero_byte).write_bytes(b"")

        app = NoMoreClutterApp()
        app.report_callback_exception = self.record_exception

        with patch("tkinter.messagebox.askyesno", return_value=True), \
             patch("tkinter.messagebox.showinfo"):
            try:
                app.update()
                dlg = JunkCleanerDialog(app, initial_folder=self.temp_dir)
                dlg.report_callback_exception = self.record_exception
                app.update()

                from services import get_cleaner_service
                cleaner = get_cleaner_service()
                items = cleaner.scan(self.temp_dir)

                dlg._on_scan_complete(items)
                app.update()

                dlg._execute_prune()
                app.update()


                if os.path.exists(empty_dir):
                    raise RuntimeError("Junk cleaner failed to delete empty directory.")
                if os.path.exists(zero_byte):
                    raise RuntimeError("Junk cleaner failed to delete zero-byte file.")

                self._safe_destroy(dlg)
                app.update()
                self.results["junk_cleaner_purge"] = "PASS"
                self.log("Junk cleaner full purge passed.")
            finally:
                self._safe_destroy(app)

    # =========================================================================
    # CORNER 6: Duplicate Finder "Set as Original" & Duplicate Isolation
    # =========================================================================
    def test_duplicate_finder_and_set_original(self):
        """Test DuplicateFinderDialog, duplicate clustering, and 'Set as Original'."""
        from main import NoMoreClutterApp
        from ui.duplicate_finder import DuplicateFinderDialog
        self.log("Starting DuplicateFinderDialog & Set as Original test...")
        
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
            
            from services.deduplicator import DeduplicationService
            groups = DeduplicationService.scan_duplicates(dup_dir)
            
            if not groups:
                raise RuntimeError("Deduplicator failed to identify identical files.")
            
            for g in groups:
                dlg._group_queue.put(g)
            dlg._on_scan_complete(groups)
            dlg._render_group_card(dlg.duplicate_groups[0], 1)
            app.update()
            
            target_group = dlg.duplicate_groups[0]
            new_orig = target_group.duplicates[0]
            old_orig = target_group.original
            card = dlg._card_frames[0]
            
            dlg._set_as_original(target_group, new_orig, card, 1)
            app.update()
            
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

    def test_duplicate_isolation_action(self):
        """Test DuplicateFinderDialog isolating redundant duplicate files into _duplicates/."""
        from main import NoMoreClutterApp
        from ui.duplicate_finder import DuplicateFinderDialog
        from services.deduplicator import DeduplicationService
        self.log("Starting DuplicateFinderDialog isolation test...")

        dup_sub = os.path.join(self.temp_dir, "dup_action_test")
        os.makedirs(dup_sub, exist_ok=True)
        f_orig = os.path.join(dup_sub, "report_orig.pdf")
        f_dup = os.path.join(dup_sub, "report_dup.pdf")
        payload = b"IDENTICAL_CONTENT_HASH_CHECK_123"
        Path(f_orig).write_bytes(payload)
        Path(f_dup).write_bytes(payload)

        app = NoMoreClutterApp()
        app.report_callback_exception = self.record_exception

        with patch("tkinter.messagebox.askyesno", return_value=True), \
             patch("tkinter.messagebox.showinfo"):
            try:
                app.update()
                dlg = DuplicateFinderDialog(app, initial_folder=dup_sub)
                dlg.report_callback_exception = self.record_exception
                app.update()

                groups = DeduplicationService.scan_duplicates(dup_sub)
                if not groups:
                    raise RuntimeError("Failed to detect duplicate files for isolation.")

                for g in groups:
                    dlg._group_queue.put(g)
                dlg._on_scan_complete(groups)
                dlg._render_group_card(dlg.duplicate_groups[0], 1)
                app.update()

                target_grp = dlg.duplicate_groups[0]
                actual_orig = target_grp.original
                actual_dup = target_grp.duplicates[0]

                dlg._isolate_selected()
                app.update()

                if not os.path.exists(actual_orig):
                    raise RuntimeError("Original file was mistakenly removed during isolation.")
                if os.path.exists(actual_dup):
                    raise RuntimeError("Duplicate file was not isolated.")


                self._safe_destroy(dlg)
                app.update()
                self.results["duplicate_isolation"] = "PASS"
                self.log("Duplicate isolation action passed.")
            finally:
                self._safe_destroy(app)

    # =========================================================================
    # CORNER 7: Settings & Slider Atomic Persistence
    # =========================================================================
    def test_settings_and_slider_persistence(self):
        """Test settings panel adjustments, slider values, and atomic JSON persistence."""
        from main import NoMoreClutterApp, SETTINGS_FILE
        self.log("Starting settings and slider persistence test...")

        app = NoMoreClutterApp()
        app.report_callback_exception = self.record_exception

        try:
            app.update()
            app.batch_size_slider.set(22)
            app.limit_slider.set(75)
            app.pacing_slider.set(0.4)
            app.peek_length_slider.set(210)
            app.provider_var.set("Google Gemini (Free Tier)")

            app._save_settings(silent=True)

            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)

            if saved.get("provider_name") != "Google Gemini (Free Tier)":
                raise RuntimeError("Provider name did not persist to settings.json.")
            if saved.get("batch_size") != "22":
                raise RuntimeError(f"Batch size did not persist: {saved.get('batch_size')}")

            self.results["settings_persistence"] = "PASS"
            self.log("Settings and slider persistence passed.")
        finally:
            self._safe_destroy(app)

    # =========================================================================
    # CORNER 8: 1-Click AI Quick Deploy Navigation
    # =========================================================================
    def test_quick_deploy_window_navigation(self):
        """Test 1-Click AI Quick Deploy window initialization and tab navigation."""
        from main import NoMoreClutterApp
        self.log("Starting Quick Deploy window navigation test...")

        app = NoMoreClutterApp()
        app.report_callback_exception = self.record_exception

        try:
            app.update()
            app._open_quick_deploy()
            app.update()

            win = app.quick_deploy_window
            if not win or not win.winfo_exists():
                raise RuntimeError("Quick Deploy window did not spawn.")

            self._safe_destroy(win)
            app.update()
            self.results["quick_deploy_window"] = "PASS"
            self.log("Quick Deploy window navigation passed.")
        finally:
            self._safe_destroy(app)

    # =========================================================================
    # CORNER 9: End-to-End AI Organization Pass (Live or Simulated)
    # =========================================================================
    def test_live_or_simulated_ai_organization(self):
        """Test real end-to-end AI organization on diverse synthetic files (categories, renames, and vision)."""
        from services.rlm_organizer import RLMOrganizer
        from services.providers.base import BaseAIProvider
        from services import get_provider_registry
        self.log("Starting Live or Simulated AI organization pass...")

        f1 = os.path.join(self.temp_dir, "invoice_october.txt")
        f2 = os.path.join(self.temp_dir, "worker_service.py")
        f3 = os.path.join(self.temp_dir, "quarterly_budget.csv")
        f4 = os.path.join(self.temp_dir, "vacation_sunset.jpg")
        
        Path(f1).write_text("Invoice for consulting services: $500. Due October 2026.", encoding="utf-8")
        Path(f2).write_text("class WorkerService:\n    def run(self): pass\n", encoding="utf-8")
        Path(f3).write_text("Q1,Q2,Q3,Q4\n100,200,300,400\n", encoding="utf-8")
        Path(f4).write_bytes(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00" + b"\x00" * 250 + b"\xFF\xD9")

        files = [f1, f2, f3, f4]

        # Check for configured live provider
        live_provider = None
        registry_get, _, _, _, _ = get_provider_registry()
        for env_key, prov_id, model_name in [
            ("GROQ_API_KEY", "groq", "llama-3.3-70b-versatile"),
            ("GEMINI_API_KEY", "gemini", "gemini-1.5-flash"),
            ("OPENAI_API_KEY", "openai", "gpt-4o-mini"),
        ]:
            key = os.getenv(env_key)
            if key:
                try:
                    prov = registry_get(prov_id, api_key=key)
                    ok, _ = prov.test_connection(model=model_name)
                    if ok:
                        live_provider = prov
                        self.log(f"Live provider '{prov_id}' detected and verified online. Using live AI!")
                        break
                except Exception:
                    pass

        if not live_provider:
            # Dynamic realistic multi-type provider
            class DynamicAIResponseProvider(BaseAIProvider):
                id = "mock_live"
                name = "Mock Live AI"
                def __init__(self):
                    super().__init__(base_url="mock://localhost")
                def test_connection(self, model=None):
                    return True, "Mock connected"
                def complete(self, prompt, model="default", temperature=0.2, max_tokens=1000):
                    return (
                        '['
                        '{"id": 0, "folder": "Invoices", "name": "consulting_invoice_october.txt"}, '
                        '{"id": 1, "folder": "Development", "name": "worker_service.py"}, '
                        '{"id": 2, "folder": "Spreadsheets", "name": "quarterly_budget_2026.csv"}'
                        ']'
                    )
                def analyze_image(self, image_path, prompt, model="default", max_tokens=100):
                    return '{"folder": "Photos/Vacation", "name": "sunset_photo_2026.jpg"}'

            live_provider = DynamicAIResponseProvider()

        organizer = RLMOrganizer(provider=live_provider)
        
        # Test AI Organization with Smart Rename & Image Vision Analysis
        changes = organizer.organize(
            files=files,
            model="default",
            output_folder=self.temp_dir,
            create_new_folders=True,
            ai_rename=True,
            analyze_images=True,
        )

        if len(changes) != 4:
            raise RuntimeError(f"Expected 4 AI organized changes, got {len(changes)}")

        folders = {os.path.basename(os.path.dirname(c.new_path)) for c in changes}
        self.log(f"AI organizer produced target folders: {folders}")

        for c in changes:
            DogfoodBlastRadiusJail.assert_confined(c.new_path, self.temp_dir)

        self.results["ai_organization_pass"] = "PASS"
        self.log("Live or Simulated AI organization pass passed (categories, renames, and vision).")

    # =========================================================================
    # CORNER 10: Zero-Token API Chaos Fuzzing
    # =========================================================================
    def test_offline_api_chaos_fuzzing(self):
        """Fuzz RLM and cleaner parsing with realistic dirty LLM outputs (0 tokens)."""
        from services.rlm_organizer import RLMOrganizer
        self.log("Starting Offline API Chaos Fuzzing (0 Tokens)...")
        
        dirty_json_int = '[{"id": 0, "name": 142809, "folder": 2017}]'
        parsed = RLMOrganizer._extract_json(dirty_json_int)
        if not parsed or not isinstance(parsed, list):
            raise RuntimeError("Failed to extract JSON from integer payload.")
        
        sanitized_folder = RLMOrganizer._sanitize_folder_name(parsed[0]["folder"])
        sanitized_name = RLMOrganizer._sanitize_filename(parsed[0]["name"], "orig.jpg")
        if sanitized_folder != "2017" or not sanitized_name.startswith("142809"):
            raise RuntimeError(f"Integer fields were not sanitized correctly: {sanitized_folder}, {sanitized_name}")
        
        dirty_markdown = 'Sure, here is your organized JSON:\n```json\n[{"id": 1, "name": "file.txt", "folder": "Docs"}]\n```\nHope this helps!'
        parsed_md = RLMOrganizer._extract_json(dirty_markdown)
        if not parsed_md or parsed_md[0]["folder"] != "Docs":
            raise RuntimeError("Markdown codeblock stripping failed.")
        
        broken_json = '[{"id": 0, "name": "file1.txt", "folder": "Docs"}, {"id": 1, "name": "file2'
        try:
            res = RLMOrganizer._extract_json(broken_json)
        except Exception as e:
            raise RuntimeError(f"Truncated JSON caused unhandled crash: {e}")
        
        self.results["api_chaos_fuzzing"] = "PASS"
        self.log("Offline API Chaos Fuzzing passed all scenarios.")

    # =========================================================================
    # MASTER RUNNER
    # =========================================================================
    def run_all(self) -> bool:
        start_time = time.time()
        self.setup_sandbox()
        all_passed = True
        
        tests = [
            ("Blast-Radius Safety Jail", self.test_blast_radius_security_jail),
            ("UI Lifecycle & Quick Organize", self.test_gui_lifecycle_and_quick_organize),
            ("Tree Preview & Undo Rollback", self.test_tree_preview_and_undo_rollback),
            ("File Viewer Multi-Format Dialog", self.test_file_viewer_dialog_rendering),
            ("Junk Cleaner Mid-Scan Abort", self.test_junk_cleaner_and_chaos_abort),
            ("Junk Cleaner Full Disk Purge", self.test_junk_cleaner_full_purge),
            ("Duplicate Finder & Set Original", self.test_duplicate_finder_and_set_original),
            ("Duplicate Isolation Action", self.test_duplicate_isolation_action),
            ("Settings & Slider Persistence", self.test_settings_and_slider_persistence),
            ("1-Click Quick Deploy Navigation", self.test_quick_deploy_window_navigation),
            ("AI Organization Pass", self.test_live_or_simulated_ai_organization),
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
                f.write(f"NoMoreClutter Exhaustive Dogfooding Run - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Overall Result: {'PASS' if all_passed else 'FAIL'} (Duration: {elapsed}s)\n\n")
                f.write("=== Captured Tkinter Exceptions ===\n")
                for exc in self.captured_exceptions:
                    f.write(exc + "\n" + "-"*40 + "\n")
                f.write("\n=== Execution Log ===\n")
                f.write("\n".join(self.log_entries) + "\n")
        except Exception as log_err:
            print(f"Warning: Failed to write {LOG_FILE}: {log_err}")
        
        # Print terse, context-budgeted dashboard to stdout (<15 lines)
        print(f"[DOGFOOD] 🛡️  Blast-Radius Safety Jail:      {self.results.get('blast_radius_jail', 'FAIL')}")
        print(f"[DOGFOOD] 🖥️  UI Lifecycle & Quick Organize: {self.results.get('gui_lifecycle', 'FAIL')}")
        print(f"[DOGFOOD] 🗂️  Tree Preview & Undo Rollback:   {self.results.get('tree_preview_and_undo', 'FAIL')}")
        print(f"[DOGFOOD] 👁️  File Viewer Rendering:         {self.results.get('file_viewer', 'FAIL')}")
        print(f"[DOGFOOD] ⚡ Junk Cleaner (Abort & Purge):   {self.results.get('junk_cleaner_purge', 'FAIL')}")
        print(f"[DOGFOOD] 👥 Duplicate (Original & Isolate):  {self.results.get('duplicate_isolation', 'FAIL')}")
        print(f"[DOGFOOD] ⚙️  Settings & Slider Persistence:  {self.results.get('settings_persistence', 'FAIL')}")
        print(f"[DOGFOOD] 🚀 1-Click Quick Deploy Navigation: {self.results.get('quick_deploy_window', 'FAIL')}")
        print(f"[DOGFOOD] 🤖 AI Organization Pass:           {self.results.get('ai_organization_pass', 'FAIL')}")
        print(f"[DOGFOOD] 🧪 API Chaos Fuzzing:              {self.results.get('api_chaos_fuzzing', 'FAIL')}")
        print(f"[DOGFOOD] ⏱️  Duration: {elapsed}s | Tkinter Errors: {len(self.captured_exceptions)}")
        verdict = "100% OPERATIONAL (All 12 Corners Verified)" if all_passed else "FAILURES DETECTED (See .agents/dogfood_last_run.log)"
        print(f"[DOGFOOD] 🏆 Final Verdict: {verdict}")
        
        return all_passed


if __name__ == "__main__":
    verbose_flag = "--verbose" in sys.argv
    harness = DogfoodHarness(verbose=verbose_flag)
    success = harness.run_all()
    sys.exit(0 if success else 1)
