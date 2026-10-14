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
│  │  document_peeker.py  │◄──────────────┤              │
│  │(Zero-dep text peek)  │               │              │
│  └──────────────────────┘               │              │
│  ┌──────────────────────┐               │              │
│  │   file_executor.py   │◄──────────────┘              │
│  │(Persistent disk undo)│                              │
│  └──────────────────────┘                              │
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
- **`document_peeker.py`**:
  - Zero-dependency document text extractor for intelligent content-based sorting.
  - Extracts budgeted snippets ($\le 200$ chars) from PDF, Word (`.docx`), Markdown, and code/text files without bloated third-party libraries.
  - Feeds `"peek"` previews directly into dense RLM payloads.
- **`file_executor.py`**:
  - Safely moves/copies files to target directories with collision resolution (`stem (n).ext`).
  - Atomically writes batch operations to `history.json` for persistent multi-session undo.
  - Detects past sessions on launch, enabling one-click rollbacks across restarts.
  - Performs reverse-order rollbacks and automatically prunes empty destination directories.
- **`model_downloader.py`**:
  - 1-click model streaming utility downloading compact GGUF weights directly from HuggingFace.
  - Atomic rename and cancellation support via standard library `urllib`.
- **`ollama_manager.py`**:
  - 1-click discovery, connection check, and streaming model pull via local Ollama REST API.
- **`llm_service.py`**:
  - Backward-compatible facade bridging existing scripts and tests to the new RLM and Provider engine.

### 2.3 Provider Layer (`services/providers/`)
- **`base.py`**: Abstract interface (`BaseAIProvider`) defining `complete()`, `analyze_image()`, and `test_connection()`.
- **`registry.py`**: Factory and catalog storing configurations for all supported cloud, local, and embedded providers.
- **`embedded.py`**: In-process GGUF inference provider executing downloaded models offline via `llama-cpp-python`.
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
       * Documents/Code with peeking enabled -> document_peeker.peek() injected into payload
       * Non-images or text files -> provider.chat() with dense JSON
     - If provider fails or not configured -> heuristic rule engine
     - Parse response & map strictly by integer file ID
6. file_executor.py receives List[Tuple[FileInfo, str, Optional[str]]]
7. Move files with collision avoidance
8. Batch operation atomically saved to history.json (persistent across restarts)
9. UI notified: progress complete, logs written, Undo button enabled
```

### 3.2 Undo Pipeline
```
1. User clicks "↩ Undo Moves" (enabled on launch if history.json contains past sessions)
2. file_executor.undo_last_batch() pops the most recent batch from history.json
3. For each moved file (in reverse order):
     - Safely moves file back to original path with collision resolution
     - Deletes newly created empty directories
4. Updates or clears history.json atomically
5. UI reflects restoration count and remaining batches in console log
```

---

## 4. Key Architectural Guarantees
- **No Data Overwrite**: Files cannot accidentally overwrite existing files.
- **Token Efficiency**: Payloads never exceed prompt budgets; rate limits are observed with adaptive pacing (**PRINCIPLE-009**).
- **Decoupled AI Engine**: The core organizer works regardless of whether the provider is Groq, Gemini, OpenAI, LM Studio, Ollama, or a local heuristic (**PRINCIPLE-003**, **PRINCIPLE-008**).
- **Empirical Grounding (Zero Hallucination)**: Read-before-write validation, verified disk paths, and AST confirmation before code execution (**PRINCIPLE-014**).
- **Compaction & Disruption Resilience**: All task state is externalized to atomic disk records (`task_ledger.json`, WAL history); agents re-anchor against disk status upon compaction resume (**PRINCIPLE-012**, **PRINCIPLE-013**, **PRINCIPLE-015**).
