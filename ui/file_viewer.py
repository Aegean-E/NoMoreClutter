"""
In-App File Viewer & Visual Duplicate Inspector (PRINCIPLE-003, PRINCIPLE-007, PRINCIPLE-012)
Provides an aesthetic, dark-themed in-app preview for images, text, code, documents (PDF/DOCX),
and binary files with side-by-side duplicate comparison support.
"""

import os
import sys
import time
from datetime import datetime
import subprocess
from typing import Optional, Callable
import customtkinter as ctk
from tkinter import messagebox

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from services.document_peeker import DocumentPeeker
from services.deduplicator import DeduplicationService

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".ico", ".tiff", ".tif"
}
TEXT_EXTENSIONS = {
    ".txt", ".py", ".json", ".csv", ".tsv", ".md", ".markdown", ".rst",
    ".xml", ".html", ".htm", ".css", ".js", ".ts", ".jsx", ".tsx",
    ".yml", ".yaml", ".log", ".ini", ".cfg", ".conf", ".bat", ".sh",
    ".ps1", ".sql", ".rs", ".go", ".java", ".c", ".cpp", ".h", ".cs"
}
DOCUMENT_EXTENSIONS = {".pdf", ".docx"}


def get_category_badge(ext: str) -> str:
    """Return a visual category badge for a given file extension."""
    ext = ext.lower()
    if ext in IMAGE_EXTENSIONS:
        return "🖼️ Image"
    if ext in TEXT_EXTENSIONS:
        return "📝 Text/Code"
    if ext in DOCUMENT_EXTENSIONS:
        return "📄 Document"
    if ext in {".mp3", ".wav", ".flac", ".ogg", ".mp4", ".mkv", ".mov", ".avi"}:
        return "🎬 Media"
    if ext in {".zip", ".tar", ".gz", ".7z", ".rar"}:
        return "📦 Archive"
    return "📁 File"


def get_file_meta_summary(path: str) -> str:
    """Extract human-readable file size and modified timestamp."""
    if not os.path.exists(path):
        return "File does not exist on disk."
    try:
        stat = os.stat(path)
        sz = DeduplicationService.format_bytes(stat.st_size)
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        return f"Size: {sz} ({stat.st_size:,} bytes)  •  Modified: {mtime}"
    except Exception as e:
        return f"Error reading stats: {e}"


def compute_image_preview_size(orig_w: int, orig_h: int, max_w: int, max_h: int) -> tuple[int, int, float]:
    """Calculate scaled dimensions preserving aspect ratio without distortion."""
    if orig_w <= 0 or orig_h <= 0:
        return (1, 1, 1.0)
    scale = min(max_w / orig_w, max_h / orig_h, 1.0)
    disp_w = max(1, int(orig_w * scale))
    disp_h = max(1, int(orig_h * scale))
    return disp_w, disp_h, scale


def read_text_preview(filepath: str, max_lines: int = 1000) -> str:
    """Read first max_lines safely across common encodings."""
    if not os.path.exists(filepath):
        return "File not found on disk."
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            with open(filepath, "r", encoding=encoding) as f:
                lines = []
                for _ in range(max_lines):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line)
                return "".join(lines)
        except (UnicodeDecodeError, OSError):
            continue
    return "[Could not decode file with standard text encodings]"


def generate_hexdump(data: bytes) -> str:
    """Generate canonical hex dump representation of binary bytes."""
    if not data:
        return "[0-byte Empty File]"
    lines = []
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        hex_bytes = " ".join(f"{b:02X}" for b in chunk)
        ascii_repr = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        lines.append(f"{i:08X}:  {hex_bytes:<48}  |{ascii_repr}|")
    return "\n".join(lines)


