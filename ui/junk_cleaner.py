"""
Orphan Folder & Junk Pruner UI Dialog (Option 4)
Allows users to recursively detect and safely prune empty subdirectories,
zero-byte orphaned files, and OS debris (Thumbs.db, .DS_Store).
"""

import os
import threading
from typing import List, Dict
import customtkinter as ctk
from tkinter import filedialog, messagebox
from models import CleanupItem, CleanupReport
from services.cleaner_service import CleanerService
from services.deduplicator import DeduplicationService


class JunkCleanerDialog(ctk.CTkToplevel):
    """Interactive Orphan Folder & Junk Pruner Dialog."""

    def __init__(self, parent, initial_folder: str = ""):
        super().__init__(parent)
        self.initial_folder = initial_folder or os.getcwd()
        self.cleanup_items: List[CleanupItem] = []
        self.item_vars: Dict[int, ctk.BooleanVar] = {}

        self.title("🧹 Orphan Folder & Junk Pruner (Deep Clean)")
        self.geometry("880x680")
        self.minsize(740, 520)
        self.transient(parent)

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # -------------------------------------------------------------
        # 1. Header & Options Card
        # -------------------------------------------------------------
        top_frame = ctk.CTkFrame(self, fg_color="#1E1E24")
        top_frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top_frame,
            text="🧹 Orphan Folder & Junk Pruner",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#F8F9FA",
        ).grid(row=0, column=0, columnspan=3, padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            top_frame,
            text="Recursively detects and prunes empty directory branches, 0-byte orphan files, and OS debris.",
            font=ctk.CTkFont(size=12),
            text_color="#ADB5BD",
        ).grid(row=1, column=0, columnspan=3, padx=16, pady=(0, 10), sticky="w")

        # Folder selection
        ctk.CTkLabel(top_frame, text="Target Folder:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, padx=(16, 8), pady=8, sticky="w")
        self.folder_entry = ctk.CTkEntry(top_frame, height=34)
        self.folder_entry.insert(0, self.initial_folder)
        self.folder_entry.grid(row=2, column=1, padx=4, pady=8, sticky="ew")

        ctk.CTkButton(
            top_frame,
            text="Browse",
            width=90,
            height=34,
            command=self._browse_folder,
        ).grid(row=2, column=2, padx=(4, 16), pady=8)

        # Scan check boxes
        opts_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        opts_frame.grid(row=3, column=0, columnspan=3, padx=16, pady=(4, 12), sticky="ew")

        self.opt_empty_dirs = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opts_frame, text="📁 Empty Subdirectories", variable=self.opt_empty_dirs).pack(side="left", padx=(0, 14))

        self.opt_zero_byte = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opts_frame, text="📄 Zero-Byte Files (0 B)", variable=self.opt_zero_byte).pack(side="left", padx=14)

        self.opt_os_debris = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opts_frame, text="🗑️ OS Debris (Thumbs.db, .DS_Store)", variable=self.opt_os_debris).pack(side="left", padx=14)

        self.scan_btn = ctk.CTkButton(
            opts_frame,
            text="🔍 Scan for Junk",
            font=ctk.CTkFont(weight="bold", size=13),
            height=34,
            width=160,
            fg_color="#1971C2",
            hover_color="#1864AB",
            command=self._start_scan,
        )
        self.scan_btn.pack(side="right")

        # -------------------------------------------------------------
        # 2. Progress & Status Card
        # -------------------------------------------------------------
        self.status_card = ctk.CTkFrame(self, fg_color="#1A1B1E", corner_radius=8)
        self.status_card.grid(row=1, column=0, padx=16, pady=6, sticky="ew")
        self.status_card.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(self.status_card, height=8)
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", padx=16, pady=(10, 4))

        self.status_label = ctk.CTkLabel(
            self.status_card,
            text="Click 'Scan for Junk' to search for empty folders and debris.",
            font=ctk.CTkFont(size=12),
            text_color="#ADB5BD",
        )
        self.status_label.pack(side="left", padx=16, pady=(2, 10))

        self.count_badge = ctk.CTkLabel(
            self.status_card,
            text="Items: 0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#74C0FC",
        )
        self.count_badge.pack(side="right", padx=16, pady=(2, 10))

        # -------------------------------------------------------------
        # 3. Scrollable Results List
        # -------------------------------------------------------------
        self.scroll_results = ctk.CTkScrollableFrame(self, fg_color="#141517")
        self.scroll_results.grid(row=2, column=0, padx=16, pady=8, sticky="nsew")
        self.scroll_results.grid_columnconfigure(0, weight=1)

        # -------------------------------------------------------------
        # 4. Action Footer Bar
        # -------------------------------------------------------------
        footer_frame = ctk.CTkFrame(self, fg_color="#1E1E24")
        footer_frame.grid(row=3, column=0, padx=16, pady=(8, 16), sticky="ew")

        ctk.CTkButton(
            footer_frame,
            text="Close",
            width=100,
            height=38,
            fg_color="#495057",
            hover_color="#343A40",
            command=self.destroy,
        ).pack(side="right", padx=(8, 16), pady=12)

        self.prune_btn = ctk.CTkButton(
            footer_frame,
            text="🧹 Clean & Prune Selected",
            width=220,
            height=38,
            fg_color="#2B8A3E",
            hover_color="#237032",
            font=ctk.CTkFont(weight="bold", size=13),
            state="disabled",
            command=self._execute_prune,
        )
        self.prune_btn.pack(side="right", padx=6, pady=12)

        self.select_all_btn = ctk.CTkButton(
            footer_frame,
            text="Select All",
            width=110,
            height=38,
            fg_color="#343A40",
            hover_color="#212529",
            state="disabled",
            command=self._select_all,
        )
        self.select_all_btn.pack(side="left", padx=(16, 6), pady=12)

        self.deselect_btn = ctk.CTkButton(
            footer_frame,
            text="Deselect All",
            width=110,
            height=38,
            fg_color="#343A40",
            hover_color="#212529",
            state="disabled",
            command=self._deselect_all,
        )
        self.deselect_btn.pack(side="left", padx=6, pady=12)

    def _browse_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.folder_entry.get().strip() or os.getcwd())
        if chosen:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, chosen)

    def _start_scan(self):
        folder = self.folder_entry.get().strip()
        if not os.path.exists(folder):
            messagebox.showerror("Error", f"Folder does not exist:\n{folder}")
            return

        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.progress_bar.set(0.1)
        self.status_label.configure(text="Scanning directory...")

        for child in self.scroll_results.winfo_children():
            child.destroy()
        self.item_vars.clear()

        thread = threading.Thread(
            target=self._scan_worker,
            args=(
                folder,
                self.opt_empty_dirs.get(),
                self.opt_zero_byte.get(),
                self.opt_os_debris.get(),
            ),
            daemon=True,
        )
        thread.start()

    def _scan_worker(self, folder: str, empty_dirs: bool, zero_byte: bool, os_debris: bool):
        def progress_cb(msg: str, frac: float):
            self.after(0, lambda m=msg, f=frac: self._update_progress(m, f))

        try:
            items = CleanerService.scan(
                folder=folder,
                scan_empty_dirs=empty_dirs,
                scan_zero_byte=zero_byte,
                scan_os_debris=os_debris,
                progress_callback=progress_cb,
            )
            self.after(0, lambda it=items: self._on_scan_complete(it))
        except Exception as e:
            self.after(0, lambda err=str(e): self._on_scan_error(err))

    def _update_progress(self, msg: str, frac: float):
        self.progress_bar.set(frac)
        self.status_label.configure(text=msg)

    def _on_scan_error(self, err_msg: str):
        self.scan_btn.configure(state="normal", text="🔍 Scan for Junk")
        self.status_label.configure(text=f"Error: {err_msg}", text_color="#FFA94D")
        messagebox.showerror("Scan Error", f"An error occurred while scanning:\n{err_msg}")

    def _on_scan_complete(self, items: List[CleanupItem]):
        self.cleanup_items = items
        self.scan_btn.configure(state="normal", text="🔍 Scan for Junk")
        self.progress_bar.set(1.0)

        empty_dir_count = sum(1 for it in items if it.item_type == "empty_dir")
        zero_byte_count = sum(1 for it in items if it.item_type == "zero_byte_file")
        debris_count = sum(1 for it in items if it.item_type == "os_debris")

        self.count_badge.configure(text=f"Found: {len(items)} items")
        self.status_label.configure(
            text=f"✅ Scan finished: {empty_dir_count} empty folders, {zero_byte_count} 0-byte files, {debris_count} OS debris.",
            text_color="#69DB7C",
        )

        if not items:
            lbl = ctk.CTkLabel(
                self.scroll_results,
                text="✨ Directory is completely clean! No empty folders or junk files found.",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#69DB7C",
            )
            lbl.pack(pady=40)
            self.prune_btn.configure(state="disabled")
            self.select_all_btn.configure(state="disabled")
            self.deselect_btn.configure(state="disabled")
            return

        self.prune_btn.configure(state="normal")
        self.select_all_btn.configure(state="normal")
        self.deselect_btn.configure(state="normal")

        # Render list of cleanup items
        for idx, item in enumerate(items):
            var = ctk.BooleanVar(value=True)
            self.item_vars[idx] = var

            row = ctk.CTkFrame(self.scroll_results, fg_color="#1F2023", corner_radius=6, height=36)
            row.pack(fill="x", padx=4, pady=3)
            row.pack_propagate(False)

            cb = ctk.CTkCheckBox(row, text="", variable=var, width=22)
            cb.pack(side="left", padx=(8, 4))

            # Item Type Badge
            if item.item_type == "empty_dir":
                badge_text = "📁 EMPTY DIR"
                badge_color = "#FFD43B"
            elif item.item_type == "zero_byte_file":
                badge_text = "📄 0-BYTE FILE"
                badge_color = "#74C0FC"
            else:
                badge_text = "🗑️ OS DEBRIS"
                badge_color = "#FF8787"

            ctk.CTkLabel(
                row,
                text=badge_text,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=badge_color,
                width=110,
                anchor="w",
            ).pack(side="left", padx=4)

            # Path & Reason
            ctk.CTkLabel(
                row,
                text=item.path,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#E9ECEF",
                anchor="w",
            ).pack(side="left", fill="x", expand=True, padx=6)

            if item.size_bytes > 0:
                sz_str = DeduplicationService.format_bytes(item.size_bytes)
                ctk.CTkLabel(
                    row,
                    text=sz_str,
                    font=ctk.CTkFont(size=11),
                    text_color="gray",
                ).pack(side="right", padx=10)

    def _select_all(self):
        for var in self.item_vars.values():
            var.set(True)

    def _deselect_all(self):
        for var in self.item_vars.values():
            var.set(False)

    def _execute_prune(self):
        selected_items = [
            self.cleanup_items[idx]
            for idx, var in self.item_vars.items()
            if var.get()
        ]

        if not selected_items:
            messagebox.showinfo("None Selected", "Please select at least one item to prune.")
            return

        confirm = messagebox.askyesno(
            "Confirm Cleanup",
            f"Permanently delete {len(selected_items)} selected empty folders and debris files?\n\n"
            "Empty directories will only be removed if they contain no files.",
        )
        if not confirm:
            return

        report: CleanupReport = CleanerService.prune(selected_items)

        msg = (
            f"🎉 Deep Clean Complete!\n\n"
            f"  • 📁 Empty directories pruned: {len(report.empty_dirs_removed)}\n"
            f"  • 📄 Zero-byte files removed: {len(report.zero_byte_files_removed)}\n"
            f"  • 🗑️ OS debris removed: {len(report.os_debris_removed)}\n"
            f"  • 💾 Storage reclaimed: {DeduplicationService.format_bytes(report.reclaimed_bytes)}"
        )
        messagebox.showinfo("Cleanup Finished", msg)
        self._start_scan()  # Refresh view
