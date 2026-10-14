import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

import json
import threading
import time
import webbrowser
from tkinter import filedialog, messagebox

import customtkinter as ctk

from services import (
    get_FileScanner,
    get_LLMService,
    get_FileExecutor,
    get_provider_registry,
    get_model_downloader,
    get_ollama_manager,
    get_deduplicator,
    get_cleaner_service,
)
from models import FILE_TYPE_CATEGORIES, FileChange
from ui import TreePreviewDialog, DuplicateFinderDialog, JunkCleanerDialog


SETTINGS_FILE = "settings.json"


class NoMoreClutterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("NoMoreClutter 🗂️ - Intelligent AI File Organizer")
        self.geometry("1340x880")
        self.minsize(1080, 680)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        try:
            # Maximizes window gracefully on Windows as user requested
            self.after(100, lambda: self.state("zoomed"))
        except Exception:
            pass
        
        self.source_folder = ""
        self.output_folder = ""
        self.analysis_results = []
        self.created_folders = []
        self.total_files = 0
        self.processed_files = 0
        
        self.quick_deploy_window = None
        self.embed_cancel_event = threading.Event()
        self.ollama_cancel_event = threading.Event()
        
        # AI Connection State Tracking
        self.ai_is_plugged: bool = False
        self.ai_status_badge: str = "Checking"
        self.ai_status_detail: str = "Checking AI status..."
        self.last_benchmark_result = None
        
        self._load_settings()
        self._build_ui()
    
    def _load_settings(self):
        """Load settings with self-healing crash resilience against power loss (PRINCIPLE-012)."""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
            else:
                self.settings = {}
        except json.JSONDecodeError as jde:
            print(f"Warning: Corrupted {SETTINGS_FILE} detected ({jde}). Quarantining corrupted file...")
            try:
                corrupt_backup = f"{SETTINGS_FILE}.corrupt_{int(time.time())}"
                if os.path.exists(SETTINGS_FILE):
                    import shutil
                    shutil.copy2(SETTINGS_FILE, corrupt_backup)
            except Exception:
                pass
            self.settings = {}
        except Exception as e:
            print(f"Warning: Failed to load settings: {e}")
            self.settings = {}
    
    def _save_settings(self, silent: bool = False):
        """Atomically persist settings with buffer flush and fsync (PRINCIPLE-012)."""
        batch_val = str(int(round(float(self.batch_size_slider.get())))) if hasattr(self, "batch_size_slider") else self.batch_size_entry.get().strip()
        limit_val = str(int(round(float(self.limit_slider.get())))) if hasattr(self, "limit_slider") else self.limit_entry.get().strip()
        peek_val = int(round(float(self.peek_length_slider.get()))) if hasattr(self, "peek_length_slider") else int(self.settings.get("peek_length", 180) or 180)
        pacing_val = round(float(self.pacing_slider.get()), 2) if hasattr(self, "pacing_slider") else float(self.settings.get("pacing_delay", 0.2) or 0.2)

        self.settings = {
            "provider_name": self.provider_var.get(),
            "api_key": self.api_key_entry.get().strip(),
            "llm_url": self.llm_url.get().strip(),
            "llm_model": self.llm_model.get().strip(),
            "create_folders": self.create_folders_var.get(),
            "analyze_images": self.analyze_images_var.get(),
            "numbered_rename": self.numbered_rename_var.get(),
            "ai_rename": self.ai_rename_var.get(),
            "content_peeking": self.content_peeking_var.get(),
            "auto_execute": self.auto_execute_var.get(),
            "limit": limit_val,
            "batch_size": batch_val,
            "peek_length": peek_val,
            "pacing_delay": pacing_val,
            "included_categories": {cat: var.get() for cat, var in self.type_vars.items()} if hasattr(self, "type_vars") else {},
        }
        
        # Atomic staging and fsync
        tmp_settings = SETTINGS_FILE + ".tmp"
        try:
            with open(tmp_settings, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except OSError:
                    pass
            os.replace(tmp_settings, SETTINGS_FILE)
        except Exception as e:
            print(f"Error saving settings atomically: {e}")
            try:
                if os.path.exists(tmp_settings):
                    os.remove(tmp_settings)
            except Exception:
                pass

        self._refresh_ai_status_async()
        if not silent:
            messagebox.showinfo("Saved", "Settings saved successfully!")
    
    def _select_all_categories(self):
        for var in self.type_vars.values():
            var.set(True)

    def _deselect_all_categories(self):
        for var in self.type_vars.values():
            var.set(False)

    def _clear_log(self):
        self.output_text.delete("1.0", "end")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # -------------------------------------------------------------
        # 1. Top Navigation & App Header (Full Width Bar)
        # -------------------------------------------------------------
        top_frame = ctk.CTkFrame(self, fg_color="#18191D", corner_radius=10, border_width=1, border_color="#2C2E33")
        top_frame.grid(row=0, column=0, padx=20, pady=(16, 10), sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)

        # Brand / Title Block
        title_box = ctk.CTkFrame(top_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, padx=(18, 10), pady=12, sticky="w")
        
        brand_row = ctk.CTkFrame(title_box, fg_color="transparent")
        brand_row.pack(anchor="w")
        ctk.CTkLabel(brand_row, text="NoMoreClutter 🗂️", font=ctk.CTkFont(size=22, weight="bold"), text_color="#F8F9FA").pack(side="left")
        ctk.CTkLabel(brand_row, text="v2.5 RLM", font=ctk.CTkFont(size=11, weight="bold"), text_color="#74C0FC", fg_color="#182A38", corner_radius=6, padx=6, pady=2).pack(side="left", padx=8)
        
        ctk.CTkLabel(title_box, text="Intelligent AI File Organizer & Storage Reclaimer", text_color="#909296", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(2, 0))

        # Top Right Actions & Tools Bar
        nav_actions = ctk.CTkFrame(top_frame, fg_color="transparent")
        nav_actions.grid(row=0, column=1, padx=(10, 16), pady=12, sticky="e")

        # Utility tools
        self.dup_btn = ctk.CTkButton(
            nav_actions,
            text="🔍 Duplicates",
            command=self._open_duplicate_finder,
            height=34,
            width=120,
            fg_color="#25262B",
            hover_color="#373A40",
            border_width=1,
            border_color="#373A40",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.dup_btn.pack(side="left", padx=5)

        self.clean_btn = ctk.CTkButton(
            nav_actions,
            text="🧹 Clean Junk",
            command=self._open_junk_cleaner,
            height=34,
            width=115,
            fg_color="#25262B",
            hover_color="#373A40",
            border_width=1,
            border_color="#373A40",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.clean_btn.pack(side="left", padx=5)

        # AI Status Pill Button (interactive)
        self.ai_status_btn = ctk.CTkButton(
            nav_actions,
            text="🟡 Checking AI...",
            command=self._on_ai_status_clicked,
            height=34,
            corner_radius=17,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2B2D31",
            hover_color="#3E4249",
            text_color="#FCC419",
            border_width=1,
            border_color="#5C5F66",
        )
        self.ai_status_btn.pack(side="left", padx=6)

        deploy_btn = ctk.CTkButton(
            nav_actions,
            text="🚀 1-Click AI Deploy",
            width=150,
            height=34,
            fg_color="#E8590C",
            hover_color="#D9480F",
            command=self._open_quick_deploy,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        deploy_btn.pack(side="left", padx=5)

        settings_btn = ctk.CTkButton(
            nav_actions,
            text="⚙ Settings",
            width=100,
            height=34,
            fg_color="#373A40",
            hover_color="#2C2E33",
            command=self._open_settings,
            font=ctk.CTkFont(size=12),
        )
        settings_btn.pack(side="left", padx=(5, 0))

        # -------------------------------------------------------------
        # 2. Main Two-Column Content Workspace
        # -------------------------------------------------------------
        workspace_grid = ctk.CTkFrame(self, fg_color="transparent")
        workspace_grid.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="nsew")
        workspace_grid.grid_columnconfigure(0, weight=0, minsize=480)
        workspace_grid.grid_columnconfigure(1, weight=1)
        workspace_grid.grid_rowconfigure(0, weight=1)

        # =============================================================
        # LEFT COLUMN: Controls & Configurations
        # =============================================================
        left_scroll = ctk.CTkScrollableFrame(workspace_grid, width=480, fg_color="transparent")
        left_scroll.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_scroll.grid_columnconfigure(0, weight=1)

        # Card 1: 📁 Directory Paths
        folders_frame = ctk.CTkFrame(left_scroll, fg_color="#1A1B1E", corner_radius=10, border_width=1, border_color="#2C2E33")
        folders_frame.pack(fill="x", pady=(0, 10))
        folders_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(folders_frame, text="📁 Directory Paths", font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8F9FA").grid(row=0, column=0, columnspan=3, padx=16, pady=(14, 6), sticky="w")
        
        # Source row
        ctk.CTkLabel(folders_frame, text="Source Folder (files to organize):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#ADB5BD").grid(row=1, column=0, columnspan=3, padx=16, pady=(4, 2), sticky="w")
        self.source_entry = ctk.CTkEntry(folders_frame, height=36, font=ctk.CTkFont(size=12))
        self.source_entry.grid(row=2, column=0, columnspan=2, padx=(16, 6), pady=(0, 6), sticky="ew")
        ctk.CTkButton(folders_frame, text="Browse", width=85, height=36, command=self._select_source, font=ctk.CTkFont(size=12)).grid(row=2, column=2, padx=(0, 16), pady=(0, 6))

        # Output row
        ctk.CTkLabel(folders_frame, text="Destination Folder (organized output):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#ADB5BD").grid(row=3, column=0, columnspan=3, padx=16, pady=(6, 2), sticky="w")
        self.output_entry = ctk.CTkEntry(folders_frame, height=36, font=ctk.CTkFont(size=12))
        self.output_entry.grid(row=4, column=0, columnspan=2, padx=(16, 6), pady=(0, 8), sticky="ew")
        ctk.CTkButton(folders_frame, text="Browse", width=85, height=36, command=self._select_output, font=ctk.CTkFont(size=12)).grid(row=4, column=2, padx=(0, 16), pady=(0, 8))

        # Folder info labels
        self.folder_info_label = ctk.CTkLabel(folders_frame, text="", text_color="#74C0FC", font=ctk.CTkFont(size=12))
        self.folder_info_label.grid(row=5, column=0, columnspan=3, padx=16, pady=(0, 4), sticky="w")
        
        self.existing_folders_label = ctk.CTkLabel(folders_frame, text="", text_color="#868E96", font=ctk.CTkFont(size=11), wraplength=440, justify="left")
        self.existing_folders_label.grid(row=6, column=0, columnspan=3, padx=16, pady=(0, 14), sticky="w")

        # Card 2: 📋 File Categories to Include
        file_types_frame = ctk.CTkFrame(left_scroll, fg_color="#1A1B1E", corner_radius=10, border_width=1, border_color="#2C2E33")
        file_types_frame.pack(fill="x", pady=10)
        file_types_frame.grid_columnconfigure((0, 1), weight=1)

        cats_header = ctk.CTkFrame(file_types_frame, fg_color="transparent")
        cats_header.grid(row=0, column=0, columnspan=2, padx=16, pady=(14, 8), sticky="ew")

        ctk.CTkLabel(cats_header, text="📋 Categories to Include", font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8F9FA").pack(side="left")

        # Quick select / deselect links
        ctk.CTkButton(cats_header, text="None", width=45, height=22, fg_color="#2C2E33", hover_color="#373A40", font=ctk.CTkFont(size=10), command=self._deselect_all_categories).pack(side="right", padx=(4, 0))
        ctk.CTkButton(cats_header, text="All", width=40, height=22, fg_color="#2C2E33", hover_color="#373A40", font=ctk.CTkFont(size=10), command=self._select_all_categories).pack(side="right")

        saved_cats = self.settings.get("included_categories", {})
        self.type_vars = {}
        for i, (category, extensions) in enumerate(FILE_TYPE_CATEGORIES.items()):
            is_enabled = saved_cats.get(category, True)
            self.type_vars[category] = ctk.BooleanVar(value=is_enabled)
            ext_display = ", ".join(extensions[:3]) + ("..." if len(extensions) > 3 else "")
            cb = ctk.CTkCheckBox(file_types_frame, text=f"{category} ({ext_display})", variable=self.type_vars[category], font=ctk.CTkFont(size=11))
            cb.grid(row=1 + (i // 2), column=i % 2, padx=16, pady=5, sticky="w")

        ctk.CTkFrame(file_types_frame, height=8, fg_color="transparent").grid(row=99, column=0, columnspan=2)

        # Card 3: ⚡ Organization Control Center
        actions_frame = ctk.CTkFrame(left_scroll, fg_color="#1A1B1E", corner_radius=10, border_width=1, border_color="#2C2E33")
        actions_frame.pack(fill="x", pady=10)
        actions_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(actions_frame, text="⚡ Organization Control Center", font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8F9FA").grid(row=0, column=0, columnspan=2, padx=16, pady=(14, 8), sticky="w")

        # Primary Trigger Buttons
        self.analyze_btn = ctk.CTkButton(
            actions_frame,
            text="🔍 AI Organize",
            command=self._analyze,
            height=46,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1971C2",
            hover_color="#1864AB",
        )
        self.analyze_btn.grid(row=1, column=0, padx=(16, 6), pady=6, sticky="ew")

        self.quick_btn = ctk.CTkButton(
            actions_frame,
            text="⚡ Quick Organize (No AI)",
            command=self._quick_organize,
            height=46,
            fg_color="#0C8599",
            hover_color="#0B7285",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.quick_btn.grid(row=1, column=1, padx=(6, 16), pady=6, sticky="ew")

        # Execution & Undo Buttons
        self.execute_btn = ctk.CTkButton(
            actions_frame,
            text="🗂️ Preview & Execute",
            command=self._execute,
            height=42,
            state="disabled",
            fg_color="#2B8A3E",
            hover_color="#237032",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.execute_btn.grid(row=2, column=0, padx=(16, 6), pady=6, sticky="ew")

        self.undo_btn = ctk.CTkButton(
            actions_frame,
            text="↩ Undo Moves",
            command=self._undo_moves,
            height=42,
            state="disabled",
            fg_color="#495057",
            hover_color="#343A40",
            font=ctk.CTkFont(size=13),
        )
        self.undo_btn.grid(row=2, column=1, padx=(6, 16), pady=6, sticky="ew")

        # Real-time Status Card row
        status_box = ctk.CTkFrame(actions_frame, fg_color="#141517", corner_radius=6, border_width=1, border_color="#25262B")
        status_box.grid(row=3, column=0, columnspan=2, padx=16, pady=(10, 16), sticky="ew")

        self.ai_plug_indicator = ctk.CTkLabel(
            status_box,
            text="⚪ Checking AI",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray",
            padx=10,
        )
        self.ai_plug_indicator.pack(side="left", padx=4, pady=8)

        self.status_label = ctk.CTkLabel(
            status_box,
            text="Select source folder to begin",
            text_color="gray",
            font=ctk.CTkFont(size=12),
        )
        self.status_label.pack(side="left", padx=6, pady=8, fill="x", expand=True)

        # =============================================================
        # RIGHT COLUMN: Live Activity Stream & Terminal
        # =============================================================
        output_frame = ctk.CTkFrame(workspace_grid, fg_color="#1A1B1E", corner_radius=10, border_width=1, border_color="#2C2E33")
        output_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_rowconfigure(1, weight=1)

        # Console Header Bar
        console_hdr = ctk.CTkFrame(output_frame, fg_color="transparent")
        console_hdr.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="ew")
        console_hdr.grid_columnconfigure(1, weight=1)

        self.output_header = ctk.CTkLabel(
            console_hdr,
            text="📝 Activity Stream & Real-Time Terminal",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F8F9FA",
        )
        self.output_header.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            console_hdr,
            text="Clear Log",
            width=80,
            height=26,
            fg_color="#2C2E33",
            hover_color="#373A40",
            font=ctk.CTkFont(size=11),
            command=self._clear_log,
        ).grid(row=0, column=2, sticky="e")

        # Console Textbox
        self.output_text = ctk.CTkTextbox(
            output_frame,
            wrap="none",
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#101113",
            border_width=1,
            border_color="#25262B",
            corner_radius=6,
        )
        self.output_text.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="nsew")

        # Check for persistent undo operations from previous sessions (Option 2)
        FileExecutor = get_FileExecutor()
        if FileExecutor.has_undo():
            self.undo_btn.configure(state="normal")
            summaries = FileExecutor.get_history_summary()
            if summaries:
                last_batch = summaries[0]
                self.output_text.insert("end", f"ℹ️ Multi-session Undo: {last_batch['count']} files from previous run ({last_batch['timestamp_str']}) can be undone with '↩ Undo Moves'.\n\n")

        self._build_settings_window()
        self._refresh_ai_status_async()

    def _build_settings_window(self):
        _, _, _, list_names, _ = get_provider_registry()
        provider_names = list_names()
        
        default_provider = self.settings.get("provider_name", "Groq (Free & Fastest - Zero Install)")
        if default_provider not in provider_names:
            default_provider = provider_names[0]

        self.settings_window = ctk.CTkToplevel(self)
        self.settings_window.title("NoMoreClutter - Settings")
        self.settings_window.geometry("640x680")
        self.settings_window.withdraw()
        self.settings_window.protocol("WM_DELETE_WINDOW", self._hide_settings)
        
        scroll = ctk.CTkScrollableFrame(self.settings_window, label_text="⚙ Configuration & AI Providers")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Quick Deploy Shortcut Card
        deploy_card = ctk.CTkFrame(scroll, fg_color="#1A1D20", corner_radius=8, border_width=1, border_color="#D9480F")
        deploy_card.pack(fill="x", padx=10, pady=(10, 15))
        ctk.CTkLabel(deploy_card, text="🚀 Need a model? 1-Click Auto-Deploy", font=ctk.CTkFont(weight="bold", size=13), text_color="#FFA94D").pack(padx=12, pady=(10, 2), anchor="w")
        ctk.CTkLabel(deploy_card, text="Automatically download an embedded GGUF model, pull into Ollama, or connect free cloud AI in 1 click.", text_color="gray", font=ctk.CTkFont(size=11)).pack(padx=12, pady=(0, 8), anchor="w")
        ctk.CTkButton(deploy_card, text="🚀 Open 1-Click Quick Deploy", command=self._open_quick_deploy, height=32, fg_color="#D9480F", hover_color="#C92A2A", font=ctk.CTkFont(weight="bold")).pack(padx=12, pady=(0, 10), anchor="w")
        
        # Section 1: Provider Selection
        ctk.CTkLabel(scroll, text="🤖 AI Provider Selection (Zero-Install or Local)", font=ctk.CTkFont(weight="bold", size=14)).pack(padx=10, pady=(10, 4), anchor="w")
        ctk.CTkLabel(scroll, text="Choose a cloud zero-install provider (no app download) or your local server:", text_color="gray", font=ctk.CTkFont(size=12)).pack(padx=10, pady=(0, 8), anchor="w")
        
        self.provider_var = ctk.StringVar(value=default_provider)
        self.provider_menu = ctk.CTkOptionMenu(
            scroll,
            values=provider_names,
            variable=self.provider_var,
            command=self._on_provider_changed,
            width=540,
            height=36
        )
        self.provider_menu.pack(padx=10, pady=5, anchor="w")
        
        # Provider Description
        self.provider_desc_label = ctk.CTkLabel(scroll, text="", text_color="cyan", font=ctk.CTkFont(size=12), wraplength=520, justify="left")
        self.provider_desc_label.pack(padx=10, pady=(2, 10), anchor="w")
        
        # API Key Section
        self.key_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.key_frame.pack(fill="x", padx=10, pady=5)
        
        self.key_label = ctk.CTkLabel(self.key_frame, text="API Key:", font=ctk.CTkFont(weight="bold"))
        self.key_label.pack(side="left", padx=(0, 10))
        
        self.api_key_entry = ctk.CTkEntry(self.key_frame, width=360, show="*")
        self.api_key_entry.insert(0, self.settings.get("api_key", ""))
        self.api_key_entry.pack(side="left", padx=5)
        
        self.show_key_var = ctk.BooleanVar(value=False)
        self.show_key_cb = ctk.CTkCheckBox(self.key_frame, text="Show", variable=self.show_key_var, command=self._toggle_show_key, width=60)
        self.show_key_cb.pack(side="left", padx=5)
        
        self.signup_btn = ctk.CTkButton(scroll, text="🔗 Get Free API Key", command=self._open_signup_url, height=28, fg_color="#1F6AA5")
        self.signup_btn.pack(padx=10, pady=(0, 10), anchor="w")
        
        # Endpoint & Model fields
        ctk.CTkLabel(scroll, text="API Base URL:").pack(padx=10, pady=(8, 0), anchor="w")
        self.llm_url = ctk.CTkEntry(scroll, width=540)
        self.llm_url.insert(0, self.settings.get("llm_url", "https://api.groq.com/openai/v1"))
        self.llm_url.pack(padx=10, pady=5, anchor="w")
        
        ctk.CTkLabel(scroll, text="Model Identifier:").pack(padx=10, pady=(8, 0), anchor="w")
        self.llm_model = ctk.CTkEntry(scroll, width=350)
        self.llm_model.insert(0, self.settings.get("llm_model", "llama-3.3-70b-versatile"))
        self.llm_model.pack(padx=10, pady=5, anchor="w")
        
        # Section 2: Organization Options
        ctk.CTkLabel(scroll, text="📁 Organization Options", font=ctk.CTkFont(weight="bold", size=14)).pack(padx=10, pady=(20, 5), anchor="w")
        
        self.create_folders_var = ctk.BooleanVar(value=self.settings.get("create_folders", True))
        ctk.CTkCheckBox(scroll, text="Create new semantic folders (e.g. 'Work_Invoices', 'Family_Photos')", variable=self.create_folders_var).pack(padx=10, pady=4, anchor="w")
        
        self.analyze_images_var = ctk.BooleanVar(value=self.settings.get("analyze_images", False))
        self.analyze_images_cb = ctk.CTkCheckBox(
            scroll,
            text="Analyze image contents using AI Vision (requires vision-capable model)",
            variable=self.analyze_images_var,
            command=self._on_vision_toggled,
        )
        self.analyze_images_cb.pack(padx=10, pady=4, anchor="w")
        
        self.ai_rename_var = ctk.BooleanVar(value=self.settings.get("ai_rename", True))
        ctk.CTkCheckBox(scroll, text="Let AI suggest descriptive filenames based on content", variable=self.ai_rename_var).pack(padx=10, pady=4, anchor="w")
        
        self.numbered_rename_var = ctk.BooleanVar(value=self.settings.get("numbered_rename", False))
        ctk.CTkCheckBox(scroll, text="Rename files sequentially (1.jpg, 2.jpg...)", variable=self.numbered_rename_var).pack(padx=10, pady=4, anchor="w")
        
        self.content_peeking_var = ctk.BooleanVar(value=self.settings.get("content_peeking", True))
        ctk.CTkCheckBox(scroll, text="Peek inside documents (PDF, DOCX, TXT) for intelligent content-based categorization", variable=self.content_peeking_var).pack(padx=10, pady=4, anchor="w")
        
        # Section 3: Performance, Context & Continuous Sliders
        ctk.CTkLabel(scroll, text="⚡ Performance, Context & Continuous Sliders", font=ctk.CTkFont(weight="bold", size=14)).pack(padx=10, pady=(20, 5), anchor="w")
        ctk.CTkLabel(scroll, text="Fine-tune performance sliders manually or click 'Run Auto-Benchmark' below to calibrate automatically:", font=ctk.CTkFont(size=12), text_color="gray").pack(padx=10, pady=(0, 6), anchor="w")
        
        self.auto_execute_var = ctk.BooleanVar(value=self.settings.get("auto_execute", False))
        ctk.CTkCheckBox(scroll, text="Auto-execute moves immediately without confirmation dialog", variable=self.auto_execute_var).pack(padx=10, pady=(0, 10), anchor="w")

        # Synchronized companion entry boxes for API compatibility
        self.batch_size_entry = ctk.CTkEntry(scroll)
        self.limit_entry = ctk.CTkEntry(scroll)

        # 1. RLM Cluster Batch Size Slider
        initial_batch = int(self.settings.get("batch_size", "15") or 15)
        initial_batch = max(1, min(30, initial_batch))

        batch_head = ctk.CTkFrame(scroll, fg_color="transparent")
        batch_head.pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkLabel(batch_head, text="📦 RLM Cluster Batch Size:", font=ctk.CTkFont(weight="bold")).pack(side="left")
        self.batch_size_label = ctk.CTkLabel(batch_head, text=f"{initial_batch} files/cluster", font=ctk.CTkFont(weight="bold"), text_color="#74C0FC")
        self.batch_size_label.pack(side="right")

        self.batch_size_slider = ctk.CTkSlider(
            scroll,
            from_=1,
            to=30,
            number_of_steps=29,
            command=self._on_batch_size_slider_changed,
            height=18
        )
        self.batch_size_slider.set(initial_batch)
        self.batch_size_slider.pack(fill="x", padx=10, pady=(0, 2))
        ctk.CTkLabel(scroll, text="Number of files grouped per AI prompt. Higher is faster; lower saves GPU/CPU RAM.", font=ctk.CTkFont(size=11), text_color="gray").pack(padx=10, pady=(0, 8), anchor="w")

        # 2. Max Files Limit Slider
        initial_limit = int(self.settings.get("limit", "50") or 50)
        initial_limit = max(0, min(250, initial_limit))

        limit_head = ctk.CTkFrame(scroll, fg_color="transparent")
        limit_head.pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkLabel(limit_head, text="📊 Max Files to Process:", font=ctk.CTkFont(weight="bold")).pack(side="left")
        limit_text = "0 (Unlimited)" if initial_limit == 0 else f"{initial_limit} files"
        self.limit_label = ctk.CTkLabel(limit_head, text=limit_text, font=ctk.CTkFont(weight="bold"), text_color="#74C0FC")
        self.limit_label.pack(side="right")

        self.limit_slider = ctk.CTkSlider(
            scroll,
            from_=0,
            to=250,
            number_of_steps=50,
            command=self._on_limit_slider_changed,
            height=18
        )
        self.limit_slider.set(initial_limit)
        self.limit_slider.pack(fill="x", padx=10, pady=(0, 2))
        ctk.CTkLabel(scroll, text="Processing limit per run. Slide to 0 for unlimited file processing.", font=ctk.CTkFont(size=11), text_color="gray").pack(padx=10, pady=(0, 8), anchor="w")

        # 3. Document Peeking Context Budget Slider
        initial_peek = int(self.settings.get("peek_length", 180) or 180)
        initial_peek = max(50, min(350, initial_peek))

        peek_head = ctk.CTkFrame(scroll, fg_color="transparent")
        peek_head.pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkLabel(peek_head, text="📄 Document Peek Snippet Length:", font=ctk.CTkFont(weight="bold")).pack(side="left")
        self.peek_length_label = ctk.CTkLabel(peek_head, text=f"{initial_peek} chars", font=ctk.CTkFont(weight="bold"), text_color="#74C0FC")
        self.peek_length_label.pack(side="right")

        self.peek_length_slider = ctk.CTkSlider(
            scroll,
            from_=50,
            to=350,
            number_of_steps=30,
            command=self._on_peek_length_slider_changed,
            height=18
        )
        self.peek_length_slider.set(initial_peek)
        self.peek_length_slider.pack(fill="x", padx=10, pady=(0, 2))
        ctk.CTkLabel(scroll, text="Snippet character preview length extracted from PDFs, Word docs, and text.", font=ctk.CTkFont(size=11), text_color="gray").pack(padx=10, pady=(0, 8), anchor="w")

        # 4. Inter-Batch Pacing Delay Slider
        initial_pacing = float(self.settings.get("pacing_delay", 0.2) or 0.2)
        initial_pacing = max(0.0, min(2.0, initial_pacing))

        pacing_head = ctk.CTkFrame(scroll, fg_color="transparent")
        pacing_head.pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkLabel(pacing_head, text="⏱️ Inter-Batch Request Pacing Delay:", font=ctk.CTkFont(weight="bold")).pack(side="left")
        self.pacing_label = ctk.CTkLabel(pacing_head, text=f"{initial_pacing:.2f}s delay", font=ctk.CTkFont(weight="bold"), text_color="#74C0FC")
        self.pacing_label.pack(side="right")

        self.pacing_slider = ctk.CTkSlider(
            scroll,
            from_=0.0,
            to=2.0,
            number_of_steps=20,
            command=self._on_pacing_slider_changed,
            height=18
        )
        self.pacing_slider.set(initial_pacing)
        self.pacing_slider.pack(fill="x", padx=10, pady=(0, 2))
        ctk.CTkLabel(scroll, text="Pause between cluster batches. 0.0s for cloud; 0.15s-0.4s for free-tier TPM or local CPU.", font=ctk.CTkFont(size=11), text_color="gray").pack(padx=10, pady=(0, 12), anchor="w")

        # Pre-populate companion entries
        self.batch_size_entry.insert(0, str(initial_batch))
        self.limit_entry.insert(0, str(initial_limit))

        # Auto-Tune & Hardware Benchmark Card (Tests PC latency & finds optimal settings)
        benchmark_card = ctk.CTkFrame(scroll, fg_color="#181B1F", corner_radius=8, border_width=1, border_color="#3B8ED0")
        benchmark_card.pack(fill="x", padx=10, pady=(15, 10))
        
        ctk.CTkLabel(benchmark_card, text="⚡ Auto-Tune Optimal Settings & Hardware Benchmark", font=ctk.CTkFont(weight="bold", size=13), text_color="#74C0FC").pack(padx=12, pady=(10, 2), anchor="w")
        ctk.CTkLabel(benchmark_card, text="Automatically tests your PC and active AI model with realistic test files. Measures latency, evaluates Vision capabilities, and determines the most optimal batch size and limits for your hardware.", text_color="gray", font=ctk.CTkFont(size=11), wraplength=520, justify="left").pack(padx=12, pady=(0, 8), anchor="w")
        
        bench_btn_row = ctk.CTkFrame(benchmark_card, fg_color="transparent")
        bench_btn_row.pack(fill="x", padx=12, pady=(0, 8))
        
        self.benchmark_run_btn = ctk.CTkButton(bench_btn_row, text="⚡ Run Auto-Benchmark & Tune", command=self._run_benchmark_action, height=32, fg_color="#1971C2", hover_color="#1864AB", font=ctk.CTkFont(weight="bold"))
        self.benchmark_run_btn.pack(side="left")
        
        self.benchmark_apply_btn = ctk.CTkButton(bench_btn_row, text="✨ Apply Recommended Settings", command=self._apply_benchmark_settings, height=32, state="disabled", fg_color="#2B8A3E", hover_color="#237032", font=ctk.CTkFont(weight="bold"))
        self.benchmark_apply_btn.pack(side="left", padx=(10, 0))
        
        self.benchmark_progress_bar = ctk.CTkProgressBar(benchmark_card, height=6)
        self.benchmark_progress_bar.set(0.0)
        self.benchmark_progress_bar.pack(fill="x", padx=12, pady=(4, 4))
        
        self.benchmark_status_label = ctk.CTkLabel(benchmark_card, text="Ready to benchmark active model.", text_color="gray", font=ctk.CTkFont(size=11))
        self.benchmark_status_label.pack(padx=12, pady=(0, 4), anchor="w")
        
        self.benchmark_results_box = ctk.CTkTextbox(benchmark_card, height=130, wrap="word", font=ctk.CTkFont(family="Consolas", size=11))
        self.benchmark_results_box.pack(fill="x", padx=12, pady=(0, 10))
        self.benchmark_results_box.insert("end", "Click 'Run Auto-Benchmark' to measure PC latency and determine optimal settings.\n")

        # Action Buttons
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=20)
        
        ctk.CTkButton(btn_row, text="💾 Save Settings", command=self._save_settings, height=38, width=140).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="🔗 Test Connection", command=self._test_connection, height=38, width=140, fg_color="#2B8A3E").pack(side="left", padx=5)
        
        self.connection_status = ctk.CTkLabel(scroll, text="", text_color="gray", wraplength=520, justify="left")
        self.connection_status.pack(padx=10, pady=5, anchor="w")
        
        # Initialize provider presets state
        self._update_provider_ui(self.provider_var.get(), force_defaults=False)

    def _on_batch_size_slider_changed(self, value):
        val_int = int(round(float(value)))
        if hasattr(self, "batch_size_label"):
            self.batch_size_label.configure(text=f"{val_int} files/cluster")
        if hasattr(self, "batch_size_entry"):
            self.batch_size_entry.delete(0, "end")
            self.batch_size_entry.insert(0, str(val_int))

    def _on_limit_slider_changed(self, value):
        val_int = int(round(float(value)))
        txt = "0 (Unlimited)" if val_int == 0 else f"{val_int} files"
        if hasattr(self, "limit_label"):
            self.limit_label.configure(text=txt)
        if hasattr(self, "limit_entry"):
            self.limit_entry.delete(0, "end")
            self.limit_entry.insert(0, str(val_int))

    def _on_peek_length_slider_changed(self, value):
        val_int = int(round(float(value)))
        if hasattr(self, "peek_length_label"):
            self.peek_length_label.configure(text=f"{val_int} chars")

    def _on_pacing_slider_changed(self, value):
        val_float = round(float(value), 2)
        if hasattr(self, "pacing_label"):
            self.pacing_label.configure(text=f"{val_float:.2f}s delay")

    def _on_provider_changed(self, choice):
        self._update_provider_ui(choice, force_defaults=True)
        self._refresh_ai_status_async()

    def _update_provider_ui(self, provider_name: str, force_defaults: bool = False):
        _, _, get_by_name, _, _ = get_provider_registry()
        preset = get_by_name(provider_name)
        if not preset:
            return

        self.provider_desc_label.configure(text=f"ℹ️ {preset.description}")
        
        # Update URL and Model if requested (e.g. user selected new preset) or if currently empty
        current_url = self.llm_url.get().strip()
        if force_defaults or not current_url:
            self.llm_url.delete(0, "end")
            self.llm_url.insert(0, preset.base_url)
        
        current_model = self.llm_model.get().strip()
        if force_defaults or not current_model:
            model_to_use = (preset.vision_model if (self.analyze_images_var.get() and preset.vision_model) else preset.default_model)
            self.llm_model.delete(0, "end")
            self.llm_model.insert(0, model_to_use)

        # Update Vision checkbox state according to preset capabilities
        if hasattr(self, "analyze_images_cb"):
            if not preset.vision_model:
                self.analyze_images_cb.configure(
                    state="disabled",
                    text="Analyze image contents using AI Vision (Disabled: Embedded/Text models only support text)"
                )
                self.analyze_images_var.set(False)
            else:
                self.analyze_images_cb.configure(
                    state="normal",
                    text="Analyze image contents using AI Vision (requires vision-capable model)"
                )
        
        if preset.requires_api_key:
            self.key_label.configure(text="API Key (Required):", text_color="#FFA94D")
            self.signup_btn.configure(state="normal", text=f"🔗 Get Free API Key for {preset.name.split('(')[0].strip()}")
        else:
            self.key_label.configure(text="API Key (Optional):", text_color="gray")
            self.signup_btn.configure(state="disabled", text="No API Key Required")

    def _on_vision_toggled(self):
        _, _, get_by_name, _, _ = get_provider_registry()
        preset = get_by_name(self.provider_var.get())
        if preset:
            if self.analyze_images_var.get() and not preset.vision_model:
                self.analyze_images_var.set(False)
                messagebox.showinfo(
                    "Vision Not Supported",
                    f"'{preset.name}' is a text-focused model and does not support image vision analysis directly.\n\n"
                    "For multimodal image vision analysis, please select Groq (llama-3.2-11b-vision) or Google Gemini in the Provider dropdown.",
                )
                return
            model_to_use = (preset.vision_model if (self.analyze_images_var.get() and preset.vision_model) else preset.default_model)
            self.llm_model.delete(0, "end")
            self.llm_model.insert(0, model_to_use)
            self._refresh_ai_status_async()

    def _toggle_show_key(self):
        show_char = "" if self.show_key_var.get() else "*"
        self.api_key_entry.configure(show=show_char)

    def _open_signup_url(self):
        _, _, get_by_name, _, _ = get_provider_registry()
        preset = get_by_name(self.provider_var.get())
        if preset and preset.signup_url:
            webbrowser.open(preset.signup_url)

    def _test_connection(self):
        self.connection_status.configure(text="Testing connection...", text_color="yellow")
        self.update()
        
        try:
            _, _, get_by_name, _, _ = get_provider_registry()
            preset = get_by_name(self.provider_var.get())
            provider_id = preset.id if preset else ("embedded" if self.llm_url.get().strip() == "local://embedded" else "custom")
            model_name = self.llm_model.get().strip()

            LLMService, _ = get_LLMService()
            llm = LLMService(
                base_url=self.llm_url.get().strip(),
                api_key=self.api_key_entry.get().strip(),
                provider_id=provider_id,
                model=model_name,
            )
            success, msg = llm.test_connection(model_name)
            if success:
                self.connection_status.configure(text=f"✅ {msg}", text_color="#51CF66")
            else:
                self.connection_status.configure(text=f"❌ {msg}", text_color="#FF6B6B")
        except Exception as e:
            self.connection_status.configure(text=f"❌ Error: {str(e)}", text_color="#FF6B6B")
        finally:
            self._refresh_ai_status_async()

    def _refresh_ai_status_async(self):
        """Non-blocking background check of whether current AI provider is plugged in (PRINCIPLE-007)."""
        if hasattr(self, "ai_status_btn"):
            self.ai_status_btn.configure(
                text="🟡 Checking AI...",
                fg_color="#2B2514",
                hover_color="#3D351D",
                text_color="#FCC419",
                border_color="#FAB005",
            )
        if hasattr(self, "ai_plug_indicator"):
            self.ai_plug_indicator.configure(text="🟡 Checking AI", text_color="#FCC419")

        thread = threading.Thread(target=self._ai_status_worker, daemon=True)
        thread.start()

    def _ai_status_worker(self):
        try:
            provider_name = (
                self.provider_var.get()
                if hasattr(self, "provider_var")
                else self.settings.get("provider_name", "Groq (Free & Fastest - Zero Install)")
            )
            api_key = (
                self.api_key_entry.get().strip()
                if hasattr(self, "api_key_entry")
                else self.settings.get("api_key", "")
            )
            base_url = (
                self.llm_url.get().strip()
                if hasattr(self, "llm_url")
                else self.settings.get("llm_url", "")
            )
            model = (
                self.llm_model.get().strip()
                if hasattr(self, "llm_model")
                else self.settings.get("llm_model", "")
            )

            LLMService, _ = get_LLMService()
            is_plugged, badge_label, detail_msg = LLMService.check_ai_status(
                provider_name=provider_name,
                base_url=base_url,
                api_key=api_key,
                model=model,
            )
            self.after(0, self._apply_ai_status_ui, is_plugged, badge_label, detail_msg)
        except Exception as e:
            self.after(0, self._apply_ai_status_ui, False, "Check Failed", str(e))

    def _apply_ai_status_ui(self, is_plugged: bool, badge_label: str, detail_msg: str):
        self.ai_is_plugged = is_plugged
        self.ai_status_badge = badge_label
        self.ai_status_detail = detail_msg

        if not hasattr(self, "ai_status_btn"):
            return

        if is_plugged:
            self.ai_status_btn.configure(
                text=f"🟢 AI Plugged: {badge_label}",
                fg_color="#142B1A",
                hover_color="#1E3F27",
                text_color="#51CF66",
                border_color="#2B8A3E",
            )
            if hasattr(self, "ai_plug_indicator"):
                self.ai_plug_indicator.configure(text=f"🟢 {badge_label}", text_color="#51CF66")
        else:
            self.ai_status_btn.configure(
                text=f"🔴 AI Unplugged ({badge_label})",
                fg_color="#2B1414",
                hover_color="#421E1E",
                text_color="#FF8787",
                border_color="#E03131",
            )
            if hasattr(self, "ai_plug_indicator"):
                self.ai_plug_indicator.configure(text="🔴 AI Unplugged", text_color="#FF8787")

    def _on_ai_status_clicked(self):
        """Handle user clicks on the interactive AI status indicator pill."""
        if self.ai_is_plugged:
            msg = (
                f"✅ AI Connection Status: PLUGGED & READY\n\n"
                f"Provider: {self.ai_status_badge}\n"
                f"Details: {self.ai_status_detail}\n\n"
                "Would you like to re-test the AI connection now?"
            )
            retest = messagebox.askyesno("AI Status - Plugged & Online", msg)
            if retest:
                self._refresh_ai_status_async()
        else:
            msg = (
                f"⚠️ AI Connection Status: UNPLUGGED\n\n"
                f"Reason: {self.ai_status_detail}\n\n"
                "To organize files using AI, choose one of these options:\n"
                "• Click 'Yes' to open 1-Click AI Deploy (download offline GGUF, pull Ollama, or get free Groq/Gemini key).\n"
                "• Click 'No' to open Settings and manually enter API keys or endpoint URLs.\n"
                "• Or use '⚡ Quick Organize (No AI)' on the main screen to organize without AI."
            )
            choice = messagebox.askyesno("AI Status - Unplugged", msg)
            if choice:
                self._open_quick_deploy()
            else:
                self._open_settings()

    def _run_benchmark_action(self):
        """Start asynchronous model benchmarking on synthetic test files (PRINCIPLE-007)."""
        self.benchmark_run_btn.configure(state="disabled")
        self.benchmark_apply_btn.configure(state="disabled")
        self.benchmark_progress_bar.set(0.05)
        self.benchmark_status_label.configure(text="Initializing test files & hardware probe...", text_color="yellow")
        self.benchmark_results_box.delete("1.0", "end")
        self.benchmark_results_box.insert("end", "⏳ Benchmarking in progress... Testing latency, compliance, and vision capability.\n")

        thread = threading.Thread(target=self._benchmark_worker, daemon=True)
        thread.start()

    def _benchmark_worker(self):
        try:
            provider_name = (
                self.provider_var.get()
                if hasattr(self, "provider_var")
                else self.settings.get("provider_name", "Groq (Free & Fastest - Zero Install)")
            )
            api_key = (
                self.api_key_entry.get().strip()
                if hasattr(self, "api_key_entry")
                else self.settings.get("api_key", "")
            )
            base_url = (
                self.llm_url.get().strip()
                if hasattr(self, "llm_url")
                else self.settings.get("llm_url", "")
            )
            model = (
                self.llm_model.get().strip()
                if hasattr(self, "llm_model")
                else self.settings.get("llm_model", "")
            )

            LLMService, _ = get_LLMService()
            llm = LLMService(base_url=base_url, api_key=api_key)

            from services.benchmark_service import BenchmarkService

            def prog_cb(msg: str, val: float):
                self.after(0, self._update_benchmark_progress_ui, msg, val)

            result = BenchmarkService.run_benchmark(
                provider=llm.provider,
                model=model,
                provider_name=provider_name,
                progress_callback=prog_cb,
            )
            self.after(0, self._on_benchmark_complete, result)
        except Exception as e:
            self.after(0, self._on_benchmark_error, str(e))

    def _update_benchmark_progress_ui(self, msg: str, val: float):
        if hasattr(self, "benchmark_progress_bar"):
            self.benchmark_progress_bar.set(val)
        if hasattr(self, "benchmark_status_label"):
            self.benchmark_status_label.configure(text=msg, text_color="yellow")

    def _on_benchmark_complete(self, result):
        self.last_benchmark_result = result
        self.benchmark_run_btn.configure(state="normal")
        self.benchmark_apply_btn.configure(state="normal")
        self.benchmark_progress_bar.set(1.0)
        self.benchmark_status_label.configure(text="✅ Benchmark complete! Optimal slider settings ready to apply.", text_color="#51CF66")

        self.benchmark_results_box.delete("1.0", "end")
        self.benchmark_results_box.insert("end", f"📊 HARDWARE & MODEL BENCHMARK REPORT\n")
        self.benchmark_results_box.insert("end", f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        self.benchmark_results_box.insert("end", f"• Tier: {result.hardware_tier}\n")
        self.benchmark_results_box.insert("end", f"• Latency: {result.latency_ms:.0f} ms (~{result.tokens_per_sec:.0f} tokens/sec)\n\n")
        self.benchmark_results_box.insert("end", f"🎯 Calibrated Continuous Slider Recommendations:\n")
        self.benchmark_results_box.insert("end", f"  • 📦 Batch Size Slider: {result.recommended_batch_size} files/cluster\n")
        self.benchmark_results_box.insert("end", f"  • 📊 File Limit Slider: {result.recommended_limit} files\n")
        self.benchmark_results_box.insert("end", f"  • 📄 Document Peek Budget Slider: {result.recommended_peek_length} chars\n")
        self.benchmark_results_box.insert("end", f"  • ⏱️ Inter-Batch Pacing Slider: {result.recommended_pacing_delay:.2f}s delay\n\n")
        self.benchmark_results_box.insert("end", f"💡 Hardware Insights:\n")
        for rec in result.recommendations:
            self.benchmark_results_box.insert("end", f"  {rec}\n")
        self.benchmark_results_box.see("1.0")

    def _on_benchmark_error(self, err_msg: str):
        self.benchmark_run_btn.configure(state="normal")
        self.benchmark_apply_btn.configure(state="disabled")
        self.benchmark_progress_bar.set(0.0)
        self.benchmark_status_label.configure(text=f"❌ Benchmark Error: {err_msg}", text_color="#FF6B6B")
        self.benchmark_results_box.delete("1.0", "end")
        self.benchmark_results_box.insert("end", f"❌ Failed to run benchmark: {err_msg}\n\nPlease check your provider configuration or connection.")

    def _apply_benchmark_settings(self):
        if not getattr(self, "last_benchmark_result", None):
            return

        res = self.last_benchmark_result
        if hasattr(self, "batch_size_slider"):
            self.batch_size_slider.set(res.recommended_batch_size)
            self._on_batch_size_slider_changed(res.recommended_batch_size)

        if hasattr(self, "limit_slider"):
            self.limit_slider.set(res.recommended_limit)
            self._on_limit_slider_changed(res.recommended_limit)

        if hasattr(self, "peek_length_slider"):
            self.peek_length_slider.set(res.recommended_peek_length)
            self._on_peek_length_slider_changed(res.recommended_peek_length)

        if hasattr(self, "pacing_slider"):
            self.pacing_slider.set(res.recommended_pacing_delay)
            self._on_pacing_slider_changed(res.recommended_pacing_delay)

        applied_msg = (
            f"Applied Optimal Settings for {res.hardware_tier}:\n"
            f"  • 📦 Batch Size Slider: {res.recommended_batch_size} files/cluster\n"
            f"  • 📊 File Limit Slider: {res.recommended_limit} files\n"
            f"  • 📄 Context Peek Budget Slider: {res.recommended_peek_length} chars\n"
            f"  • ⏱️ Inter-Batch Pacing Slider: {res.recommended_pacing_delay:.2f}s delay"
        )

        if res.is_vision_supported and not self.analyze_images_var.get():
            enable_vision = messagebox.askyesno(
                "Enable Vision?",
                f"Your active model supports Vision!\n\n"
                f"Would you like to enable 'Analyze image contents using AI Vision' so AI can inspect actual photo contents instead of relying on filenames?"
            )
            if enable_vision:
                self.analyze_images_var.set(True)
                applied_msg += "\n  • 👁️ Enabled AI Vision for images"

        self._save_settings(silent=True)
        messagebox.showinfo("Optimal Settings Applied", f"{applied_msg}\n\nSettings saved successfully!")

    def _open_settings(self):
        try:
            if self.settings_window and self.settings_window.winfo_exists():
                self.settings_window.deiconify()
                self.settings_window.lift()
                self.settings_window.focus_force()
            else:
                self._build_settings_window()
                self.settings_window.deiconify()
        except Exception:
            self._build_settings_window()
            self.settings_window.deiconify()

    def _hide_settings(self):
        self.settings_window.withdraw()

    def _open_quick_deploy(self):
        try:
            if self.quick_deploy_window and self.quick_deploy_window.winfo_exists():
                self.quick_deploy_window.deiconify()
                self.quick_deploy_window.lift()
                self.quick_deploy_window.focus_force()
            else:
                self._build_quick_deploy_window()
                self.quick_deploy_window.deiconify()
        except Exception:
            self._build_quick_deploy_window()
            self.quick_deploy_window.deiconify()

    def _hide_quick_deploy(self):
        if self.quick_deploy_window and self.quick_deploy_window.winfo_exists():
            self.quick_deploy_window.withdraw()

    def _build_quick_deploy_window(self):
        self.quick_deploy_window = ctk.CTkToplevel(self)
        self.quick_deploy_window.title("NoMoreClutter - 🚀 1-Click AI Quick Deploy")
        self.quick_deploy_window.geometry("700x660")
        self.quick_deploy_window.withdraw()
        self.quick_deploy_window.protocol("WM_DELETE_WINDOW", self._hide_quick_deploy)

        # Header
        head = ctk.CTkFrame(self.quick_deploy_window, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(head, text="🚀 1-Click AI Quick Deploy", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(head, text="Deploy a local model or connect fast cloud AI in one click without complicated setups.", text_color="gray", font=ctk.CTkFont(size=12)).pack(anchor="w")

        # Tabs
        tabs = ctk.CTkTabview(self.quick_deploy_window)
        tabs.pack(fill="both", expand=True, padx=20, pady=(5, 15))

        tab_embed = tabs.add("📦 Built-In Embedded AI")
        tab_ollama = tabs.add("🦙 Ollama Auto-Pilot")
        tab_cloud = tabs.add("⚡ Instant Free Cloud")

        # ==========================================
        # TAB 1: Built-In Embedded AI (100% Offline GGUF)
        # ==========================================
        ctk.CTkLabel(tab_embed, text="📦 100% Offline Embedded AI (No External Apps)", font=ctk.CTkFont(weight="bold", size=14)).pack(padx=10, pady=(10, 4), anchor="w")
        ctk.CTkLabel(tab_embed, text="Downloads a quantized GGUF model directly into NoMoreClutter. Runs completely offline without LM Studio, Ollama, or API keys.", text_color="gray", wraplength=620, justify="left", font=ctk.CTkFont(size=12)).pack(padx=10, pady=(0, 10), anchor="w")

        ModelDownloader, GGUF_CATALOG = get_model_downloader()
        catalog_names = [item.name for item in GGUF_CATALOG.values()]

        ctk.CTkLabel(tab_embed, text="Select Model:", font=ctk.CTkFont(weight="bold")).pack(padx=10, pady=(5, 2), anchor="w")
        self.embed_model_var = ctk.StringVar(value=catalog_names[1] if len(catalog_names) > 1 else catalog_names[0])
        self.embed_model_menu = ctk.CTkOptionMenu(
            tab_embed,
            values=catalog_names,
            variable=self.embed_model_var,
            command=self._on_embed_catalog_changed,
            width=580,
            height=36,
        )
        self.embed_model_menu.pack(padx=10, pady=(0, 10), anchor="w")

        # Status & description card
        self.embed_card = ctk.CTkFrame(tab_embed, fg_color="#1E1E24", corner_radius=8)
        self.embed_card.pack(fill="x", padx=10, pady=5)
        
        self.embed_desc_label = ctk.CTkLabel(self.embed_card, text="", text_color="cyan", wraplength=580, justify="left", font=ctk.CTkFont(size=12))
        self.embed_desc_label.pack(padx=12, pady=(10, 4), anchor="w")
        
        self.embed_status_label = ctk.CTkLabel(self.embed_card, text="", font=ctk.CTkFont(weight="bold", size=12))
        self.embed_status_label.pack(padx=12, pady=(0, 10), anchor="w")

        # Progress elements
        ctk.CTkLabel(tab_embed, text="Download Progress:", font=ctk.CTkFont(weight="bold")).pack(padx=10, pady=(12, 2), anchor="w")
        self.embed_progress_bar = ctk.CTkProgressBar(tab_embed, width=580, height=14)
        self.embed_progress_bar.set(0.0)
        self.embed_progress_bar.pack(padx=10, pady=(0, 4), anchor="w")

        self.embed_progress_label = ctk.CTkLabel(tab_embed, text="Ready", text_color="gray", font=ctk.CTkFont(size=11))
        self.embed_progress_label.pack(padx=10, pady=(0, 10), anchor="w")

        # Embedded action buttons
        embed_btn_row = ctk.CTkFrame(tab_embed, fg_color="transparent")
        embed_btn_row.pack(fill="x", padx=10, pady=10)

        self.embed_download_btn = ctk.CTkButton(
            embed_btn_row,
            text="⬇️ Download & Activate Model",
            command=self._download_embedded_action,
            height=38,
            fg_color="#D9480F",
            hover_color="#C92A2A",
            font=ctk.CTkFont(weight="bold")
        )
        self.embed_download_btn.pack(side="left", padx=(0, 8))

        self.embed_cancel_btn = ctk.CTkButton(
            embed_btn_row,
            text="🛑 Cancel",
            command=self._cancel_embedded_download,
            height=38,
            state="disabled",
            fg_color="#6C757D"
        )
        self.embed_cancel_btn.pack(side="left", padx=8)

        self.embed_activate_btn = ctk.CTkButton(
            embed_btn_row,
            text="✅ Set as Active Provider",
            command=self._activate_selected_embedded_model,
            height=38,
            state="disabled",
            fg_color="#2B8A3E",
            hover_color="#237032"
        )
        self.embed_activate_btn.pack(side="left", padx=8)

        self._update_embed_status_ui()

        # ==========================================
        # TAB 2: Ollama Auto-Pilot
        # ==========================================
        ctk.CTkLabel(tab_ollama, text="🦙 1-Click Ollama Auto-Pilot", font=ctk.CTkFont(weight="bold", size=14)).pack(padx=10, pady=(10, 4), anchor="w")
        ctk.CTkLabel(tab_ollama, text="Pings your local Ollama daemon on localhost:11434 and streams models with one click.", text_color="gray", wraplength=620, justify="left", font=ctk.CTkFont(size=12)).pack(padx=10, pady=(0, 8), anchor="w")

        # Ollama connection badge
        ollama_status_frame = ctk.CTkFrame(tab_ollama, fg_color="#1E1E24", corner_radius=8)
        ollama_status_frame.pack(fill="x", padx=10, pady=5)
        
        self.ollama_conn_label = ctk.CTkLabel(ollama_status_frame, text="Checking Ollama...", font=ctk.CTkFont(weight="bold", size=12))
        self.ollama_conn_label.pack(side="left", padx=12, pady=10)

        ctk.CTkButton(
            ollama_status_frame,
            text="🔄 Refresh",
            width=80,
            height=28,
            command=self._refresh_ollama_status
        ).pack(side="right", padx=12, pady=8)

        self.ollama_installed_label = ctk.CTkLabel(tab_ollama, text="Installed in Ollama: checking...", text_color="gray", font=ctk.CTkFont(size=11), wraplength=600, justify="left")
        self.ollama_installed_label.pack(padx=10, pady=(4, 8), anchor="w")

        OllamaManager, RECOMMENDED_OLLAMA_MODELS = get_ollama_manager()
        ollama_model_options = [f"{m.id} - {m.name} ({m.size_approx})" for m in RECOMMENDED_OLLAMA_MODELS.values()]

        ctk.CTkLabel(tab_ollama, text="Select Recommended Model to Pull:", font=ctk.CTkFont(weight="bold")).pack(padx=10, pady=(6, 2), anchor="w")
        self.ollama_model_var = ctk.StringVar(value=ollama_model_options[0])
        self.ollama_model_menu = ctk.CTkOptionMenu(
            tab_ollama,
            values=ollama_model_options,
            variable=self.ollama_model_var,
            width=580,
            height=36
        )
        self.ollama_model_menu.pack(padx=10, pady=(0, 10), anchor="w")

        # Progress elements
        ctk.CTkLabel(tab_ollama, text="Pull Progress:", font=ctk.CTkFont(weight="bold")).pack(padx=10, pady=(8, 2), anchor="w")
        self.ollama_progress_bar = ctk.CTkProgressBar(tab_ollama, width=580, height=14)
        self.ollama_progress_bar.set(0.0)
        self.ollama_progress_bar.pack(padx=10, pady=(0, 4), anchor="w")

        self.ollama_progress_label = ctk.CTkLabel(tab_ollama, text="Ready", text_color="gray", font=ctk.CTkFont(size=11))
        self.ollama_progress_label.pack(padx=10, pady=(0, 10), anchor="w")

        # Ollama action buttons
        ollama_btn_row = ctk.CTkFrame(tab_ollama, fg_color="transparent")
        ollama_btn_row.pack(fill="x", padx=10, pady=10)

        self.ollama_pull_btn = ctk.CTkButton(
            ollama_btn_row,
            text="📥 1-Click Pull to Ollama & Activate",
            command=self._pull_ollama_action,
            height=38,
            fg_color="#1F6AA5",
            hover_color="#144A75",
            font=ctk.CTkFont(weight="bold")
        )
        self.ollama_pull_btn.pack(side="left", padx=(0, 8))

        self.ollama_cancel_btn = ctk.CTkButton(
            ollama_btn_row,
            text="🛑 Cancel",
            command=self._cancel_ollama_pull,
            height=38,
            state="disabled",
            fg_color="#6C757D"
        )
        self.ollama_cancel_btn.pack(side="left", padx=8)

        self._refresh_ollama_status()

        # ==========================================
        # TAB 3: Instant Free Cloud
        # ==========================================
        ctk.CTkLabel(tab_cloud, text="⚡ Instant Zero-Download Cloud AI", font=ctk.CTkFont(weight="bold", size=14)).pack(padx=10, pady=(10, 4), anchor="w")
        ctk.CTkLabel(tab_cloud, text="Use high-speed free tier cloud models (Groq or Google Gemini). 0 MB disk space, instant start, intelligent reasoning.", text_color="gray", wraplength=620, justify="left", font=ctk.CTkFont(size=12)).pack(padx=10, pady=(0, 12), anchor="w")

        self.cloud_provider_var = ctk.StringVar(value="Groq (Free & Fastest - Zero Install)")
        cloud_options = ["Groq (Free & Fastest - Zero Install)", "Google Gemini (Free Tier - Zero Install)"]
        self.cloud_provider_menu = ctk.CTkOptionMenu(
            tab_cloud,
            values=cloud_options,
            variable=self.cloud_provider_var,
            width=580,
            height=36,
            command=self._on_cloud_provider_changed
        )
        self.cloud_provider_menu.pack(padx=10, pady=(0, 10), anchor="w")

        self.cloud_desc_label = ctk.CTkLabel(tab_cloud, text="⚡ Groq provides ultra-fast free LLaMA 3.3 70B inference with hundreds of tokens per second.", text_color="cyan", wraplength=580, justify="left", font=ctk.CTkFont(size=12))
        self.cloud_desc_label.pack(padx=10, pady=(0, 10), anchor="w")

        self.cloud_key_btn = ctk.CTkButton(
            tab_cloud,
            text="🔗 Open Free Key Website (console.groq.com)",
            command=self._open_cloud_key_url,
            height=32,
            fg_color="#3B8ED0"
        )
        self.cloud_key_btn.pack(padx=10, pady=(0, 12), anchor="w")

        ctk.CTkLabel(tab_cloud, text="Paste Your Free API Key Here:", font=ctk.CTkFont(weight="bold")).pack(padx=10, pady=(4, 2), anchor="w")
        self.cloud_key_entry = ctk.CTkEntry(tab_cloud, width=580, height=36, placeholder_text="gsk_... or AIzaSy...")
        self.cloud_key_entry.pack(padx=10, pady=(0, 12), anchor="w")

        ctk.CTkButton(
            tab_cloud,
            text="⚡ Validate & Activate Cloud AI",
            command=self._activate_cloud_action,
            height=38,
            fg_color="#2B8A3E",
            hover_color="#237032",
            font=ctk.CTkFont(weight="bold")
        ).pack(padx=10, pady=10, anchor="w")

        self.cloud_status_label = ctk.CTkLabel(tab_cloud, text="", font=ctk.CTkFont(size=12))
        self.cloud_status_label.pack(padx=10, pady=5, anchor="w")

    def _on_embed_catalog_changed(self, choice):
        self._update_embed_status_ui()

    def _update_embed_status_ui(self):
        ModelDownloader, GGUF_CATALOG = get_model_downloader()
        choice = self.embed_model_var.get()
        selected_item = None
        for item in GGUF_CATALOG.values():
            if item.name == choice:
                selected_item = item
                break
        if not selected_item:
            selected_item = GGUF_CATALOG["qwen2.5-1.5b"]

        self.embed_desc_label.configure(text=f"ℹ️ {selected_item.description} (Size: ~{selected_item.size_mb} MB)")

        is_dl = ModelDownloader.is_model_downloaded(selected_item.filename)
        if is_dl:
            model_path = ModelDownloader.get_model_path(selected_item.filename)
            actual_mb = model_path.stat().st_size / (1024 * 1024)
            self.embed_status_label.configure(text=f"✅ Downloaded & Ready to Use ({actual_mb:.0f} MB)", text_color="#51CF66")
            self.embed_download_btn.configure(text="⬇️ Re-Download Model", state="normal")
            self.embed_activate_btn.configure(state="normal")
        else:
            self.embed_status_label.configure(text=f"⬇️ Not Downloaded Yet (~{selected_item.size_mb} MB needed)", text_color="#FFA94D")
            self.embed_download_btn.configure(text="⬇️ Download & Activate Model", state="normal")
            self.embed_activate_btn.configure(state="disabled")

    def _download_embedded_action(self):
        choice = self.embed_model_var.get()
        ModelDownloader, GGUF_CATALOG = get_model_downloader()
        selected_id = "qwen2.5-1.5b"
        for item in GGUF_CATALOG.values():
            if item.name == choice:
                selected_id = item.id
                break

        self.embed_cancel_event.clear()
        self.embed_download_btn.configure(state="disabled")
        self.embed_activate_btn.configure(state="disabled")
        self.embed_cancel_btn.configure(state="normal")
        self.embed_progress_bar.set(0.0)
        self.embed_progress_label.configure(text="Connecting to HuggingFace repository...", text_color="yellow")

        thread = threading.Thread(target=self._download_embedded_worker, args=(selected_id,), daemon=True)
        thread.start()

    def _cancel_embedded_download(self):
        self.embed_cancel_event.set()
        self.embed_progress_label.configure(text="Aborting download...", text_color="#FFA94D")

    def _download_embedded_worker(self, model_id: str):
        ModelDownloader, GGUF_CATALOG = get_model_downloader()
        item = GGUF_CATALOG.get(model_id)

        def progress_cb(downloaded, total, speed, percent):
            val = (percent / 100.0) if percent > 0 else 0.0
            mb_down = downloaded / (1024 * 1024)
            mb_tot = total / (1024 * 1024)
            txt = f"Downloading: {percent:.1f}% ({mb_down:.0f}/{mb_tot:.0f} MB) - {speed:.1f} MB/s"
            self.after(0, self._update_embed_progress_ui, val, txt)

        try:
            dest_path = ModelDownloader.download_model(
                model_id=model_id,
                progress_callback=progress_cb,
                cancel_event=self.embed_cancel_event,
            )
            fn = item.filename if item else os.path.basename(dest_path)
            self.after(0, self._on_embedded_download_success, fn)
        except InterruptedError:
            self.after(0, self._on_embedded_download_cancelled)
        except Exception as e:
            self.after(0, self._on_embedded_download_error, str(e))

    def _update_embed_progress_ui(self, val, txt):
        self.embed_progress_bar.set(val)
        self.embed_progress_label.configure(text=txt, text_color="yellow")

    def _on_embedded_download_success(self, filename: str):
        self.embed_progress_bar.set(1.0)
        self.embed_progress_label.configure(text="✅ Download Complete!", text_color="#51CF66")
        self.embed_download_btn.configure(state="normal")
        self.embed_cancel_btn.configure(state="disabled")
        self._update_embed_status_ui()
        self._activate_embedded_model(filename)

    def _on_embedded_download_cancelled(self):
        self.embed_progress_bar.set(0.0)
        self.embed_progress_label.configure(text="❌ Download Cancelled", text_color="#FF6B6B")
        self.embed_download_btn.configure(state="normal")
        self.embed_cancel_btn.configure(state="disabled")
        self._update_embed_status_ui()

    def _on_embedded_download_error(self, err: str):
        self.embed_progress_bar.set(0.0)
        self.embed_progress_label.configure(text=f"❌ Download Error: {err}", text_color="#FF6B6B")
        self.embed_download_btn.configure(state="normal")
        self.embed_cancel_btn.configure(state="disabled")
        self._update_embed_status_ui()
        messagebox.showerror("Download Error", f"Failed to download model weights:\n{err}")

    def _activate_selected_embedded_model(self):
        ModelDownloader, GGUF_CATALOG = get_model_downloader()
        choice = self.embed_model_var.get()
        selected_item = None
        for item in GGUF_CATALOG.values():
            if item.name == choice:
                selected_item = item
                break
        if not selected_item:
            selected_item = GGUF_CATALOG["qwen2.5-1.5b"]

        self._activate_embedded_model(selected_item.filename)

    def _activate_embedded_model(self, filename: str):
        target_provider_name = "Built-In Embedded AI (100% Offline GGUF)"
        self.provider_var.set(target_provider_name)
        self._update_provider_ui(target_provider_name)
        self.llm_model.delete(0, "end")
        self.llm_model.insert(0, filename)
        self._save_settings(silent=True)
        self.status_label.configure(text=f"✅ Active: Built-In AI ({filename})", text_color="#51CF66")
        self.output_text.insert("end", f"\n🚀 Activated Built-In Embedded Model: {filename}\n")
        self.output_text.see("end")
        messagebox.showinfo("Activated", f"Built-In model '{filename}' is now active and ready for offline organization!")

    def _refresh_ollama_status(self):
        OllamaManager, _ = get_ollama_manager()
        is_running, msg = OllamaManager.check_status()
        if is_running:
            self.ollama_conn_label.configure(text="✅ " + msg, text_color="#51CF66")
            self.ollama_pull_btn.configure(state="normal")
            installed = OllamaManager.list_installed_models()
            if installed:
                inst_str = ", ".join(installed[:6])
                if len(installed) > 6:
                    inst_str += f" (+{len(installed) - 6} more)"
                self.ollama_installed_label.configure(text=f"Installed in Ollama: {inst_str}", text_color="#4DABF7")
            else:
                self.ollama_installed_label.configure(text="No models installed yet in Ollama.", text_color="gray")
        else:
            self.ollama_conn_label.configure(text="⚠️ " + msg, text_color="#FFA94D")
            self.ollama_installed_label.configure(text="Ollama daemon is offline. Run `ollama serve` in terminal.", text_color="gray")

    def _pull_ollama_action(self):
        choice = self.ollama_model_var.get()
        tag = choice.split()[0].strip()
        OllamaManager, _ = get_ollama_manager()
        is_running, _ = OllamaManager.check_status()
        if not is_running:
            messagebox.showwarning("Ollama Not Running", "Ollama is not running on localhost:11434.\nPlease start Ollama and click Refresh.")
            return

        self.ollama_cancel_event.clear()
        self.ollama_pull_btn.configure(state="disabled")
        self.ollama_cancel_btn.configure(state="normal")
        self.ollama_progress_bar.set(0.0)
        self.ollama_progress_label.configure(text=f"Starting pull for {tag}...", text_color="yellow")

        thread = threading.Thread(target=self._pull_ollama_worker, args=(tag,), daemon=True)
        thread.start()

    def _cancel_ollama_pull(self):
        self.ollama_cancel_event.set()
        self.ollama_progress_label.configure(text="Cancelling pull...", text_color="#FFA94D")

    def _pull_ollama_worker(self, model_tag: str):
        OllamaManager, _ = get_ollama_manager()

        def progress_cb(status, completed, total, percent):
            val = (percent / 100.0) if percent > 0 else 0.0
            mb_down = completed / (1024 * 1024)
            mb_tot = total / (1024 * 1024)
            if total > 0:
                txt = f"{status}: {percent:.1f}% ({mb_down:.0f}/{mb_tot:.0f} MB)"
            else:
                txt = f"Status: {status}"
            self.after(0, self._update_ollama_progress_ui, val, txt)

        try:
            success = OllamaManager.pull_model(
                model_name=model_tag,
                progress_callback=progress_cb,
                cancel_event=self.ollama_cancel_event,
            )
            if success:
                self.after(0, self._on_ollama_pull_success, model_tag)
            else:
                self.after(0, self._on_ollama_pull_error, "Pull did not complete successfully.")
        except InterruptedError:
            self.after(0, self._on_ollama_pull_cancelled)
        except Exception as e:
            self.after(0, self._on_ollama_pull_error, str(e))

    def _update_ollama_progress_ui(self, val, txt):
        self.ollama_progress_bar.set(val)
        self.ollama_progress_label.configure(text=txt, text_color="yellow")

    def _on_ollama_pull_success(self, model_tag: str):
        self.ollama_progress_bar.set(1.0)
        self.ollama_progress_label.configure(text=f"✅ Successfully pulled {model_tag}!", text_color="#51CF66")
        self.ollama_pull_btn.configure(state="normal")
        self.ollama_cancel_btn.configure(state="disabled")
        self._refresh_ollama_status()
        self._activate_ollama_model(model_tag)

    def _on_ollama_pull_cancelled(self):
        self.ollama_progress_bar.set(0.0)
        self.ollama_progress_label.configure(text="❌ Pull Cancelled", text_color="#FF6B6B")
        self.ollama_pull_btn.configure(state="normal")
        self.ollama_cancel_btn.configure(state="disabled")

    def _on_ollama_pull_error(self, err: str):
        self.ollama_progress_bar.set(0.0)
        self.ollama_progress_label.configure(text=f"❌ Pull Error: {err}", text_color="#FF6B6B")
        self.ollama_pull_btn.configure(state="normal")
        self.ollama_cancel_btn.configure(state="disabled")
        messagebox.showerror("Ollama Pull Error", f"Failed to pull model in Ollama:\n{err}")

    def _activate_ollama_model(self, model_tag: str):
        target_name = "Ollama (Local Server)"
        self.provider_var.set(target_name)
        self._update_provider_ui(target_name)
        self.llm_model.delete(0, "end")
        self.llm_model.insert(0, model_tag)
        self._save_settings(silent=True)
        self.status_label.configure(text=f"✅ Active: Ollama ({model_tag})", text_color="#51CF66")
        self.output_text.insert("end", f"\n🦙 Activated Ollama Model: {model_tag}\n")
        self.output_text.see("end")
        messagebox.showinfo("Activated", f"Ollama model '{model_tag}' is now active and ready for local organization!")

    def _on_cloud_provider_changed(self, choice: str):
        if "groq" in choice.lower():
            self.cloud_desc_label.configure(text="⚡ Groq provides ultra-fast free LLaMA 3.3 70B inference with hundreds of tokens per second.")
            self.cloud_key_btn.configure(text="🔗 Open Free Key Website (console.groq.com)")
        else:
            self.cloud_desc_label.configure(text="🌟 Google Gemini provides a generous free tier with multimodal vision and reasoning.")
            self.cloud_key_btn.configure(text="🔗 Open Free Key Website (aistudio.google.com)")

    def _open_cloud_key_url(self):
        choice = self.cloud_provider_var.get()
        if "groq" in choice.lower():
            webbrowser.open("https://console.groq.com/keys")
        else:
            webbrowser.open("https://aistudio.google.com/app/apikey")

    def _activate_cloud_action(self):
        choice = self.cloud_provider_var.get()
        key = self.cloud_key_entry.get().strip()
        if not key:
            messagebox.showwarning("Key Required", "Please paste your free API key into the field above.")
            return

        provider_id = "groq" if "groq" in choice.lower() else "gemini"
        _, get_preset, _, _, _ = get_provider_registry()
        preset = get_preset(provider_id)

        self.cloud_status_label.configure(text="Testing connection...", text_color="yellow")
        self.update()

        LLMService, _ = get_LLMService()
        llm = LLMService(base_url=preset.base_url, api_key=key, provider_id=provider_id)
        success, msg = llm.test_connection(preset.default_model)

        if success:
            self.provider_var.set(preset.name)
            self._update_provider_ui(preset.name)
            self.api_key_entry.delete(0, "end")
            self.api_key_entry.insert(0, key)
            self._save_settings(silent=True)
            self.cloud_status_label.configure(text=f"✅ Connected & Activated: {preset.name}", text_color="#51CF66")
            self.status_label.configure(text=f"✅ Active: {preset.name}", text_color="#51CF66")
            self.output_text.insert("end", f"\n⚡ Connected & Activated Cloud Provider: {preset.name}\n")
            self.output_text.see("end")
            messagebox.showinfo("Activated", f"Successfully activated {preset.name}!\n\n{msg}")
        else:
            self.cloud_status_label.configure(text=f"❌ Connection failed: {msg}", text_color="#FF6B6B")
            messagebox.showerror("Connection Failed", f"Could not connect to {preset.name}:\n\n{msg}\n\nPlease verify your API key.")


    def _select_source(self):
        folder = filedialog.askdirectory(title="Select Source Folder")
        if folder:
            self.source_folder = folder
            self.source_entry.delete(0, "end")
            self.source_entry.insert(0, folder)
            self.created_folders = []
            self._update_folder_info()

    def _select_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder = folder
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, folder)
            self._update_folder_info()

    def _update_folder_info(self):
        output = self.output_folder if self.output_folder else self.source_folder
        if output:
            self.folder_info_label.configure(text=f"Files will be organized in: {output}")
        existing = self._get_existing_folders()
        if existing:
            folders_str = ", ".join(existing[:8])
            if len(existing) > 8:
                folders_str += f", ... (+{len(existing) - 8} more)"
            self.existing_folders_label.configure(text=f"Existing folders: {folders_str}", text_color="#4DABF7")
        else:
            self.existing_folders_label.configure(text="No subfolders currently in output directory", text_color="gray")

    def _get_selected_extensions(self):
        extensions = []
        for category, var in self.type_vars.items():
            if var.get():
                extensions.extend(FILE_TYPE_CATEGORIES[category])
        return extensions

    def _get_existing_folders(self):
        folders = []
        checked = set()
        output = self.output_folder if self.output_folder else self.source_folder
        if output and os.path.exists(output):
            for item in os.listdir(output):
                if item not in checked:
                    path = os.path.join(output, item)
                    if os.path.isdir(path):
                        folders.append(item)
                        checked.add(item)
        return folders

    def _quick_organize(self):
        """Instant zero-install heuristic categorization (PRINCIPLE-008)."""
        extensions = self._get_selected_extensions()
        if not extensions:
            messagebox.showwarning("Warning", "Please select at least one file category")
            return
        if not self.source_folder:
            messagebox.showwarning("Warning", "Please select a source folder")
            return

        files = get_FileScanner().scan_folder(self.source_folder, extensions, include_subfolders=False)
        if not files:
            messagebox.showinfo("Info", "No matching files found in the source directory.")
            return

        try:
            if hasattr(self, "limit_slider"):
                limit = int(round(float(self.limit_slider.get())))
            else:
                limit = int(self.limit_entry.get().strip() or 0)
        except Exception:
            limit = 0
        if limit > 0:
            files = files[:limit]

        output = self.output_folder if self.output_folder else self.source_folder
        RLMOrganizer, _ = get_RLMOrganizer()
        
        # Pure rule-based fast categorization
        changes = []
        existing = self._get_existing_folders()
        for f in files:
            cat = RLMOrganizer.get_heuristic_category(f)
            folder_name = cat
            if not self.create_folders_var.get():
                if existing:
                    folder_name = RLMOrganizer._match_closest_folder(cat, existing)
                else:
                    folder_name = ""
            
            target_path = os.path.join(output, folder_name, os.path.basename(f)) if folder_name else os.path.join(output, os.path.basename(f))
            changes.append(FileChange(
                original=f,
                action="move",
                new_path=target_path
            ))

        # Honor numbered_rename setting
        if self.numbered_rename_var.get() and changes:
            changes = RLMOrganizer._apply_numbered_rename(changes)

        self.analysis_results = changes
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", f"⚡ Quick Organized {len(changes)} files using smart rules:\n\n")
        for c in changes:
            dest_dir = os.path.dirname(c.new_path)
            dest_cat = os.path.basename(dest_dir) if dest_dir != output else "(root)"
            self.output_text.insert("end", f"  • {os.path.basename(c.original)} ➔ {dest_cat}/\n")

        self.status_label.configure(text=f"⚡ Ready: {len(changes)} files classified", text_color="#51CF66")
        self.execute_btn.configure(state="normal")
        
        if self.auto_execute_var.get():
            self._execute()

    def _analyze(self):
        extensions = self._get_selected_extensions()
        if not extensions:
            messagebox.showwarning("Warning", "Please select at least one file category")
            return
        if not self.source_folder:
            messagebox.showwarning("Warning", "Please select a source folder")
            return

        if not getattr(self, "ai_is_plugged", False):
            badge = getattr(self, "ai_status_badge", "Unplugged")
            detail = getattr(self, "ai_status_detail", "No active AI provider is connected.")
            msg = (
                f"AI is currently unplugged ({badge}).\n\n"
                f"{detail}\n\n"
                "Would you like to open '1-Click AI Deploy' to set up a model or free key?\n\n"
                "• Click 'Yes' to open 1-Click AI Deploy.\n"
                "• Click 'No' to organize files instantly with '⚡ Quick Organize (No AI)'.\n"
                "• Click 'Cancel' to abort."
            )
            choice = messagebox.askyesnocancel("AI Unplugged", msg)
            if choice is True:
                self._open_quick_deploy()
                return
            elif choice is False:
                self._quick_organize()
                return
            else:
                return

        files = get_FileScanner().scan_folder(self.source_folder, extensions, include_subfolders=False)
        if not files:
            messagebox.showinfo("Info", "No matching files found in the source directory.")
            return

        try:
            if hasattr(self, "limit_slider"):
                limit = int(round(float(self.limit_slider.get())))
            else:
                limit = int(self.limit_entry.get().strip() or 0)
        except Exception:
            limit = 0

        if limit > 0:
            files = files[:limit]

        self.total_files = len(files)
        self.processed_files = 0
        self.analysis_results = []

        self.status_label.configure(text=f"Found {self.total_files} files. Analyzing with AI...", text_color="yellow")
        self.analyze_btn.configure(state="disabled")
        self.quick_btn.configure(state="disabled")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", f"🤖 Starting RLM analysis on {self.total_files} files...\n\n")

        thread = threading.Thread(target=self._analyze_thread, args=(files,), daemon=True)
        thread.start()

    def _analyze_thread(self, files):
        try:
            if hasattr(self, "batch_size_slider"):
                batch_size = int(round(float(self.batch_size_slider.get())))
            else:
                batch_size = int(self.batch_size_entry.get().strip() or 15)
        except Exception:
            batch_size = 15
        if batch_size <= 0:
            batch_size = 15

        try:
            if hasattr(self, "peek_length_slider"):
                peek_max_chars = int(round(float(self.peek_length_slider.get())))
            else:
                peek_max_chars = int(self.settings.get("peek_length", 180) or 180)
        except Exception:
            peek_max_chars = 180

        _, _, get_by_name, _, _ = get_provider_registry()
        preset = get_by_name(self.provider_var.get())
        provider_id = preset.id if preset else ("embedded" if self.llm_url.get().strip() == "local://embedded" else "custom")
        model_name = self.llm_model.get().strip()

        try:
            if hasattr(self, "pacing_slider"):
                pacing_sec = float(self.pacing_slider.get())
            else:
                pacing_sec = preset.recommended_pacing_sec if preset else 0.2
        except Exception:
            pacing_sec = 0.2

        all_results = []
        output = self.output_folder if self.output_folder else self.source_folder

        try:
            LLMService, LLMError = get_LLMService()
            llm = LLMService(
                base_url=self.llm_url.get().strip(),
                api_key=self.api_key_entry.get().strip(),
                provider_id=provider_id,
                model=model_name,
            )
            
            existing = self._get_existing_folders() + self.created_folders

            for i in range(0, len(files), batch_size):
                batch = files[i:i + batch_size]
                
                results = llm.analyze_files(
                    files=batch,
                    model=self.llm_model.get().strip(),
                    create_new_folders=self.create_folders_var.get(),
                    existing_folders=existing,
                    analyze_images=self.analyze_images_var.get(),
                    numbered_rename=self.numbered_rename_var.get(),
                    ai_rename=self.ai_rename_var.get(),
                    content_peeking=self.content_peeking_var.get(),
                    peek_max_chars=peek_max_chars,
                    target_folder=output,
                    output_folder=output,
                )

                all_results.extend(results)
                self.processed_files += len(batch)
                
                # Real-time logging of analyzed items
                self.after(0, self._append_batch_log, results)
                self.after(0, self._update_progress, len(batch), all_results)

                # Provider-adaptive pacing delay from slider
                if pacing_sec > 0 and (i + batch_size < len(files)):
                    time.sleep(pacing_sec)

        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda msg=err_msg: self._show_error(msg))
            return

        self.after(0, self._analysis_complete, all_results)

    def _append_batch_log(self, results):
        for r in results:
            orig_name = os.path.basename(r.original)
            dest_folder = os.path.basename(os.path.dirname(r.new_path))
            dest_name = os.path.basename(r.new_path)
            if orig_name != dest_name:
                self.output_text.insert("end", f"  • {orig_name} ➔ {dest_folder}/{dest_name}\n")
            else:
                self.output_text.insert("end", f"  • {orig_name} ➔ {dest_folder}/\n")
        self.output_text.see("end")

    def _update_progress(self, count, results):
        self.status_label.configure(text=f"Analyzing... {self.processed_files}/{self.total_files} files done", text_color="yellow")

    def _analysis_complete(self, results):
        self.analysis_results = results
        self.output_text.insert("end", f"\n✅ Analysis complete! {len(results)} proposed actions.\n")
        self.status_label.configure(text=f"✅ Analysis complete: {len(results)} files ready", text_color="#51CF66")
        self.analyze_btn.configure(state="normal")
        self.quick_btn.configure(state="normal")
        self.execute_btn.configure(state="normal")

        if self.auto_execute_var.get() and results:
            self._execute()

    def _show_error(self, error):
        self.output_text.insert("end", f"\n⚠️ AI Analysis Notice: {error}\n")
        self.output_text.insert("end", "Tip: Check your API Key or try 'Quick Organize (No AI)' for instant organization.\n")
        self.output_text.see("end")
        self.status_label.configure(text="AI paused - check settings or use Quick Organize", text_color="#FFA94D")
        self.analyze_btn.configure(state="normal")
        self.quick_btn.configure(state="normal")

    def _execute(self):
        if not self.analysis_results:
            return

        output_dir = self.output_entry.get().strip() or self.source_entry.get().strip()

        if not self.auto_execute_var.get():
            # Open interactive Tree Preview Dialog with per-file checkboxes
            TreePreviewDialog(
                self,
                changes=self.analysis_results,
                output_base_folder=output_dir,
                on_confirm=self._execute_confirmed,
            )
        else:
            self._execute_confirmed(self.analysis_results)

    def _execute_confirmed(self, selected_changes: list):
        if not selected_changes:
            return

        total_proposed = len(self.analysis_results)
        skipped_count = total_proposed - len(selected_changes)

        self.execute_btn.configure(state="disabled")

        FileExecutor = get_FileExecutor()
        success, errors = FileExecutor.execute(selected_changes)

        status_text = f"✅ Done! {success} moved"
        if skipped_count > 0:
            status_text += f", {skipped_count} skipped"
        if errors:
            status_text += f", {errors} errors"
        self.status_label.configure(text=status_text, text_color="#51CF66")

        self.output_text.insert("end", f"\n🎉 Successfully moved {success} files (collision-safe)!\n")
        if skipped_count > 0:
            self.output_text.insert("end", f"ℹ️ Skipped {skipped_count} file(s) as unchecked in Tree Preview.\n")
        if errors:
            self.output_text.insert("end", f"⚠️ Errors encountered: {errors}\n")

        self.undo_btn.configure(state="normal")
        self.analysis_results = []
        self._update_folder_info()

    def _open_duplicate_finder(self):
        folder = self.source_entry.get().strip() or self.output_entry.get().strip() or os.getcwd()
        DuplicateFinderDialog(self, initial_folder=folder)

    def _open_junk_cleaner(self):
        folder = self.source_entry.get().strip() or self.output_entry.get().strip() or os.getcwd()
        JunkCleanerDialog(self, initial_folder=folder)

    def _undo_moves(self):
        """Revert last batch of moves safely (PRINCIPLE-007)."""
        FileExecutor = get_FileExecutor()
        if not FileExecutor.has_undo():
            messagebox.showinfo("Info", "No recent moves to undo.")
            return

        if not messagebox.askyesno("Confirm Undo", "Revert the last batch of moved files back to their original locations?"):
            return

        reverted, errors = FileExecutor.undo_last_batch()
        self.output_text.insert("end", f"\n↩ Reverted {reverted} files back to original locations!\n")
        if errors:
            self.output_text.insert("end", f"⚠️ Undo errors: {errors}\n")

        self.status_label.configure(text=f"↩ Reverted {reverted} files", text_color="#4DABF7")
        if not FileExecutor.has_undo():
            self.undo_btn.configure(state="disabled")
        self._update_folder_info()


if __name__ == "__main__":
    app = NoMoreClutterApp()
    app.mainloop()
