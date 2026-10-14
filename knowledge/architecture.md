# System Architecture 🏛️

This document describes the high-level architecture, module boundaries, control flows, and structural design of NoMoreClutter.

---

## 1. Architectural Layers

NoMoreClutter follows a clean separation of concerns:

```
┌────────────────────────────────────────────────────────┐
│                   Presentation Layer                   │
│                        main.py                         │
│  (CustomTkinter UI, Asynchronous Threads, Dialogs)    │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                    Service Layer                       │
│  ┌──────────────────────┐    ┌──────────────────────┐  │
│  │   file_scanner.py    │    │   rlm_organizer.py   │  │
│  │ (Directory traversal)│    │(Hierarchical cluster)│  │
│  └──────────────────────┘    └──────────┬───────────┘  │
│  ┌──────────────────────┐               │              │
│  │   file_executor.py   │               │              │
│  │(Safe moves & Undo)   │               │              │
│  └──────────────────────┘               │              │
└─────────────────────────────────────────┼──────────────┘
                                          │
┌─────────────────────────────────────────▼──────────────┐
│                    Provider Layer                      │
│                services/providers/                     │
│  ┌────────────────────┐      ┌──────────────────────┐  │
│  │      base.py       │      │     registry.py      │  │
│  │ (Provider contract)│      │  (Preset catalog)    │  │
│  └─────────▲──────────┘      └──────────┬───────────┘  │
│            │                            │              │
│  ┌─────────┴────────────────────────────▼───────────┐  │
│  │              openai_compatible.py                │  │
│  │  (Groq, Gemini, OpenAI, LM Studio, Ollama)      │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

---

## 2. Component Roles & Boundaries

### 2.1 UI Layer (`main.py`)
- **Presentation Only**: Handles widgets, theme styling, directory picking, user events, and real-time status logging.
- **Strictly Non-Blocking**: UI callbacks launch background worker threads (`threading.Thread(daemon=True)`) for disk I/O, AI calls, and batch moves.
- **Thread-Safe Dispatch**: Log updates and progress bar ticks are dispatched back to the Tkinter event loop via thread-safe callbacks or queued UI updates.

### 2.2 Service Layer (`services/`)
- **`file_scanner.py`**:
  - Recursively or shallowly traverses directories.
  - Categorizes files by extension into `FileCategory` buckets (`IMAGES`, `DOCUMENTS`, `AUDIO`, `VIDEO`, `ARCHIVES`, `CODE`).
  - Returns structured `ScanResult` and `FileInfo` objects.
- **`rlm_organizer.py`**:
  - Implements the Recursive Language Model (RLM) engine.
  - Partitions files into semantic clusters before querying the LLM.
  - Serializes files into dense JSON schemas (`id`, `name`, `ext`) saving ~70% token budget.
  - Enforces deterministic ID-to-file mapping.
  - Provides a 100% offline, zero-AI heuristic fallback.
- **`file_executor.py`**:
  - Moves files safely to target directories.
  - Dynamically prevents collisions using `stem (n).ext`.
  - Maintains an undo operation history stack enabling batch rollback.
- **`llm_service.py`**:
  - Backward-compatible facade bridging existing scripts and tests to the new RLM and Provider engine.

### 2.3 Provider Layer (`services/providers/`)
- **`base.py`**: Abstract interface (`BaseAIProvider`) defining `chat()`, `chat_vision()`, and `test_connection()`.
- **`registry.py`**: Factory and catalog storing configurations for all supported cloud and local providers.
- **`openai_compatible.py`**: Robust client using the official `openai` SDK with timeout handling, base URL redirection, and error sanitization.

---

## 3. Data Flow Pipelines

### 3.1 AI Organization Pipeline
```
1. User clicks "🚀 Organize Files"
2. main.py creates worker thread
3. file_scanner.py returns List[FileInfo]
4. rlm_organizer.py groups files into Clusters
5. For each Cluster:
     - Check file types:
       * Images with vision enabled -> provider.chat_vision()
       * Non-images or text files  -> provider.chat() with dense JSON
     - If provider fails or not configured -> heuristic rule engine
     - Parse response & map strictly by integer file ID
6. file_executor.py receives List[Tuple[FileInfo, str, Optional[str]]]
7. Move files with collision avoidance
8. Operation batch saved to undo stack
9. UI notified: progress complete, logs written
```

### 3.2 Undo Pipeline
```
1. User clicks "↩ Undo Moves"
2. file_executor.undo_last_batch() pops the last BatchOperation
3. For each moved file (in reverse order):
     - Safely moves file back to original path
     - Deletes newly created empty directories
4. Returns count of restored files
5. UI reflects restoration in console log
```

---

## 4. Key Architectural Guarantees
- **No Data Overwrite**: Files cannot accidentally overwrite existing files.
- **Token Efficiency**: Payloads never exceed prompt budgets; rate limits are observed with adaptive pacing.
- **Decoupled AI Engine**: The core organizer works regardless of whether the provider is Groq, Gemini, OpenAI, LM Studio, Ollama, or a local heuristic.
