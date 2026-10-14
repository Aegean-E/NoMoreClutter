# Architecture Decision Records (ADRs) 📜

This document preserves the rationale, context, and consequences of critical architectural decisions.

---

## ADR-001: RLM Hierarchical Decomposition vs. Flat Batching

### Context
Sending hundreds or thousands of raw file paths directly into an LLM prompt leads to:
1. Context window exhaustion.
2. Rapid exhaustion of free-tier rate limits (e.g. Groq TPM caps).
3. "Attention dilution" and hallucinated file names.
4. Latency spikes and cost increases.

### Decision
Implement a Recursive Language Model (RLM) engine (`services/rlm_organizer.py`). Files are first partitioned into logical category clusters. Each cluster is serialized into dense JSON payloads using relative IDs rather than long absolute paths. Responses are deterministically mapped by ID.

### Consequences
- **Positive**: Cuts token overhead by ~70%. Guarantees that free-tier rate limits are respected. Eliminates off-by-one mapping errors.
- **Negative**: Adds an intermediate clustering step before dispatching requests.

---

## ADR-002: Zero-Install Cloud Providers with Local Fallback (Hybrid AI)

### Context
Requiring users to download heavy desktop apps (LM Studio, Ollama) before organizing their first file introduces substantial friction and turns away casual users. However, power users demand local self-hosted privacy.

### Decision
Support both paradigms seamlessly via a pluggable provider abstraction (`services/providers/`). Provide pre-configured cloud presets (Groq with free keys, Google Gemini, OpenAI, OpenRouter) alongside local servers (LM Studio, Ollama) and a 100% offline heuristic fallback.

### Consequences
- **Positive**: "One-click and start" accessibility for new users while retaining full privacy and power for local users.
- **Negative**: Requires maintaining provider presets and testing multiple endpoint types.

---

## ADR-003: Collision Avoidance and Batch Undo Stack

### Context
File operations can be destructive if destination folders already contain files with the same name, or if the user is dissatisfied with AI organization decisions.

### Decision
1. Dynamic collision renaming: if `destination/file.ext` exists, automatically generate `destination/file (1).ext`.
2. Batch undo: every file move is recorded as a `FileMoveRecord(original, new, timestamp)` and pushed to an undo stack. Users can roll back the entire batch with one click.

### Consequences
- **Positive**: Zero risk of accidental file overwrites or data loss. High user confidence.
- **Negative**: Memory overhead for the undo stack (negligible for typical batches).

---

## ADR-004: Living Principles System & Automated Cross-AI Synchronization

### Context
Different developers and AI assistants (Gemini, Claude, Cursor, Copilot) enter this repository across different workflows. Disconnected guidelines lead to knowledge drift and conflicting changes.

### Decision
Establish `AGENTS.md` as the master canonical specification. Implement `scripts/sync_principles.py` and `scripts/update_knowledge_base.py` to programmatically synchronize all guidelines (`GEMINI.md`, `CLAUDE.md`, `.cursorrules`, `.agents/rules/`, `.github/copilot-instructions.md`) and validate the knowledge base.

### Consequences
- **Positive**: 100% consistency across all AI assistants; eliminates knowledge drift.
- **Negative**: AI assistants must run sync scripts whenever principles or architecture change.

---

## ADR-005: Automated Test Verification & Continuous Test Coverage (Regression Shield)

### Context
Frequent additions, refactorings, or modifications made across disparate AI sessions risk breaking existing service interfaces, corrupting data mappings, or regressing path calculation logic.

### Decision
Codify `PRINCIPLE-011: Automated Test Verification & Continuous Test Coverage`. Every change must be paired with dedicated unit tests in `tests/`, and the complete test suite must be executed and confirmed 100% green before any commit is finalized.

### Consequences
- **Positive**: Complete regression protection, rapid feedback cycle (<0.1s run time), clean CI-ready test baseline.
- **Negative**: Requires writing unit test fixtures for each new feature or refactor.

---

## ADR-006: 1-Click AI Model Quick-Deploy (Embedded GGUF, Ollama Auto-Pilot, and Cloud Connect)

### Context
New users often find setting up local LLM servers (LM Studio, Ollama CLI) or obtaining cloud API keys to be friction-heavy. To make AI organization truly "one-click", the application needed an automated way to download, stream, and deploy AI models.

### Decision
Implement a multi-path 1-Click Quick Deploy architecture:
1. **Embedded Local GGUF**: Downloads quantized weights (`Qwen 2.5 1.5B/0.5B`, `SmolLM2 1.7B`) from HuggingFace via `urllib.request` with streaming progress bars, cancellation, and atomic writes. Runs offline via `EmbeddedProvider`.
2. **Ollama Auto-Pilot**: Interacts with local Ollama daemon via REST API to pull models (`llama3.2:1b`, etc.) without terminal commands.
3. **Instant Free Cloud**: Streamlined 1-click wizard to activate free Groq or Google Gemini keys.

### Consequences
- **Positive**: True zero-friction onboarding (PRINCIPLE-008); users can deploy an AI model in a single click with visual progress.
- **Negative**: Model weights require disk space (~400MB to ~1GB), managed safely outside git via `.gitignore`.

---

## ADR-007: Persistent Multi-Session Undo & Zero-Dependency Document Peeking

### Context
1. **Volatile Undo**: Reorganizing files in prior versions relied solely on an in-memory stack. If a user closed the app or experienced a crash, all undo capability was lost.
2. **Cryptic File Names**: Many scanned or downloaded files have ambiguous names (e.g. `Scan_001.pdf`, `doc_final.docx`, `export.csv`). Categorizing purely on filenames caused inaccurate grouping. Heavy text-extraction libraries (`pypdf`, `python-docx`, `tika`) would violate lean dependency principles (PRINCIPLE-007).

### Decision
1. **Atomic Disk History (`history.json`)**:
   - `FileExecutor` persists batch operations to `history.json` via atomic `.tmp` replacement.
   - On startup, `FileExecutor.has_undo()` automatically detects past sessions, enabling the Undo button with summary notices.
   - Rollbacks occur in reverse chronological order, safely resolve collisions, and clean up newly empty destination folders.
2. **Zero-Dependency Document Peeking (`services/document_peeker.py`)**:
   - Text/code files are read directly with UTF-8 / latin-1 fallback.
   - `.docx` documents are inspected using Python standard library `zipfile`, reading `<w:t>` tags from `word/document.xml`.
   - `.pdf` documents are inspected for uncompressed text blocks and decompressed FlateDecode streams using Python standard library `zlib`.
   - Extracted snippets are strictly capped at $\le 200$ characters and whitespace-sanitized to preserve token frugality (PRINCIPLE-009).
   - Injected into dense RLM organizer payloads under the `"peek"` key.

### Consequences
- **Positive**: Reorganize operations can be undone days or weeks later across reboots; semantic categorization accuracy is dramatically elevated; zero external pip dependencies added; token overhead is bounded and lean.
- **Negative**: Incur negligible disk I/O when reading the first few bytes of documents during planning.