class FileViewerDialog(ctk.CTkToplevel):
    """
    Rich in-app File Viewer and Side-by-Side Duplicate Comparator.
    """

    def __init__(
        self,
        parent,
        filepath: str,
        compare_filepath: Optional[str] = None,
        on_action_performed: Optional[Callable[[str, str], None]] = None,
    ):
        super().__init__(parent)
        self.filepath = os.path.abspath(filepath)
        self.compare_filepath = os.path.abspath(compare_filepath) if compare_filepath else None
        self.on_action_performed = on_action_performed

        self.is_compare_mode = bool(self.compare_filepath and os.path.exists(self.compare_filepath))

        if self.is_compare_mode:
            self.title("👥 Duplicate Inspector & Visual Side-by-Side Comparator")
            self.geometry("1160x740")
            self.minsize(980, 600)
        else:
            self.title(f"👁️ File Viewer — {os.path.basename(self.filepath)}")
            self.geometry("860x680")
            self.minsize(720, 500)

        self.transient(parent)
        self.configure(fg_color="#141517")

        # Keep references to CTkImage objects so they aren't garbage collected
        self._image_refs = []

        self._build_ui()

        # Handle modal grab safely: transfer grab if parent held it so dialog is interactive
        self._parent_grabbed = False
        try:
            if parent and hasattr(parent, "grab_current") and parent.grab_current():
                self._parent_grabbed = True
                parent.grab_release()
            self.grab_set()
        except Exception:
            pass

        # Lift dialog directly to the foreground so the preview image is immediately visible
        self.lift()
        self.focus_force()
        try:
            self.attributes("-topmost", True)
            self.after(200, lambda: self.attributes("-topmost", False) if self.winfo_exists() else None)
        except Exception:
            pass

    def destroy(self):
        try:
            self.grab_release()
        except Exception:
            pass
        if getattr(self, "_parent_grabbed", False) and self.master and self.master.winfo_exists():
            try:
                self.master.grab_set()
            except Exception:
                pass
        super().destroy()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # -------------------------------------------------------------
        # Top Header Bar: Title, Type Badge, and Quick Actions
        # -------------------------------------------------------------
        header_frame = ctk.CTkFrame(self, fg_color="#1E1E24", corner_radius=0, height=56)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.pack_propagate(False)

        # Left header: Icon & Title
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=16, pady=8)

        if self.is_compare_mode:
            ctk.CTkLabel(
                title_box,
                text="👥 Duplicate File Comparison",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#F8F9FA",
            ).pack(anchor="w")
            ctk.CTkLabel(
                title_box,
                text="Compare the canonical original with the redundant copy side-by-side before deciding.",
                font=ctk.CTkFont(size=11),
                text_color="#ADB5BD",
            ).pack(anchor="w")
        else:
            ext = os.path.splitext(self.filepath)[1].lower()
            badge_text = self._get_category_badge(ext)
            ctk.CTkLabel(
                title_box,
                text=f"{badge_text}  {os.path.basename(self.filepath)}",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#F8F9FA",
            ).pack(anchor="w")
            ctk.CTkLabel(
                title_box,
                text=self.filepath,
                font=ctk.CTkFont(size=11),
                text_color="#ADB5BD",
            ).pack(anchor="w")

        # Right header: OS Open & Close buttons
        actions_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_box.pack(side="right", padx=16, pady=8)

        ctk.CTkButton(
            actions_box,
            text="📋 Copy Path",
            width=90,
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color="#25262B",
            hover_color="#373A40",
            command=self._copy_primary_path,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            actions_box,
            text="📂 Reveal",
            width=80,
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color="#25262B",
            hover_color="#373A40",
            command=lambda: self._reveal_in_explorer(self.filepath),
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            actions_box,
            text="🚀 OS Open",
            width=85,
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color="#1971C2",
            hover_color="#1864AB",
            command=lambda: self._open_system_default(self.filepath),
        ).pack(side="left", padx=4)

        # -------------------------------------------------------------
        # Main Viewer Area
        # -------------------------------------------------------------
        if self.is_compare_mode:
            self._build_compare_view()
        else:
            self._build_single_view()

        # -------------------------------------------------------------
        # Bottom Status Bar
        # -------------------------------------------------------------
        footer_frame = ctk.CTkFrame(self, fg_color="#1E1E24", corner_radius=0, height=36)
        footer_frame.grid(row=2, column=0, sticky="ew")
        footer_frame.pack_propagate(False)

        if not self.is_compare_mode:
            stat_text = self._get_file_meta_summary(self.filepath)
            ctk.CTkLabel(
                footer_frame,
                text=stat_text,
                font=ctk.CTkFont(family="Consolas", size=11),
                text_color="#CED4DA",
            ).pack(side="left", padx=16)

        ctk.CTkButton(
            footer_frame,
            text="Close",
            width=70,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#2C2E33",
            hover_color="#373A40",
            command=self.destroy,
        ).pack(side="right", padx=16)

    def _get_category_badge(self, ext: str) -> str:
        return get_category_badge(ext)

    def _get_file_meta_summary(self, path: str) -> str:
        return get_file_meta_summary(path)

    # =========================================================================
    # SINGLE FILE VIEW
    # =========================================================================
    def _build_single_view(self):
        container = ctk.CTkFrame(self, fg_color="#141517", corner_radius=0)
        container.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self._render_file_preview(container, self.filepath, max_w=800, max_h=520)

    # =========================================================================
    # SIDE-BY-SIDE COMPARE VIEW
    # =========================================================================
    def _build_compare_view(self):
        container = ctk.CTkFrame(self, fg_color="#141517", corner_radius=0)
        container.grid(row=1, column=0, sticky="nsew", padx=16, pady=10)
        container.grid_columnconfigure((0, 1), weight=1, uniform="col")
        container.grid_rowconfigure(1, weight=1)

        # Match verification banner
        banner = ctk.CTkFrame(container, fg_color="#1C2E20", corner_radius=6, height=36)
        banner.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        banner.pack_propagate(False)

        identical = False
        try:
            sz1 = os.path.getsize(self.compare_filepath)
            sz2 = os.path.getsize(self.filepath)
            identical = (sz1 == sz2)
        except Exception:
            pass

        if identical:
            banner_text = "✅ 100% Byte-for-Byte Match (Confirmed Duplicate Set) — Both files share identical data."
            banner_color = "#51CF66"
        else:
            banner_text = "⚠️ File sizes differ — Review visual and textual differences below."
            banner_color = "#FFA94D"

        ctk.CTkLabel(
            banner,
            text=banner_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=banner_color,
        ).pack(side="left", padx=12)

        # -------------------------------------------------------------
        # Left Panel: Canonical Original File
        # -------------------------------------------------------------
        left_card = ctk.CTkFrame(container, fg_color="#1E1E24", corner_radius=8, border_width=1, border_color="#2B8A3E")
        left_card.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        left_card.grid_columnconfigure(0, weight=1)
        left_card.grid_rowconfigure(2, weight=1)

        # Left Card Header
        left_hdr = ctk.CTkFrame(left_card, fg_color="#182A1B", corner_radius=6, height=36)
        left_hdr.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        left_hdr.pack_propagate(False)

        ctk.CTkLabel(
            left_hdr,
            text="🟢 CANONICAL ORIGINAL (Kept Safe)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#69DB7C",
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            left_card,
            text=self.compare_filepath,
            font=ctk.CTkFont(size=11),
            text_color="#ADB5BD",
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))

        # Left Preview
        left_preview_box = ctk.CTkFrame(left_card, fg_color="#141517", corner_radius=6)
        left_preview_box.grid(row=2, column=0, sticky="nsew", padx=8, pady=4)
        left_preview_box.grid_columnconfigure(0, weight=1)
        left_preview_box.grid_rowconfigure(0, weight=1)
        self._render_file_preview(left_preview_box, self.compare_filepath, max_w=480, max_h=380)

        # Left Meta summary
        ctk.CTkLabel(
            left_card,
            text=self._get_file_meta_summary(self.compare_filepath),
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color="gray",
        ).grid(row=3, column=0, sticky="w", padx=10, pady=6)

        # -------------------------------------------------------------
        # Right Panel: Redundant Duplicate File
        # -------------------------------------------------------------
        right_card = ctk.CTkFrame(container, fg_color="#1E1E24", corner_radius=8, border_width=1, border_color="#C92A2A")
        right_card.grid(row=1, column=1, sticky="nsew", padx=(6, 0))
        right_card.grid_columnconfigure(0, weight=1)
        right_card.grid_rowconfigure(2, weight=1)

        # Right Card Header
        right_hdr = ctk.CTkFrame(right_card, fg_color="#2B1D1D", corner_radius=6, height=36)
        right_hdr.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        right_hdr.pack_propagate(False)

        ctk.CTkLabel(
            right_hdr,
            text="🔴 REDUNDANT DUPLICATE (Safe to Remove)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FF8787",
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            right_card,
            text=self.filepath,
            font=ctk.CTkFont(size=11),
            text_color="#ADB5BD",
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))

        # Right Preview
        right_preview_box = ctk.CTkFrame(right_card, fg_color="#141517", corner_radius=6)
        right_preview_box.grid(row=2, column=0, sticky="nsew", padx=8, pady=4)
        right_preview_box.grid_columnconfigure(0, weight=1)
        right_preview_box.grid_rowconfigure(0, weight=1)
        self._render_file_preview(right_preview_box, self.filepath, max_w=480, max_h=380)

        # Right Action Buttons
        right_actions = ctk.CTkFrame(right_card, fg_color="transparent")
        right_actions.grid(row=3, column=0, sticky="ew", padx=8, pady=6)

        ctk.CTkLabel(
            right_actions,
            text=self._get_file_meta_summary(self.filepath),
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color="gray",
        ).pack(side="left")

        ctk.CTkButton(
            right_actions,
            text="🗑️ Delete Duplicate",
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#C92A2A",
            hover_color="#A61E4D",
            command=self._delete_duplicate_action,
        ).pack(side="right", padx=(4, 0))

        ctk.CTkButton(
            right_actions,
            text="📦 Isolate",
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#D9480F",
            hover_color="#B63E0C",
            command=self._isolate_duplicate_action,
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            right_actions,
            text="⭐ Set as Original",
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2B8A3E",
            hover_color="#237032",
            command=self._set_as_original_action,
        ).pack(side="right", padx=4)

    # =========================================================================
    # CORE PREVIEW DISPATCHER
    # =========================================================================
    def _render_file_preview(self, parent_widget, filepath: str, max_w: int, max_h: int):
        if not os.path.exists(filepath):
            ctk.CTkLabel(
                parent_widget,
                text="⚠️ File not found on disk.",
                text_color="#FFA94D",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(expand=True)
            return

        ext = os.path.splitext(filepath)[1].lower()

        # 1. Image Preview
        if ext in IMAGE_EXTENSIONS and HAS_PIL:
            self._render_image(parent_widget, filepath, max_w, max_h)
            return

        # 2. Document Preview (PDF / DOCX)
        if ext in DOCUMENT_EXTENSIONS:
            self._render_document(parent_widget, filepath)
            return

        # 3. Plain Text / Code / CSV
        if ext in TEXT_EXTENSIONS:
            self._render_text(parent_widget, filepath)
            return

        # 4. Binary Fallback (Hex dump + metadata)
        self._render_binary(parent_widget, filepath)

    def _render_image(self, parent, filepath: str, max_w: int, max_h: int):
        try:
            with Image.open(filepath) as pil_img:
                orig_w, orig_h = pil_img.size
                mode = pil_img.mode
                disp_w, disp_h, scale = compute_image_preview_size(orig_w, orig_h, max_w, max_h)

                # Ensure image mode is compatible with Tkinter PhotoImage (RGB or RGBA)
                if pil_img.mode in ("RGBA", "LA") or (pil_img.mode == "P" and "transparency" in pil_img.info):
                    converted = pil_img.convert("RGBA")
                else:
                    converted = pil_img.convert("RGB")

                resized = converted.resize((disp_w, disp_h), Image.Resampling.BILINEAR)

            ctk_img = ctk.CTkImage(light_image=resized, dark_image=resized, size=(disp_w, disp_h))
            self._image_refs.append(ctk_img)

            img_container = ctk.CTkFrame(parent, fg_color="transparent")
            img_container.pack(expand=True, fill="both", padx=6, pady=6)

            lbl = ctk.CTkLabel(img_container, image=ctk_img, text="")
            lbl.pack(expand=True)

            ctk.CTkLabel(
                img_container,
                text=f"Resolution: {orig_w} × {orig_h} px  •  Color Mode: {mode}  •  Zoom: {int(scale * 100)}%",
                font=ctk.CTkFont(size=11),
                text_color="#74C0FC",
            ).pack(pady=(4, 0))

        except Exception as e:
            err_box = ctk.CTkFrame(parent, fg_color="transparent")
            err_box.pack(expand=True, fill="both", padx=12, pady=12)
            ctk.CTkLabel(
                err_box,
                text=f"🖼️ In-App Image Preview Unavailable:\n{e}",
                text_color="#FFA94D",
                font=ctk.CTkFont(size=12),
            ).pack(expand=True, pady=(10, 6))
            ctk.CTkButton(
                err_box,
                text="📂 Open with Default System Application",
                command=lambda: self._open_system_default(filepath),
                fg_color="#1971C2",
                hover_color="#1864AB",
                width=240,
                height=32,
            ).pack(pady=6)

    def _render_text(self, parent, filepath: str):
        textbox = ctk.CTkTextbox(
            parent,
            fg_color="#18191D",
            text_color="#E9ECEF",
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="none",
        )
        textbox.pack(fill="both", expand=True, padx=6, pady=6)

        content = read_text_preview(filepath)
        textbox.insert("1.0", content)
        textbox.configure(state="disabled")

    def _render_document(self, parent, filepath: str):
        info_header = ctk.CTkFrame(parent, fg_color="#25262B", height=28)
        info_header.pack(fill="x", padx=6, pady=(6, 2))
        info_header.pack_propagate(False)

        ctk.CTkLabel(
            info_header,
            text="📄 Extracted Document Snippet (Zero-Dependency Content Peeker)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#4DABF7",
        ).pack(side="left", padx=8)

        textbox = ctk.CTkTextbox(
            parent,
            fg_color="#18191D",
            text_color="#E9ECEF",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            wrap="word",
        )
        textbox.pack(fill="both", expand=True, padx=6, pady=(2, 6))

        try:
            peeked_text = DocumentPeeker.peek(filepath, max_chars=4000)
            if not peeked_text:
                peeked_text = "[No readable text streams discovered in document.]"
            textbox.insert("1.0", peeked_text)
            textbox.configure(state="disabled")
        except Exception as e:
            textbox.insert("1.0", f"Document extraction error: {e}")
            textbox.configure(state="disabled")

    def _render_binary(self, parent, filepath: str):
        info_header = ctk.CTkFrame(parent, fg_color="#25262B", height=28)
        info_header.pack(fill="x", padx=6, pady=(6, 2))
        info_header.pack_propagate(False)

        ctk.CTkLabel(
            info_header,
            text="⚙️ Binary File Header (First 512 Bytes Hex Dump)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FFA94D",
        ).pack(side="left", padx=8)

        textbox = ctk.CTkTextbox(
            parent,
            fg_color="#18191D",
            text_color="#CED4DA",
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="none",
        )
        textbox.pack(fill="both", expand=True, padx=6, pady=(2, 6))

        try:
            with open(filepath, "rb") as f:
                data = f.read(512)
            hexdump_text = generate_hexdump(data)
            textbox.insert("1.0", hexdump_text)
            textbox.configure(state="disabled")
        except Exception as e:
            textbox.insert("1.0", f"Binary read error: {e}")
            textbox.configure(state="disabled")

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def _copy_primary_path(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self.filepath)
            self.update()
            messagebox.showinfo("Copied", f"Path copied to clipboard:\n{self.filepath}")
        except Exception as e:
            print(f"Clipboard error: {e}")

    def _reveal_in_explorer(self, filepath: str):
        if not os.path.exists(filepath):
            return
        try:
            if sys.platform == "win32":
                subprocess.Popen(f'explorer /select,"{os.path.normpath(filepath)}"')
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", filepath])
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(filepath)])
        except Exception as e:
            print(f"Reveal error: {e}")

    def _open_system_default(self, filepath: str):
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
            print(f"Open error: {e}")

    def _delete_duplicate_action(self):
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Permanently delete duplicate file:\n{self.filepath}\n\n"
            f"The canonical original at:\n{self.compare_filepath}\nwill be preserved.",
        )
        if not confirm:
            return

        deleted, errors = DeduplicationService.delete_duplicates([self.filepath])
        if deleted > 0:
            messagebox.showinfo("Deleted", "Duplicate file was permanently removed.")
            if self.on_action_performed:
                self.on_action_performed("delete", self.filepath)
            self.destroy()
        else:
            messagebox.showerror("Error", f"Failed to delete duplicate:\n{errors}")

    def _isolate_duplicate_action(self):
        base_dir = os.path.dirname(self.compare_filepath or self.filepath)
        moved, errors = DeduplicationService.isolate_duplicates([self.filepath], base_dir)
        if moved > 0:
            messagebox.showinfo("Isolated", f"Duplicate file moved safely to:\n{base_dir}/_Duplicates/")
            if self.on_action_performed:
                self.on_action_performed("isolate", self.filepath)
            self.destroy()
        else:
            messagebox.showerror("Error", f"Failed to isolate duplicate:\n{errors}")

    def _set_as_original_action(self):
        if not self.compare_filepath:
            return
        confirm = messagebox.askyesno(
            "Set as Original",
            f"Designate this file as the canonical original to KEEP:\n{self.filepath}\n\n"
            f"The previous original:\n{self.compare_filepath}\nwill become a duplicate marked for deletion/isolation.",
        )
        if not confirm:
            return

        if self.on_action_performed:
            self.on_action_performed("set_original", self.filepath)
        messagebox.showinfo(
            "Original Designated",
            f"'{os.path.basename(self.filepath)}' is now designated as the original to keep.\n"
            f"The previous original was marked as duplicate in the list.",
        )
        self.destroy()
