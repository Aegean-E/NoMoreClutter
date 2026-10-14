# UI Concurrency, State & Event Flow 🖥️

This document describes the presentation architecture in `main.py`, including CustomTkinter widget hierarchy, background threading, safe UI marshaling, and settings persistence.

---

## 1. UI Hierarchy

Built with CustomTkinter in a dark-mode theme:

```
NoMoreClutterApp (ctk.CTk)
├── Header & Title Frame
│   ├── Logo / Title Label
│   └── Settings & Connection Status Indicators
├── Top Control Area
│   ├── Directory Selector (Entry + Browse Button)
│   └── Provider & Key Controls (Provider Dropdown, API Key, Model Entry, Test Button)
├── Main Workspace (Split / Tabbed Panes)
│   ├── Category Selection Checkboxes (Images, Documents, Media, Code, Archives)
│   ├── Action Controls:
│   │   ├── "⚡ Quick Organize (No AI)"
│   │   ├── "🚀 Organize Files"
│   │   └── "↩ Undo Moves"
│   └── Real-time Console Log (ctk.CTkTextbox with autoscroll)
└── Status Bar (Progress Bar, Current State, File Counters)
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
