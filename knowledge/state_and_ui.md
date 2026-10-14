# UI Concurrency, State & Event Flow 🖥️

This document describes the presentation architecture in `main.py`, including CustomTkinter widget hierarchy, background threading, safe UI marshaling, and settings persistence.

---

## 1. UI Hierarchy

Built with CustomTkinter in a dark-mode theme:

```
NoMoreClutterApp (ctk.CTk) - Maximized / Zoomed Full-Screen on Startup (1340x880 minsize)
├── Top Navigation & Header Bar
│   ├── Branding & Subtitle ("📁 NoMoreClutter: AI-Powered Workspace Organizer")
│   ├── AI Status Badge (Interactive Clickable Pill: 🟢 Plugged / 🔴 Unplugged / 🟡 Checking)
│   ├── Utility Tool Openers ("🔍 Duplicates", "🧹 Clean Junk")
│   └── Navigation Action Deck ("🚀 1-Click Deploy", "⚙️ Settings")
└── Main Workspace Grid (Two-Column Master-Detail Layout)
    ├── Left Scrollable Control Deck:
    │   ├── Card 1: 📂 Directory Configuration (Source & Destination entries, Browse, Scan badge)
    │   ├── Card 2: 🎯 File Types to Process (2-Column Grid, Select All / Clear All toggles)
    │   └── Card 3: ⚡ Organization Control Center ("🔍 AI Organize", "⚡ Quick Organize", "🗂️ Preview & Execute", "↩ Undo Moves", Real-time status pill)
    └── Right Activity Stream & Terminal:
        ├── Header Bar (Title + "Clear Log" button)
        └── Full-Height Live Console Textbox (ctk.CTkTextbox with Consolas font)
```

---

## 2. Concurrency & Threading Model

Tkinter is not thread-safe. To prevent UI freezing during file system walks, LLM network requests, and batch file moves, all long-running tasks run in dedicated worker threads:

```
[Main Thread (Tk Event Loop)]
     │
     │ User clicks "Organize" / "Undo"
     ▼
[Spawn Daemon Worker Thread]
     │
     ├── Executes disk operations / AI calls
     ├── Posts progress via safe callbacks
     ▼
[UI Update Queue / root.after()]
     │
     ▼
[Main Thread safely updates widgets & log]
```

### Threading Rules
1. **Never block the main thread**: Network calls, file moves, and scans must never be called synchronously from Tkinter button callbacks.
2. **Safe Logging**: Worker threads invoke callback functions that schedule widget mutations onto the Tkinter loop via `self.after(0, ...)`.
3. **Daemon Threads**: All worker threads are marked `daemon=True` so closing the window immediately terminates pending background jobs.

---

## 3. Settings Persistence

- User configurations (selected provider, API key, model, check state) are loaded on startup from `settings.json`.
- When the user changes providers in the dropdown, default values (API URL, recommended model) are auto-populated.
- Whenever settings are modified, they are saved automatically to `settings.json`.
- `settings.json` is gitignored to protect user API keys.

---

## 4. Real-Time AI Plugged/Unplugged Indicator

The application displays an interactive real-time status pill in the top header and a companion indicator next to the organization action buttons:
- **`PLUGGED` State (🟢)**:
  - Header Pill: `🟢 AI Plugged: {Provider} Ready` (emerald green border `#2B8A3E`, dark green bg `#142B1A`).
  - Action Indicator: `🟢 AI Plugged`.
  - Triggered when cloud API keys are verified, local embedded GGUF weights are detected on disk, or local Ollama daemons respond.
- **`UNPLUGGED` State (🔴)**:
  - Header Pill: `🔴 AI Unplugged ({Reason})` (crimson border `#E03131`, dark red bg `#2B1414`).
  - Action Indicator: `🔴 AI Unplugged`.
  - Triggered when API keys are missing, model weights are not downloaded, or local servers are unreachable.
- **`CHECKING` State (🟡)**:
  - Header Pill: `🟡 Checking AI...` (amber border `#FAB005`, dark slate bg `#2B2514`).
  - Evaluated in a background daemon thread (`_refresh_ai_status_async`) without blocking the Tkinter event loop.
- **Interactive Click Actions**:
  - Clicking the pill when plugged shows connection details and offers a one-click connection re-test.
  - Clicking the pill when unplugged opens a guided dialog directing the user to 1-Click AI Deploy or Settings.
  - Clicking "🔍 AI Organize" when unplugged prompts the user to deploy AI or run "⚡ Quick Organize (No AI)" instead.

---

## 5. Interactive Tree Preview & Selective Execution (`ui/tree_preview.py`)

- **Hierarchical Visualizer**: Replaces blind all-or-nothing move execution with an interactive expandable tree window (`TreePreviewDialog`).
- **Destination Folder Grouping**: Files are partitioned by relative destination directories (`Invoices`, `Photos/2018`).
- **Selective Per-File Checkboxes**:
  - Folder-level `[☑ Select All]` and individual file-level checkboxes.
  - Skips unchecked files from physical moves, leaving them safely in place.
- **Search & Live Filtering**: Instant search bar dynamically hides/shows matching file rows and auto-expands parent cards.
- **Direct File Inspection**: Double-clicking any file row or clicking `👁️ Open` opens the original file via the system viewer.

---

## 6. Smart Duplicate File Finder Dialog (`ui/duplicate_finder.py`)

- **Interactive Deduplication Center**: Launched via the `🔍 Duplicates` button in the actions bar.
- **Storage Metrics**: Displays live reclaimed space badges (`💾 Reclaimable: 1.45 GB`) and redundant file counts.
- **Cluster Breakdown**: Displays canonical original files (marked 🟢 `ORIGINAL`) alongside duplicates (marked 🔴 `DUPLICATE` with pre-checked boxes).
- **Execution Safeguards**:
  - **`📦 Isolate Duplicates`**: Moves duplicates into `_Duplicates/` preserving originals.
  - **`🗑️ Delete Selected`**: Permanently removes selected duplicates after confirmation.

---

## 7. Orphan Folder & Junk Pruner Dialog (`ui/junk_cleaner.py`)

- **Deep Cleaning Center**: Launched via the `🧹 Clean Junk` button in the actions bar.
- **Triple-Scan Matrix**: Configurable checkboxes for empty subdirectories, zero-byte orphan files, and OS debris (`Thumbs.db`, `.DS_Store`).
- **Safe Leaf Pruning**: Utilizes bottom-up traversal with `os.rmdir()` to prune empty directories without risking non-empty folders.

---

## 8. In-App File Viewer & Side-by-Side Duplicate Comparator (`ui/file_viewer.py`)

- **Interactive File Inspection**: Launched via `👁️ File Viewer` in the main header bar, `👁️ Preview` in Tree Preview, or `👥 Compare` in Duplicate Finder.
- **Single-File Mode**: Previews images with Pillow aspect scaling, text/code files across multiple encodings, documents via `DocumentPeeker`, or raw binary hex dumps. Provides path copying, explorer revealing, and system opening.
- **Side-by-Side Comparator Mode**: Compares the canonical original with the duplicate candidate in real time with byte-match confirmation banners, file metadata, and direct "Delete" / "Isolate" actions.
- **Headless Test Safety**: All parsing, decoding, and scaling logic is extracted into pure functions (`get_category_badge`, `get_file_meta_summary`, `compute_image_preview_size`, `read_text_preview`, `generate_hexdump`), ensuring unit tests never instantiate GUI widgets.


