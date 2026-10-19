"""
Interactive Tree Preview & Per-File Checkboxes (Pre-Execution Visualizer)
Allows users to visually review, selectively filter, expand/collapse,
and inspect proposed AI file moves before execution.
"""

import os
import subprocess
import sys
from collections import defaultdict
from typing import List, Dict, Callable
import customtkinter as ctk
from models import FileChange


class TreePreviewDialog(ctk.CTkToplevel):
    """Interactive visual tree preview dialog with hierarchical folder grouping and checkboxes."""

    def __init__(
        self,
        parent,
        changes: List[FileChange],
        output_base_folder: str = "",
        on_confirm: Callable[[List[FileChange]], None] = None,
    ):
        super().__init__(parent)
        self.changes = changes
        self.output_base = output_base_folder
        self.on_confirm = on_confirm

        self.title("🗂️ Proposed Structure Preview & Selective Execution")
        self.geometry("900x720")
        self.minsize(760, 540)
        self.transient(parent)
        self.grab_set()

        # Group changes by destination subfolder
        self.grouped_changes: Dict[str, List[FileChange]] = defaultdict(list)
        self._group_changes()

        # Checkbox variable mappings:
        # file_vars[change_id] -> ctk.BooleanVar
        # folder_vars[folder_name] -> ctk.BooleanVar
        self.file_vars: Dict[int, ctk.BooleanVar] = {}
        self.folder_vars: Dict[str, ctk.BooleanVar] = {}
        self.folder_card_frames: Dict[str, ctk.CTkFrame] = {}
        self.folder_content_frames: Dict[str, ctk.CTkFrame] = {}
        self.folder_toggle_btns: Dict[str, ctk.CTkButton] = {}
        self.folder_expanded: Dict[str, bool] = {}

        self._build_ui()
        self._update_selection_counts()

    def _group_changes(self):
        """Partition proposed moves by relative destination directory."""
        for c in self.changes:
            dest_dir = os.path.dirname(c.new_path)
            if self.output_base and dest_dir.startswith(self.output_base):
                rel_dir = os.path.relpath(dest_dir, self.output_base)
                if rel_dir == ".":
                    rel_dir = "Root Destination"
            else:
                rel_dir = os.path.basename(dest_dir) or "Root Destination"

            self.grouped_changes[rel_dir].append(c)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # -------------------------------------------------------------
        # 1. Header & Controls Bar
        # -------------------------------------------------------------
        header_frame = ctk.CTkFrame(self, fg_color="#1E1E24")
        header_frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        title_label = ctk.CTkLabel(
            header_frame,
            text="📁 Proposed Organization Tree",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#F8F9FA",
        )
        title_label.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        desc_label = ctk.CTkLabel(
            header_frame,
            text="Uncheck any file you wish to skip. Double-click any row to view the original file.",
            font=ctk.CTkFont(size=12),
            text_color="#ADB5BD",
        )
        desc_label.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 10), sticky="w")

        # Search / Filter Entry
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)
        search_entry = ctk.CTkEntry(
            header_frame,
            textvariable=self.search_var,
            placeholder_text="🔎 Search filenames or folders...",
            width=260,
            height=32,
        )
        search_entry.grid(row=0, column=1, padx=(10, 16), pady=(12, 4), sticky="e")

        # Global Action Bar (Select All / Expand / Collapse)
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="s")  # Will overlay or place cleanly

        btn_bar = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_bar.grid(row=2, column=0, columnspan=2, padx=16, pady=(4, 10), sticky="ew")

        ctk.CTkButton(
            btn_bar,
            text="☑ Select All",
            width=95,
            height=28,
            command=self._select_all,
            font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_bar,
            text="☐ Deselect All",
            width=100,
            height=28,
            command=self._deselect_all,
            font=ctk.CTkFont(size=11),
            fg_color="#495057",
            hover_color="#343A40",
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_bar,
            text="▼ Expand All",
            width=95,
            height=28,
            command=self._expand_all,
            font=ctk.CTkFont(size=11),
            fg_color="#343A40",
            hover_color="#212529",
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_bar,
            text="▶ Collapse All",
            width=95,
            height=28,
            command=self._collapse_all,
            font=ctk.CTkFont(size=11),
            fg_color="#343A40",
            hover_color="#212529",
        ).pack(side="left", padx=6)

        self.summary_badge = ctk.CTkLabel(
            btn_bar,
            text="Loading...",
            font=ctk.CTkFont(weight="bold", size=12),
            text_color="#74C0FC",
        )
        self.summary_badge.pack(side="right", padx=10)

        # -------------------------------------------------------------
        # 2. Scrollable Hierarchical Tree Canvas
        # -------------------------------------------------------------
        self.scroll_tree = ctk.CTkScrollableFrame(self, fg_color="#141517")
        self.scroll_tree.grid(row=1, column=0, padx=16, pady=8, sticky="nsew")
        self.scroll_tree.grid_columnconfigure(0, weight=1)

        self.file_row_widgets = []
        change_idx = 0

        # Render folder clusters
        for folder_name, folder_files in sorted(self.grouped_changes.items()):
            folder_var = ctk.BooleanVar(value=True)
            self.folder_vars[folder_name] = folder_var
            self.folder_expanded[folder_name] = True

            # Folder Card Container
            card = ctk.CTkFrame(self.scroll_tree, fg_color="#1F2023", corner_radius=8, border_width=1, border_color="#2C2E33")
            card.pack(fill="x", padx=4, pady=6)
            card.grid_columnconfigure(0, weight=1)
            self.folder_card_frames[folder_name] = card

            # Header row of folder card
            header_row = ctk.CTkFrame(card, fg_color="#25262B", corner_radius=6, height=38)
            header_row.pack(fill="x", padx=4, pady=4)
            header_row.pack_propagate(False)

            toggle_btn = ctk.CTkButton(
                header_row,
                text="▼",
                width=28,
                height=26,
                fg_color="transparent",
                hover_color="#373A40",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda fn=folder_name: self._toggle_folder(fn),
            )
            toggle_btn.pack(side="left", padx=(6, 2))
            self.folder_toggle_btns[folder_name] = toggle_btn

            folder_cb = ctk.CTkCheckBox(
                header_row,
                text=f"📂 {folder_name}  ({len(folder_files)} files)",
                variable=folder_var,
                command=lambda fn=folder_name: self._on_folder_checkbox_toggled(fn),
                font=ctk.CTkFont(weight="bold", size=13),
                text_color="#F1F3F5",
            )
            folder_cb.pack(side="left", padx=6)

            # Container for file child rows
            content_frame = ctk.CTkFrame(card, fg_color="transparent")
            content_frame.pack(fill="x", padx=12, pady=(2, 6))
            content_frame.grid_columnconfigure(1, weight=1)
            self.folder_content_frames[folder_name] = content_frame

            # Child file rows
            for c in folder_files:
                var = ctk.BooleanVar(value=True)
                self.file_vars[change_idx] = var

                row = ctk.CTkFrame(content_frame, fg_color="#1A1B1E", corner_radius=4, height=32)
                row.pack(fill="x", pady=2)
                row.pack_propagate(False)

                cb = ctk.CTkCheckBox(
                    row,
                    text="",
                    variable=var,
                    width=22,
                    command=lambda fn=folder_name: self._on_file_checkbox_toggled(fn),
                )
                cb.pack(side="left", padx=(8, 4))

                orig_name = os.path.basename(c.original)
                dest_name = os.path.basename(c.new_path)
                is_renamed = orig_name != dest_name

                name_frame = ctk.CTkFrame(row, fg_color="transparent")
                name_frame.pack(side="left", fill="both", expand=True, padx=4)

                if is_renamed:
                    display_text = f"📄 {orig_name}   ➔   ✨ {dest_name}"
                    text_color = "#69DB7C"
                else:
                    display_text = f"📄 {orig_name}"
                    text_color = "#E9ECEF"

                lbl = ctk.CTkLabel(
                    name_frame,
                    text=display_text,
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=text_color,
                    anchor="w",
                )
                lbl.pack(side="left", fill="x", expand=True)

                # Action button to preview original file in FileViewerDialog
                inspect_btn = ctk.CTkButton(
                    row,
                    text="👁️ Preview",
                    width=62,
                    height=22,
                    fg_color="#2C2E33",
                    hover_color="#373A40",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    command=lambda p=c.original: self._open_viewer(p),
                )
                inspect_btn.pack(side="right", padx=(4, 8))

                # Allow double clicking label to preview file
                lbl.bind("<Double-Button-1>", lambda event, p=c.original: self._open_viewer(p))

                # Keep references for live search filtering
                self.file_row_widgets.append({
                    "row": row,
                    "folder": folder_name.lower(),
                    "orig_name": orig_name.lower(),
                    "dest_name": dest_name.lower(),
                    "change_idx": change_idx,
                })

                change_idx += 1

        # -------------------------------------------------------------
        # 3. Bottom Action Footer Bar
        # -------------------------------------------------------------
        footer_frame = ctk.CTkFrame(self, fg_color="#1E1E24")
        footer_frame.grid(row=2, column=0, padx=16, pady=(8, 16), sticky="ew")

        self.cancel_btn = ctk.CTkButton(
            footer_frame,
            text="Cancel",
            width=110,
            height=38,
            fg_color="#495057",
            hover_color="#343A40",
            command=self.destroy,
        )
        self.cancel_btn.pack(side="right", padx=(8, 16), pady=12)

        self.execute_btn = ctk.CTkButton(
            footer_frame,
            text="🚀 Execute Selected Moves",
            width=230,
            height=38,
            fg_color="#2B8A3E",
            hover_color="#237032",
            font=ctk.CTkFont(weight="bold", size=13),
            command=self._confirm_execution,
        )
        self.execute_btn.pack(side="right", padx=8, pady=12)

        self.status_detail = ctk.CTkLabel(
            footer_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#ADB5BD",
        )
        self.status_detail.pack(side="left", padx=16, pady=12)

    def _toggle_folder(self, folder_name: str):
        """Expand or collapse a folder's children."""
        is_expanded = self.folder_expanded.get(folder_name, True)
        content_frame = self.folder_content_frames.get(folder_name)
        toggle_btn = self.folder_toggle_btns.get(folder_name)

        if is_expanded:
            if content_frame:
                content_frame.pack_forget()
            if toggle_btn:
                toggle_btn.configure(text="▶")
            self.folder_expanded[folder_name] = False
        else:
            if content_frame:
                content_frame.pack(fill="x", padx=12, pady=(2, 6))
            if toggle_btn:
                toggle_btn.configure(text="▼")
            self.folder_expanded[folder_name] = True

    def _expand_all(self):
        for fn in self.folder_expanded.keys():
            if not self.folder_expanded[fn]:
                self._toggle_folder(fn)

    def _collapse_all(self):
        for fn in self.folder_expanded.keys():
            if self.folder_expanded[fn]:
                self._toggle_folder(fn)

    def _on_folder_checkbox_toggled(self, folder_name: str):
        """Set all children files to match the parent folder's check state."""
        state = self.folder_vars[folder_name].get()
        folder_files = self.grouped_changes[folder_name]
        for c in folder_files:
            idx = self.changes.index(c)
            if idx in self.file_vars:
                self.file_vars[idx].set(state)
        self._update_selection_counts()

    def _on_file_checkbox_toggled(self, folder_name: str):
        """Update parent folder checkbox state based on child file states."""
        folder_files = self.grouped_changes[folder_name]
        indices = [self.changes.index(c) for c in folder_files]
        all_checked = all(self.file_vars[idx].get() for idx in indices if idx in self.file_vars)
        self.folder_vars[folder_name].set(all_checked)
        self._update_selection_counts()

    def _select_all(self):
        for var in self.file_vars.values():
            var.set(True)
        for var in self.folder_vars.values():
            var.set(True)
        self._update_selection_counts()

    def _deselect_all(self):
        for var in self.file_vars.values():
            var.set(False)
        for var in self.folder_vars.values():
            var.set(False)
        self._update_selection_counts()

    def _update_selection_counts(self):
        """Recalculate selected files and update badges and action buttons."""
        selected_count = sum(1 for var in self.file_vars.values() if var.get())
        total = len(self.changes)
        skipped = total - selected_count

        self.summary_badge.configure(text=f"Selected: {selected_count} / {total} files")
        if skipped > 0:
            self.status_detail.configure(
                text=f"Ready to move {selected_count} files ({skipped} will be skipped and left in place).",
                text_color="#FFA94D",
            )
        else:
            self.status_detail.configure(
                text=f"All {total} proposed file moves selected.",
                text_color="#69DB7C",
            )

        if selected_count > 0:
            self.execute_btn.configure(
                state="normal",
                text=f"🚀 Execute Selected Moves ({selected_count})",
                fg_color="#2B8A3E",
            )
        else:
            self.execute_btn.configure(
                state="disabled",
                text="Select at least 1 file",
                fg_color="#495057",
            )

    def _on_search_changed(self, *args):
        """Live filter displayed file rows based on query."""
        query = self.search_var.get().strip().lower()

        # Check visibility for each row
        matched_folders = set()
        for item in self.file_row_widgets:
            match = (
                not query
                or query in item["orig_name"]
                or query in item["dest_name"]
                or query in item["folder"]
            )
            if match:
                item["row"].pack(fill="x", pady=2)
                matched_folders.add(item["folder"])
            else:
                item["row"].pack_forget()

        # Auto-expand folders with matches
        if query:
            for fn, card in self.folder_card_frames.items():
                if fn.lower() in matched_folders:
                    card.pack(fill="x", padx=4, pady=6)
                    if not self.folder_expanded.get(fn, False):
                        self._toggle_folder(fn)
                else:
                    card.pack_forget()
        else:
            for fn, card in self.folder_card_frames.items():
                card.pack(fill="x", padx=4, pady=6)

    def _open_file(self, filepath: str):
        """Open file directly in the default system application (e.g. Windows Photos, Notepad, Acrobat)."""
        if not filepath:
            return
        target = os.path.abspath(filepath)
        if not os.path.exists(target):
            target = filepath
            if not os.path.exists(target):
                return
        try:
            if sys.platform == "win32":
                os.startfile(target)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", target])  # hygiene: allow native system file launcher launches external viewer asynchronously
            else:
                subprocess.Popen(["xdg-open", target])  # hygiene: allow native system file launcher launches external viewer asynchronously
        except Exception as e:
            print(f"Could not open file: {e}")

    def _open_viewer(self, filepath: str):
        """Open file inside the aesthetic in-app FileViewerDialog with guaranteed foreground lift."""
        if not filepath:
            return
        target = os.path.abspath(filepath)
        if not os.path.exists(target):
            target = filepath
            if not os.path.exists(target):
                return
        from .file_viewer import FileViewerDialog
        dlg = FileViewerDialog(parent=self, filepath=target)
        try:
            dlg.lift()
            dlg.focus_force()
        except Exception:  # hygiene: allow window manager focus failure on destroyed or unfocused dialog
            pass

    def _confirm_execution(self):
        """Extract checked files and dispatch to callback."""
        selected_changes = [
            c for idx, c in enumerate(self.changes)
            if self.file_vars.get(idx, ctk.BooleanVar(value=False)).get()
        ]
        self.destroy()
        if self.on_confirm:
            self.on_confirm(selected_changes)
