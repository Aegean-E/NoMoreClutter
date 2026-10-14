"""
Smart Duplicate File Finder & Storage Reclaimer UI Dialog
Allows users to scan for identical duplicates, view reclaimable space,
and isolate or safely delete duplicate files.
"""

import os
import subprocess
import sys
import threading
from typing import List, Dict
import customtkinter as ctk
from tkinter import filedialog, messagebox
from models import DuplicateGroup
from services.deduplicator import DeduplicationService


class DuplicateFinderDialog(ctk.CTkToplevel):
    """Interactive Duplicate File Finder & Storage Reclaimer."""

    def __init__(self, parent, initial_folder: str = ""):
        super().__init__(parent)
        self.initial_folder = initial_folder or os.getcwd()
        self.duplicate_groups: List[DuplicateGroup] = []

        self.title("🔍 Smart Duplicate Finder & Storage Reclaimer")
        self.geometry("920x720")
        self.minsize(780, 540)
        self.transient(parent)

        # Mapping: duplicate_filepath -> ctk.BooleanVar
        self.dup_checkbox_vars: Dict[str, ctk.BooleanVar] = {}

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # -------------------------------------------------------------
        # 1. Header & Folder Selector
        # -------------------------------------------------------------
        top_frame = ctk.CTkFrame(self, fg_color="#1E1E24")
        top_frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top_frame,
            text="🔍 Duplicate File Finder & Storage Reclaimer",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#F8F9FA",
        ).grid(row=0, column=0, columnspan=3, padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            top_frame,
            text="Detects exact duplicates via two-stage O(N) size matching + SHA-256 chunk hashing.",
            font=ctk.CTkFont(size=12),
            text_color="#ADB5BD",
        ).grid(row=1, column=0, columnspan=3, padx=16, pady=(0, 10), sticky="w")

        # Folder picker
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

        # Options & Scan Trigger Row
        opts_row = ctk.CTkFrame(top_frame, fg_color="transparent")
        opts_row.grid(row=3, column=0, columnspan=3, padx=16, pady=(4, 12), sticky="ew")

        self.recursive_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opts_row, text="Scan Subdirectories Recursively", variable=self.recursive_var).pack(side="left", padx=(0, 16))

        self.scan_btn = ctk.CTkButton(
            opts_row,
            text="🔍 Scan for Duplicates",
            font=ctk.CTkFont(weight="bold", size=13),
            height=34,
            width=180,
            fg_color="#1971C2",
            hover_color="#1864AB",
            command=self._start_scan,
        )
        self.scan_btn.pack(side="right")

        # -------------------------------------------------------------
        # 2. Progress & Metrics Card
        # -------------------------------------------------------------
        self.metrics_card = ctk.CTkFrame(self, fg_color="#1A1B1E", corner_radius=8)
        self.metrics_card.grid(row=1, column=0, padx=16, pady=6, sticky="ew")
        self.metrics_card.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(self.metrics_card, height=8)
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", padx=16, pady=(10, 4))

        self.status_label = ctk.CTkLabel(
            self.metrics_card,
            text="Click 'Scan for Duplicates' to begin analysis.",
            font=ctk.CTkFont(size=12),
            text_color="#ADB5BD",
        )
        self.status_label.pack(side="left", padx=16, pady=(2, 10))

        self.reclaim_badge = ctk.CTkLabel(
            self.metrics_card,
            text="Reclaimable: 0 B",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#69DB7C",
        )
        self.reclaim_badge.pack(side="right", padx=16, pady=(2, 10))

        # -------------------------------------------------------------
        # 3. Scrollable Results Frame
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

        self.delete_btn = ctk.CTkButton(
            footer_frame,
            text="🗑️ Delete Selected",
            width=160,
            height=38,
            fg_color="#C92A2A",
            hover_color="#A61E4D",
            font=ctk.CTkFont(weight="bold"),
            state="disabled",
            command=self._delete_selected,
        )
        self.delete_btn.pack(side="right", padx=6, pady=12)

        self.isolate_btn = ctk.CTkButton(
            footer_frame,
            text="📦 Isolate to _Duplicates/",
            width=190,
            height=38,
            fg_color="#2B8A3E",
            hover_color="#237032",
            font=ctk.CTkFont(weight="bold"),
            state="disabled",
            command=self._isolate_selected,
        )
        self.isolate_btn.pack(side="right", padx=6, pady=12)

        self.select_all_btn = ctk.CTkButton(
            footer_frame,
            text="Select All Duplicates",
            width=160,
            height=38,
            fg_color="#343A40",
            hover_color="#212529",
            state="disabled",
            command=self._select_all_dups,
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
            command=self._deselect_all_dups,
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
        self.progress_bar.set(0.05)
        self.status_label.configure(text="Scanning directory for duplicate candidates...")

        # Clear existing view
        for child in self.scroll_results.winfo_children():
            child.destroy()
        self.dup_checkbox_vars.clear()

        thread = threading.Thread(target=self._scan_worker, args=(folder, self.recursive_var.get()), daemon=True)
        thread.start()

    def _scan_worker(self, folder: str, recursive: bool):
        def progress_cb(msg: str, frac: float):
            self.after(0, lambda m=msg, f=frac: self._update_progress(m, f))

        try:
            groups = DeduplicationService.scan_duplicates(
                folder=folder,
                recursive=recursive,
                progress_callback=progress_cb,
            )
            self.after(0, lambda g=groups: self._on_scan_complete(g))
        except Exception as e:
            self.after(0, lambda err=str(e): self._on_scan_error(err))

    def _update_progress(self, msg: str, frac: float):
        self.progress_bar.set(frac)
        self.status_label.configure(text=msg)

    def _on_scan_error(self, err_msg: str):
        self.scan_btn.configure(state="normal", text="🔍 Scan for Duplicates")
        self.status_label.configure(text=f"Scan error: {err_msg}", text_color="#FFA94D")
        messagebox.showerror("Scan Error", f"An error occurred while scanning:\n{err_msg}")

    def _on_scan_complete(self, groups: List[DuplicateGroup]):
        self.duplicate_groups = groups
        self.scan_btn.configure(state="normal", text="🔍 Scan for Duplicates")
        self.progress_bar.set(1.0)

        total_reclaimable = sum(g.reclaimable_bytes for g in groups)
        total_dup_files = sum(len(g.duplicates) for g in groups)

        self.reclaim_badge.configure(
            text=f"💾 Reclaimable: {DeduplicationService.format_bytes(total_reclaimable)}"
        )
        self.status_label.configure(
            text=f"✅ Found {len(groups)} duplicate sets ({total_dup_files} redundant files).",
            text_color="#69DB7C",
        )

        if not groups:
            empty_lbl = ctk.CTkLabel(
                self.scroll_results,
                text="🎉 No duplicate files found in this directory! Everything is unique.",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#69DB7C",
            )
            empty_lbl.pack(pady=40)
            self.isolate_btn.configure(state="disabled")
            self.delete_btn.configure(state="disabled")
            self.select_all_btn.configure(state="disabled")
            self.deselect_btn.configure(state="disabled")
            return

        self.isolate_btn.configure(state="normal")
        self.delete_btn.configure(state="normal")
        self.select_all_btn.configure(state="normal")
        self.deselect_btn.configure(state="normal")

        # Render each duplicate cluster
        for idx, group in enumerate(groups):
            card = ctk.CTkFrame(self.scroll_results, fg_color="#1E1E24", corner_radius=8, border_width=1, border_color="#2C2E33")
            card.pack(fill="x", padx=4, pady=6)
            card.grid_columnconfigure(0, weight=1)

            # Cluster header
            hdr = ctk.CTkFrame(card, fg_color="#25262B", corner_radius=6, height=32)
            hdr.pack(fill="x", padx=4, pady=4)
            hdr.pack_propagate(False)

            sz_text = DeduplicationService.format_bytes(group.file_size)
            reclaim_grp = DeduplicationService.format_bytes(group.reclaimable_bytes)
            ctk.CTkLabel(
                hdr,
                text=f"Set #{idx+1}: {sz_text} each  •  {len(group.all_files)} identical files  •  Saves {reclaim_grp}",
                font=ctk.CTkFont(weight="bold", size=12),
                text_color="#74C0FC",
            ).pack(side="left", padx=10)

            ctk.CTkLabel(
                hdr,
                text=f"SHA: {group.sha256[:12]}...",
                font=ctk.CTkFont(family="Consolas", size=10),
                text_color="gray",
            ).pack(side="right", padx=10)

            # Original Row (Preserved)
            orig_row = ctk.CTkFrame(card, fg_color="#182A1B", corner_radius=4, height=30)
            orig_row.pack(fill="x", padx=8, pady=(2, 2))
            orig_row.pack_propagate(False)

            ctk.CTkLabel(
                orig_row,
                text="🟢 ORIGINAL (Keep)",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#69DB7C",
            ).pack(side="left", padx=8)

            ctk.CTkLabel(
                orig_row,
                text=group.original,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#E9ECEF",
                anchor="w",
            ).pack(side="left", fill="x", expand=True, padx=4)

            ctk.CTkButton(
                orig_row,
                text="👁️ Open",
                width=50,
                height=20,
                font=ctk.CTkFont(size=9),
                fg_color="#2C2E33",
                hover_color="#373A40",
                command=lambda p=group.original: self._open_file(p),
            ).pack(side="right", padx=6)

            # Duplicate Rows (Selected for action)
            for dup_path in group.duplicates:
                dup_var = ctk.BooleanVar(value=True)
                self.dup_checkbox_vars[dup_path] = dup_var

                dup_row = ctk.CTkFrame(card, fg_color="#2B1D1D", corner_radius=4, height=30)
                dup_row.pack(fill="x", padx=8, pady=2)
                dup_row.pack_propagate(False)

                cb = ctk.CTkCheckBox(dup_row, text="", variable=dup_var, width=20)
                cb.pack(side="left", padx=(8, 4))

                ctk.CTkLabel(
                    dup_row,
                    text="🔴 DUPLICATE",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color="#FF8787",
                ).pack(side="left", padx=4)

                ctk.CTkLabel(
                    dup_row,
                    text=dup_path,
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color="#CED4DA",
                    anchor="w",
                ).pack(side="left", fill="x", expand=True, padx=4)

                ctk.CTkButton(
                    dup_row,
                    text="👁️ Open",
                    width=50,
                    height=20,
                    font=ctk.CTkFont(size=9),
                    fg_color="#2C2E33",
                    hover_color="#373A40",
                    command=lambda p=dup_path: self._open_file(p),
                ).pack(side="right", padx=6)

    def _select_all_dups(self):
        for var in self.dup_checkbox_vars.values():
            var.set(True)

    def _deselect_all_dups(self):
        for var in self.dup_checkbox_vars.values():
            var.set(False)

    def _get_selected_duplicate_paths(self) -> List[str]:
        return [p for p, var in self.dup_checkbox_vars.items() if var.get()]

    def _isolate_selected(self):
        selected = self._get_selected_duplicate_paths()
        if not selected:
            messagebox.showinfo("None Selected", "Please select at least one duplicate file to isolate.")
            return

        folder = self.folder_entry.get().strip()
        confirm = messagebox.askyesno(
            "Confirm Isolation",
            f"Move {len(selected)} duplicate files into '{folder}/_Duplicates/'?\n\n"
            "This will clear duplicate clutter from your folders without permanently deleting anything.",
        )
        if not confirm:
            return

        moved, errors = DeduplicationService.isolate_duplicates(selected, folder)
        msg = f"Successfully isolated {moved} duplicate files into '_Duplicates/'!"
        if errors:
            msg += f"\n\nErrors encountered:\n" + "\n".join(errors[:5])
        messagebox.showinfo("Isolation Complete", msg)
        self._start_scan()  # Refresh

    def _delete_selected(self):
        selected = self._get_selected_duplicate_paths()
        if not selected:
            messagebox.showinfo("None Selected", "Please select at least one duplicate file to delete.")
            return

        confirm = messagebox.askyesno(
            "⚠️ Confirm Deletion",
            f"Are you sure you want to permanently delete {len(selected)} duplicate files?\n\n"
            "The original files will remain untouched.",
        )
        if not confirm:
            return

        deleted, errors = DeduplicationService.delete_duplicates(selected)
        msg = f"Permanently deleted {deleted} duplicate files."
        if errors:
            msg += f"\n\nErrors encountered:\n" + "\n".join(errors[:5])
        messagebox.showinfo("Deletion Complete", msg)
        self._start_scan()  # Refresh

    def _open_file(self, filepath: str):
        if not os.path.exists(filepath):
            return
        try:
            if sys.platform == "win32":
                os.startfile(filepath)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", filepath])
            else:
                subprocess.Popen(["xdg-open", filepath])
        except Exception as e:
            print(f"Could not open file: {e}")
