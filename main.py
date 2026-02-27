import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

import json
import threading

from tkinter import filedialog, messagebox

import customtkinter as ctk

from services import get_FileScanner, get_LLMService, get_FileExecutor
from models import FILE_TYPE_CATEGORIES, FileChange


SETTINGS_FILE = "settings.json"


class NoMoreClutterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("NoMoreClutter - AI File Organizer")
        self.geometry("1000x800")
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
                with open(SETTINGS_FILE, "r") as f:
                    self.settings = json.load(f)
            else:
                self.settings = {}
        except:
            self.settings = {}
    
    def _save_settings(self):
        self.settings = {
            "llm_url": self.llm_url.get(),
            "llm_model": self.llm_model.get(),
            "create_folders": self.create_folders_var.get(),
            "analyze_images": self.analyze_images_var.get(),
            "numbered_rename": self.numbered_rename_var.get(),
            "ai_rename": self.ai_rename_var.get(),
            "auto_execute": self.auto_execute_var.get(),
            "limit": self.limit_entry.get(),
            "batch_size": self.batch_size_entry.get(),
        }
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f)
        messagebox.showinfo("Saved", "Settings saved successfully!")
    
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(top_frame, text="NoMoreClutter", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=10, sticky="w")
        ctk.CTkLabel(top_frame, text="AI-powered file organizer", text_color="gray").grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")
        
        settings_btn = ctk.CTkButton(top_frame, text="⚙ Settings", width=100, command=self._open_settings)
        settings_btn.grid(row=0, rowspan=2, column=2, padx=20, pady=10)
        
        folders_frame = ctk.CTkFrame(self)
        folders_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        folders_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(folders_frame, text="📁 Source Folder (where files are now)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, padx=15, pady=(15, 5), sticky="w")
        self.source_entry = ctk.CTkEntry(folders_frame, height=38)
        self.source_entry.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="ew")
        ctk.CTkButton(folders_frame, text="Browse", width=100, height=38, command=self._select_source).grid(row=1, column=2, padx=(0, 15), pady=(0, 10))
        
        ctk.CTkLabel(folders_frame, text="💾 Output Folder (where files will go)", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, columnspan=3, padx=15, pady=(15, 5), sticky="w")
        self.output_entry = ctk.CTkEntry(folders_frame, height=38)
        self.output_entry.grid(row=3, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")
        ctk.CTkButton(folders_frame, text="Browse", width=100, height=38, command=self._select_output).grid(row=3, column=2, padx=(0, 15), pady=(0, 15))
        
        self.folder_info_label = ctk.CTkLabel(folders_frame, text="", text_color="gray", font=ctk.CTkFont(size=12))
        self.folder_info_label.grid(row=4, column=0, columnspan=3, padx=15, pady=(0, 10), sticky="w")
        
        file_types_frame = ctk.CTkFrame(self)
        file_types_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        file_types_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        ctk.CTkLabel(file_types_frame, text="📋 File Types to Organize", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, padx=15, pady=(15, 5), sticky="w")
        
        self.type_vars = {}
        for i, (category, extensions) in enumerate(FILE_TYPE_CATEGORIES.items()):
            self.type_vars[category] = ctk.BooleanVar(value=False)
            ext_display = ", ".join(extensions[:3]) + ("..." if len(extensions) > 3 else "")
            ctk.CTkCheckBox(file_types_frame, text=f"{category} ({ext_display})", variable=self.type_vars[category]).grid(row=1 + i // 3, column=i % 3, padx=15, pady=5, sticky="w")
        
        actions_frame = ctk.CTkFrame(self)
        actions_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.analyze_btn = ctk.CTkButton(actions_frame, text="🔍 Analyze Files", command=self._analyze, height=45, font=ctk.CTkFont(size=14, weight="bold"))
        self.analyze_btn.pack(side="left", padx=10, pady=15)
        
        self.execute_btn = ctk.CTkButton(actions_frame, text="▶ Execute Moves", command=self._execute, height=45, state="disabled", fg_color="green", font=ctk.CTkFont(size=14, weight="bold"))
        self.execute_btn.pack(side="left", padx=10, pady=15)
        
        self.status_label = ctk.CTkLabel(actions_frame, text="Select folders and file types, then click Analyze", text_color="gray", font=ctk.CTkFont(size=13))
        self.status_label.pack(side="left", padx=20)
        
        output_frame = ctk.CTkFrame(self)
        output_frame.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        self.grid_rowconfigure(4, weight=1)
        
        self.output_header = ctk.CTkLabel(output_frame, text="📝 Proposed Changes", font=ctk.CTkFont(size=14, weight="bold"))
        self.output_header.pack(padx=15, pady=(15, 5), anchor="w")
        
        self.output_text = ctk.CTkTextbox(output_frame, wrap="none", font=ctk.CTkFont(size=12))
        self.output_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self._build_settings_window()
    
    def _build_settings_window(self):
        self.settings_window = ctk.CTkToplevel(self)
        self.settings_window.title("Settings")
        self.settings_window.geometry("600x550")
        self.settings_window.withdraw()
        
        # Prevent closing, just hide
        self.settings_window.protocol("WM_DELETE_WINDOW", self._hide_settings)
        
        scroll = ctk.CTkScrollableFrame(self.settings_window, label_text="⚙ Settings")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(scroll, text="AI Model Configuration", font=ctk.CTkFont(weight="bold", size=14)).pack(padx=10, pady=(10, 5), anchor="w")
        
        ctk.CTkLabel(scroll, text="API URL (for local AI):").pack(padx=10, pady=(10, 0), anchor="w")
        self.llm_url = ctk.CTkEntry(scroll, width=500)
        self.llm_url.insert(0, self.settings.get("llm_url", "http://localhost:1234/v1"))
        self.llm_url.pack(padx=10, pady=5, anchor="w")
        
        ctk.CTkLabel(scroll, text="Model name (e.g., llama3, gpt-4):").pack(padx=10, pady=(10, 0), anchor="w")
        self.llm_model = ctk.CTkEntry(scroll, width=300)
        self.llm_model.insert(0, self.settings.get("llm_model", "llama3"))
        self.llm_model.pack(padx=10, pady=5, anchor="w")
        
        ctk.CTkLabel(scroll, text="File Organization Options", font=ctk.CTkFont(weight="bold", size=14)).pack(padx=10, pady=(20, 5), anchor="w")
        
        self.create_folders_var = ctk.BooleanVar(value=self.settings.get("create_folders", True))
        ctk.CTkCheckBox(scroll, text="Create new folders for organizing (e.g., 'Photos', 'Work_Docs')", variable=self.create_folders_var).pack(padx=10, pady=3, anchor="w")
        
        self.analyze_images_var = ctk.BooleanVar(value=self.settings.get("analyze_images", False))
        ctk.CTkCheckBox(scroll, text="Use AI to understand what's in images (needs vision-capable AI)", variable=self.analyze_images_var).pack(padx=10, pady=3, anchor="w")
        
        self.numbered_rename_var = ctk.BooleanVar(value=self.settings.get("numbered_rename", False))
        ctk.CTkCheckBox(scroll, text="Rename files as numbers (1.jpg, 2.png, 3.pdf...)", variable=self.numbered_rename_var).pack(padx=10, pady=3, anchor="w")
        
        self.ai_rename_var = ctk.BooleanVar(value=self.settings.get("ai_rename", True))
        ctk.CTkCheckBox(scroll, text="Let AI suggest better names based on file content", variable=self.ai_rename_var).pack(padx=10, pady=3, anchor="w")
        
        ctk.CTkLabel(scroll, text="Processing Options", font=ctk.CTkFont(weight="bold", size=14)).pack(padx=10, pady=(20, 5), anchor="w")
        
        self.auto_execute_var = ctk.BooleanVar(value=self.settings.get("auto_execute", False))
        ctk.CTkCheckBox(scroll, text="Automatically move files after analysis (no confirmation)", variable=self.auto_execute_var).pack(padx=10, pady=3, anchor="w")
        
        ctk.CTkLabel(scroll, text="Max files to process (0 = unlimited):").pack(padx=10, pady=(10, 0), anchor="w")
        self.limit_entry = ctk.CTkEntry(scroll, width=100)
        self.limit_entry.insert(0, self.settings.get("limit", "50"))
        self.limit_entry.pack(padx=10, pady=5, anchor="w")
        
        ctk.CTkLabel(scroll, text="AI batch size (how many files per AI request):").pack(padx=10, pady=(10, 0), anchor="w")
        self.batch_size_entry = ctk.CTkEntry(scroll, width=100)
        self.batch_size_entry.insert(0, self.settings.get("batch_size", "10"))
        self.batch_size_entry.pack(padx=10, pady=5, anchor="w")
        
        ctk.CTkButton(scroll, text="💾 Save Settings", command=self._save_settings, height=40).pack(padx=10, pady=20, anchor="e")
        
        # Test connection button
        ctk.CTkButton(scroll, text="🔗 Test AI Connection", command=self._test_connection, height=40).pack(padx=10, pady=10, anchor="e")
        self.connection_status = ctk.CTkLabel(scroll, text="", text_color="gray")
        self.connection_status.pack(padx=10, pady=5, anchor="e")
    
    def _test_connection(self):
        try:
            LLMService, _ = get_LLMService()
            llm = LLMService(base_url=self.llm_url.get().strip(), api_key="not-needed")
            model_name = self.llm_model.get().strip()
            success, msg = llm.test_connection(model_name)
            if success:
                self.connection_status.configure(text=f"✅ Connected to: {model_name}", text_color="green")
            else:
                self.connection_status.configure(text=f"❌ {msg}", text_color="red")
        except Exception as e:
            self.connection_status.configure(text=f"❌ Error: {str(e)}", text_color="red")
    
    def _open_settings(self):
        try:
            if self.settings_window and self.settings_window.winfo_exists():
                self.settings_window.deiconify()
                self.settings_window.lift()
                self.settings_window.focus_force()
            else:
                self._build_settings_window()
        except:
            try:
                self._build_settings_window()
            except:
                pass
    
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
    
    def _analyze(self):
        extensions = self._get_selected_extensions()
        if not extensions:
            messagebox.showwarning("Warning", "Please select at least one file type")
            return
        
        if not self.source_folder:
            messagebox.showwarning("Warning", "Please select a source folder")
            return
        
        # Only scan the source folder, not subfolders
        files = get_FileScanner().scan_folder(self.source_folder, extensions, include_subfolders=False)
        if not files:
            messagebox.showinfo("Info", "No matching files found")
            return
        
        try:
            limit = int(self.limit_entry.get() or 0)
        except:
            limit = 0
        
        # If limit is 0, process all files (unlimited)
        if limit > 0:
            files = files[:limit]
        
        self.total_files = len(files)
        self.processed_files = 0
        self.analysis_results = []
        self.current_files = files  # Store for fallback
        
        self.status_label.configure(text=f"Found {self.total_files} files. Starting analysis...", text_color="yellow")
        self.analyze_btn.configure(state="disabled")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", f"📂 Found {self.total_files} files to analyze...\n\n")
        self.update()
        
        thread = threading.Thread(target=self._analyze_thread, args=(files,))
        thread.start()
    
    def _analyze_thread(self, files):
        try:
            batch_size = int(self.batch_size_entry.get() or 10)
        except:
            batch_size = 10
        all_results = []
        
        self.after(0, self._update_status, "🔄 Analyzing files...")
        
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            
            try:
                LLMService, LLMError = get_LLMService()
                llm = LLMService(base_url=self.llm_url.get().strip(), api_key="not-needed")
                existing = self._get_existing_folders() + self.created_folders
                output = self.output_folder if self.output_folder else self.source_folder
                
                results = llm.analyze_files(
                    files=batch,
                    model=self.llm_model.get().strip(),
                    create_new_folders=self.create_folders_var.get(),
                    existing_folders=existing,
                    analyze_images=self.analyze_images_var.get(),
                    numbered_rename=self.numbered_rename_var.get(),
                    ai_rename=self.ai_rename_var.get(),
                    target_folder=self.source_folder,
                    output_folder=output
                )
                
                all_results.extend(results)
                self.processed_files += len(batch)
                
                self.after(0, self._update_progress, len(batch), all_results)
                
            except Exception as e:
                error_msg = str(e)
                self.output_text.insert("end", f"⚠️ AI Error: {error_msg}\n")
                # Use fallback - organize by extension
                self.output_text.insert("end", "🔄 Using automatic organization by file type...\n")
                self.after(0, self._update_status, "⚠️ AI failed, using auto...")
                break
        else:
            # Loop completed without break - AI worked
            if all_results:
                self.after(0, self._update_status, f"✅ Analyzed {len(all_results)} files")
        
        # If no results or error occurred, use fallback
        if not all_results:
            self.after(0, self._update_status, "🔄 Organizing files automatically...")
            all_results = self._create_fallback_results()
        
        self.after(0, self._analysis_complete, all_results)
    
    def _update_status(self, text):
        self.status_label.configure(text=text)
    
    def _create_fallback_results(self):
        """Create automatic organization by file extension - no AI needed"""
        if not hasattr(self, 'current_files') or not self.current_files:
            return []
        
        output = self.output_folder if self.output_folder else self.source_folder
        
        # Build reverse mapping: extension -> category
        ext_to_cat = {}
        for cat, exts in FILE_TYPE_CATEGORIES.items():
            for ext in exts:
                ext_to_cat[ext.lower()] = cat
        
        # Get existing folders
        existing = self._get_existing_folders()
        
        results = []
        for f in self.current_files:
            ext = os.path.splitext(f)[1].lower()
            category = ext_to_cat.get(ext, "Other")
            
            # Use existing folder if available, otherwise use category
            folder_name = category
            if category in existing:
                folder_name = category
            
            folder_path = os.path.join(output, folder_name)
            results.append(FileChange(
                original=f, 
                action="move", 
                new_path=os.path.join(folder_path, os.path.basename(f))
            ))
        
        return results
    
    def _update_progress(self, count, results):
        self.output_text.insert("end", f"✅ Batch analyzed - got {len(results)} suggestions...\n")
        self.output_text.see("end")
        self.status_label.configure(text=f"Analyzing... {self.processed_files}/{self.total_files} files done", text_color="yellow")
    
    def _analysis_complete(self, results):
        # Fallback: if AI returns nothing, organize by extension
        if not results and hasattr(self, 'current_files') and self.current_files:
            output = self.output_folder if self.output_folder else self.source_folder
            
            # Build reverse mapping: extension -> category
            ext_to_cat = {}
            for cat, exts in FILE_TYPE_CATEGORIES.items():
                for ext in exts:
                    ext_to_cat[ext.lower()] = cat
            
            # Create default organization by extension
            results = []
            for f in self.current_files:
                ext = os.path.splitext(f)[1].lower()
                category = ext_to_cat.get(ext, "Other")
                folder_path = os.path.join(output, category)
                results.append(FileChange(original=f, action="move", new_path=os.path.join(folder_path, os.path.basename(f))))
        
        self.analysis_results = results
        
        self.output_text.delete("1.0", "end")
        
        if not results:
            self.output_text.insert("end", "⚠️ Could not generate suggestions. Check AI connection.\n")
            self.status_label.configure(text="Analysis failed - check errors", text_color="red")
            return
        
        output = self.output_folder if self.output_folder else self.source_folder
        
        for r in results:
            filename = r.original.split(os.sep)[-1]
            self.output_text.insert("end", f"📄 {filename}\n")
            self.output_text.insert("end", f"   ➜ {r.new_path}\n\n")
        
        self.status_label.configure(text=f"✅ Analysis complete: {len(results)} files to move", text_color="green")
        
        if self.auto_execute_var.get() and results:
            self.status_label.configure(text=f"⏳ Auto-executing {len(results)} moves...", text_color="yellow")
            self._execute()
        else:
            self.execute_btn.configure(state="normal")
        
        self.analyze_btn.configure(state="normal")
    
    def _show_error(self, error):
        self.output_text.insert("end", f"❌ Error: {error}\n")
        self.output_text.see("end")
        messagebox.showerror("Error", error)
        self.status_label.configure(text="Error occurred - check output", text_color="red")
        self.analyze_btn.configure(state="normal")
    
    def _execute(self):
        if not self.analysis_results:
            return
        
        if not self.auto_execute_var.get():
            if not messagebox.askyesno("Confirm", f"Execute {len(self.analysis_results)} file operations?"):
                return
        
        self.execute_btn.configure(state="disabled")
        
        new_folders = set()
        output_base = self.output_folder if self.output_folder else self.source_folder
        
        for change in self.analysis_results:
            folder = os.path.dirname(change.new_path)
            if folder and folder != output_base:
                rel = os.path.relpath(folder, output_base)
                if os.sep in rel:
                    new_folders.add(rel.split(os.sep)[0])
                else:
                    new_folders.add(rel)
        
        FileExecutor = get_FileExecutor()
        success, errors = FileExecutor.execute(self.analysis_results)
        self.created_folders.extend(list(new_folders))
        
        self.status_label.configure(text=f"✅ Done! {success} succeeded, {errors} failed", text_color="green")
        
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", f"✅ Successfully moved: {success} files\n")
        if errors:
            self.output_text.insert("end", f"❌ Errors: {errors}\n")
        
        self.analysis_results = []


if __name__ == "__main__":
    app = NoMoreClutterApp()
    app.mainloop()
