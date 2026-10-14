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

from services import get_FileScanner, get_LLMService, get_FileExecutor, get_provider_registry
from models import FILE_TYPE_CATEGORIES, FileChange


SETTINGS_FILE = "settings.json"


class NoMoreClutterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("NoMoreClutter - AI File Organizer")
        self.geometry("1000x820")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.source_folder = ""
        self.output_folder = ""
        self.analysis_results = []
        self.created_folders = []
        self.total_files = 0
        self.processed_files = 0
        
        self._load_settings()
        self._build_ui()
        self._build_settings_window()
    
    def _load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
            else:
                self.settings = {}
        except Exception:
            self.settings = {}
    
    def _save_settings(self):
        self.settings = {
            "provider_name": self.provider_var.get(),
            "api_key": self.api_key_entry.get().strip(),
            "llm_url": self.llm_url.get().strip(),
            "llm_model": self.llm_model.get().strip(),
            "create_folders": self.create_folders_var.get(),
            "analyze_images": self.analyze_images_var.get(),
            "numbered_rename": self.numbered_rename_var.get(),
            "ai_rename": self.ai_rename_var.get(),
            "auto_execute": self.auto_execute_var.get(),
            "limit": self.limit_entry.get().strip(),
            "batch_size": self.batch_size_entry.get().strip(),
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2)
        messagebox.showinfo("Saved", "Settings saved successfully!")
    
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        # 1. Header Frame
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(top_frame, text="NoMoreClutter 🗂️", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 0), sticky="w")
        ctk.CTkLabel(top_frame, text="Intelligent, RLM-compatible file organizer", text_color="gray").grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")
        
        settings_btn = ctk.CTkButton(top_frame, text="⚙ AI Settings", width=120, command=self._open_settings)
        settings_btn.grid(row=0, rowspan=2, column=2, padx=20, pady=10)
        
        # 2. Folder Selection Frame
        folders_frame = ctk.CTkFrame(self)
        folders_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        folders_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(folders_frame, text="📁 Source Folder (files to organize)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, padx=15, pady=(12, 4), sticky="w")
        self.source_entry = ctk.CTkEntry(folders_frame, height=36)
        self.source_entry.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 8), sticky="ew")
        ctk.CTkButton(folders_frame, text="Browse", width=100, height=36, command=self._select_source).grid(row=1, column=2, padx=(0, 15), pady=(0, 8))
        
        ctk.CTkLabel(folders_frame, text="💾 Output Folder (organized destination)", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, columnspan=3, padx=15, pady=(8, 4), sticky="w")
        self.output_entry = ctk.CTkEntry(folders_frame, height=36)
        self.output_entry.grid(row=3, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="ew")
        ctk.CTkButton(folders_frame, text="Browse", width=100, height=36, command=self._select_output).grid(row=3, column=2, padx=(0, 15), pady=(0, 10))
        
        self.folder_info_label = ctk.CTkLabel(folders_frame, text="", text_color="gray", font=ctk.CTkFont(size=12))
        self.folder_info_label.grid(row=4, column=0, columnspan=3, padx=15, pady=(0, 6), sticky="w")
        
        self.existing_folders_label = ctk.CTkLabel(folders_frame, text="", text_color="gray", font=ctk.CTkFont(size=11))
        self.existing_folders_label.grid(row=5, column=0, columnspan=3, padx=15, pady=(0, 10), sticky="w")
        
        # 3. File Types Frame
        file_types_frame = ctk.CTkFrame(self)
        file_types_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        file_types_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        ctk.CTkLabel(file_types_frame, text="📋 File Categories to Include", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, padx=15, pady=(12, 6), sticky="w")
        
        self.type_vars = {}
        for i, (category, extensions) in enumerate(FILE_TYPE_CATEGORIES.items()):
            self.type_vars[category] = ctk.BooleanVar(value=True)  # Enabled by default for zero-friction
            ext_display = ", ".join(extensions[:3]) + ("..." if len(extensions) > 3 else "")
            ctk.CTkCheckBox(file_types_frame, text=f"{category} ({ext_display})", variable=self.type_vars[category]).grid(row=1 + i // 3, column=i % 3, padx=15, pady=4, sticky="w")
        
        # 4. Actions Frame
        actions_frame = ctk.CTkFrame(self)
        actions_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.analyze_btn = ctk.CTkButton(actions_frame, text="🔍 AI Organize", command=self._analyze, height=42, font=ctk.CTkFont(size=13, weight="bold"))
        self.analyze_btn.pack(side="left", padx=8, pady=12)
        
        self.quick_btn = ctk.CTkButton(actions_frame, text="⚡ Quick Organize (No AI)", command=self._quick_organize, height=42, fg_color="#3B8ED0", font=ctk.CTkFont(size=13))
        self.quick_btn.pack(side="left", padx=8, pady=12)
        
        self.execute_btn = ctk.CTkButton(actions_frame, text="▶ Execute Moves", command=self._execute, height=42, state="disabled", fg_color="green", font=ctk.CTkFont(size=13, weight="bold"))
        self.execute_btn.pack(side="left", padx=8, pady=12)
        
        self.undo_btn = ctk.CTkButton(actions_frame, text="↩ Undo Moves", command=self._undo_moves, height=42, state="disabled", fg_color="#6C757D", font=ctk.CTkFont(size=13))
        self.undo_btn.pack(side="left", padx=8, pady=12)
        
        self.status_label = ctk.CTkLabel(actions_frame, text="Select source folder to begin", text_color="gray", font=ctk.CTkFont(size=12))
        self.status_label.pack(side="left", padx=15)
        
        # 5. Output Frame
        output_frame = ctk.CTkFrame(self)
        output_frame.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        self.grid_rowconfigure(4, weight=1)
        
        self.output_header = ctk.CTkLabel(output_frame, text="📝 Activity Log & Proposed Moves", font=ctk.CTkFont(size=13, weight="bold"))
        self.output_header.pack(padx=15, pady=(12, 4), anchor="w")
        
        self.output_text = ctk.CTkTextbox(output_frame, wrap="none", font=ctk.CTkFont(family="Consolas", size=12))
        self.output_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self._build_settings_window()

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
        ctk.CTkCheckBox(scroll, text="Analyze image contents using AI Vision (requires vision-capable model)", variable=self.analyze_images_var, command=self._on_vision_toggled).pack(padx=10, pady=4, anchor="w")
        
        self.ai_rename_var = ctk.BooleanVar(value=self.settings.get("ai_rename", True))
        ctk.CTkCheckBox(scroll, text="Let AI suggest descriptive filenames based on content", variable=self.ai_rename_var).pack(padx=10, pady=4, anchor="w")
        
        self.numbered_rename_var = ctk.BooleanVar(value=self.settings.get("numbered_rename", False))
        ctk.CTkCheckBox(scroll, text="Rename files sequentially (1.jpg, 2.jpg...)", variable=self.numbered_rename_var).pack(padx=10, pady=4, anchor="w")
        
        # Section 3: Performance & Limits
        ctk.CTkLabel(scroll, text="⚡ Performance & Limits", font=ctk.CTkFont(weight="bold", size=14)).pack(padx=10, pady=(20, 5), anchor="w")
        
        self.auto_execute_var = ctk.BooleanVar(value=self.settings.get("auto_execute", False))
        ctk.CTkCheckBox(scroll, text="Auto-execute moves immediately without confirmation dialog", variable=self.auto_execute_var).pack(padx=10, pady=4, anchor="w")
        
        ctk.CTkLabel(scroll, text="Max files to process (0 = unlimited):").pack(padx=10, pady=(8, 0), anchor="w")
        self.limit_entry = ctk.CTkEntry(scroll, width=120)
        self.limit_entry.insert(0, self.settings.get("limit", "50"))
        self.limit_entry.pack(padx=10, pady=4, anchor="w")
        
        ctk.CTkLabel(scroll, text="RLM cluster batch size:").pack(padx=10, pady=(8, 0), anchor="w")
        self.batch_size_entry = ctk.CTkEntry(scroll, width=120)
        self.batch_size_entry.insert(0, self.settings.get("batch_size", "15"))
        self.batch_size_entry.pack(padx=10, pady=4, anchor="w")
        
        # Action Buttons
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=20)
        
        ctk.CTkButton(btn_row, text="💾 Save Settings", command=self._save_settings, height=38, width=140).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="🔗 Test Connection", command=self._test_connection, height=38, width=140, fg_color="#2B8A3E").pack(side="left", padx=5)
        
        self.connection_status = ctk.CTkLabel(scroll, text="", text_color="gray", wraplength=520, justify="left")
        self.connection_status.pack(padx=10, pady=5, anchor="w")
        
        # Initialize provider presets state
        self._update_provider_ui(self.provider_var.get())

    def _on_provider_changed(self, choice):
        self._update_provider_ui(choice)

    def _update_provider_ui(self, provider_name: str):
        _, _, get_by_name, _, _ = get_provider_registry()
        preset = get_by_name(provider_name)
        if not preset:
            return

        self.provider_desc_label.configure(text=f"ℹ️ {preset.description}")
        
        # Update URL and Model if they match prior presets or are default
        self.llm_url.delete(0, "end")
        self.llm_url.insert(0, preset.base_url)
        
        model_to_use = preset.vision_model if self.analyze_images_var.get() else preset.default_model
        self.llm_model.delete(0, "end")
        self.llm_model.insert(0, model_to_use)
        
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
            model_to_use = preset.vision_model if self.analyze_images_var.get() else preset.default_model
            self.llm_model.delete(0, "end")
            self.llm_model.insert(0, model_to_use)

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
            LLMService, _ = get_LLMService()
            llm = LLMService(
                base_url=self.llm_url.get().strip(),
                api_key=self.api_key_entry.get().strip(),
            )
            model_name = self.llm_model.get().strip()
            success, msg = llm.test_connection(model_name)
            if success:
                self.connection_status.configure(text=f"✅ {msg}", text_color="#51CF66")
            else:
                self.connection_status.configure(text=f"❌ {msg}", text_color="#FF6B6B")
        except Exception as e:
            self.connection_status.configure(text=f"❌ Error: {str(e)}", text_color="#FF6B6B")

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

        output = self.output_folder if self.output_folder else self.source_folder
        RLMOrganizer, _ = get_RLMOrganizer()
        
        # Pure rule-based fast categorization
        changes = []
        existing = self._get_existing_folders()
        for f in files:
            cat = RLMOrganizer.get_heuristic_category(f)
            folder_name = cat
            if not self.create_folders_var.get() and existing:
                folder_name = RLMOrganizer._match_closest_folder(cat, existing)
            changes.append(FileChange(
                original=f,
                action="move",
                new_path=os.path.join(output, folder_name, os.path.basename(f))
            ))

        self.analysis_results = changes
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", f"⚡ Quick Organized {len(changes)} files using smart rules:\n\n")
        for c in changes:
            dest_cat = os.path.basename(os.path.dirname(c.new_path))
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

        files = get_FileScanner().scan_folder(self.source_folder, extensions, include_subfolders=False)
        if not files:
            messagebox.showinfo("Info", "No matching files found in the source directory.")
            return

        try:
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
            batch_size = int(self.batch_size_entry.get().strip() or 15)
        except Exception:
            batch_size = 15

        all_results = []
        output = self.output_folder if self.output_folder else self.source_folder

        _, _, get_by_name, _, _ = get_provider_registry()
        preset = get_by_name(self.provider_var.get())
        pacing_sec = preset.recommended_pacing_sec if preset else 0.2

        try:
            LLMService, LLMError = get_LLMService()
            llm = LLMService(
                base_url=self.llm_url.get().strip(),
                api_key=self.api_key_entry.get().strip(),
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
                    target_folder=output,
                    output_folder=output,
                )

                all_results.extend(results)
                self.processed_files += len(batch)
                
                # Real-time logging of analyzed items
                self.after(0, self._append_batch_log, results)
                self.after(0, self._update_progress, len(batch), all_results)

                # Provider-adaptive pacing (0ms for fast cloud APIs, short pause for local servers)
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

        if not self.auto_execute_var.get():
            if not messagebox.askyesno("Confirm", f"Execute {len(self.analysis_results)} file operations?"):
                return

        self.execute_btn.configure(state="disabled")

        FileExecutor = get_FileExecutor()
        success, errors = FileExecutor.execute(self.analysis_results)

        self.status_label.configure(text=f"✅ Done! {success} moved, {errors} errors", text_color="#51CF66")
        self.output_text.insert("end", f"\n🎉 Successfully moved {success} files (collision-safe)!\n")
        if errors:
            self.output_text.insert("end", f"⚠️ Errors encountered: {errors}\n")

        self.undo_btn.configure(state="normal")
        self.analysis_results = []
        self._update_folder_info()

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
