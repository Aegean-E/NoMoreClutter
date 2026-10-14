# NoMoreClutter AI Knowledge Base 🧠📚

> **MANDATORY INSTRUCTION FOR AI AGENTS & CODING ASSISTANTS:**
> This directory (`knowledge/`) serves as the living source of truth for the codebase architecture, services, data models, UI concurrency, and design decisions.
> Whenever you add, refactor, or modify any code, you MUST update the corresponding knowledge base document(s) in this folder and run `python scripts/update_knowledge_base.py`.

---

## 🧭 Knowledge Base Catalog

| Document | Purpose | Key Topics Covered |
|----------|---------|--------------------|
| **[architecture.md](architecture.md)** | System architecture & data flow | System layers, RLM pipeline, provider abstractions, safety boundaries |
| **[services.md](services.md)** | Service layer specifications | RLM organizer, provider system, file executor, file scanner, LLM facade |
| **[data_models.md](data_models.md)** | Data structures & schemas | `FileInfo`, `FileCategory`, `ScanResult`, provider models, dense JSON formats |
| **[state_and_ui.md](state_and_ui.md)** | UI, threading, and state | CustomTkinter architecture, background threads, safe UI dispatch, settings |
| **[decisions.md](decisions.md)** | Architecture Decision Records (ADRs) | Why RLM over monolithic prompting, zero-install cloud, collision renaming, undo history |
| **[codebase_map.md](codebase_map.md)** | Auto-generated code registry | All modules, exported classes, methods, signatures, and docstrings |

---

## ⚡ Quick Architectural Overview

NoMoreClutter is an intelligent, high-performance desktop file organization application. It operates under a clean layered design:

```mermaid
flowchart TD
    UI[CustomTkinter UI Layer (main.py)]
    UI -->|Scans Directory| Scanner[services/file_scanner.py]
    UI -->|Requests Organization| Organizer[services/rlm_organizer.py]
    UI -->|Executes & Reverts Moves| Executor[services/file_executor.py]
    
    Organizer -->|Dense JSON Payloads| ProviderRegistry[services/providers/registry.py]
    ProviderRegistry -->|Routes Call| ActiveProvider[services/providers/openai_compatible.py]
    ActiveProvider -->|HTTP Requests| RemoteLLM[Cloud: Groq / Gemini / OpenAI / Local: LM Studio / Ollama]
    
    Organizer -->|Zero-AI Mode| Heuristics[Local Rule Engine]
    Executor -->|Collision-Free Rename| FileSystem[(Disk Operations)]
    Executor -->|Push Operation Log| UndoStack[Undo History Stack]
```

### Core Design Pillars
1. **Hybrid AI Access (Zero-Install Cloud + Local Server)**: Users can use ultra-fast free cloud APIs (Groq, Gemini) with zero external setup, or local servers (LM Studio, Ollama) for complete offline privacy.
2. **Recursive Language Model (RLM)**: Never dump flat lists of hundreds of files into an LLM. Files are clustered hierarchically, serialized compactly (~70% token savings), and mapped deterministically by ID.
3. **Fail-Safe Operations**: Moving files never overwrites existing files (`name (1).ext`), and all operations can be undone with a single click.

---

## 🔄 Maintaining the Knowledge Base

1. **When adding a new feature or service**: Document its design in `services.md` and data models in `data_models.md`.
2. **When modifying architectural boundaries**: Update diagrams and descriptions in `architecture.md`.
3. **When modifying UI or threading flows**: Update `state_and_ui.md`.
4. **When making key design trade-offs**: Add an ADR entry to `decisions.md`.
5. **Always run the auto-sync script**:
   ```bash
   python scripts/update_knowledge_base.py
   ```
