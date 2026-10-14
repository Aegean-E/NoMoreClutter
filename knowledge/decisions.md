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

---

## ADR-008: Hardware Auto-Benchmark & Camera Timestamp Anti-Hallucination Guard

### Context
1. **Uncalibrated Batch Settings**: Users running different models (ultra-fast cloud like Groq vs. slower local CPU GGUF models) had to guess optimal batch sizes and processing limits. Setting batch sizes too high on slow hardware caused long UI freezes, while setting them too low on fast cloud models wasted roundtrip latency.
2. **Camera Roll Photo Hallucinations**: When organizing photos with numeric timestamps (e.g. `20170926_112101.jpg`) with Vision disabled, models lacked semantic text context and hallucinated arbitrary categories (such as labeling an entire directory of photos as `Animals/`).

### Decision
1. **`BenchmarkService` (`services/benchmark_service.py`)**:
   - Synthesizes realistic test files across invoices, code, documents, and photos.
   - Measures actual latency and throughput against the active model.
   - Probes Vision support and suggests provider-specific vision models (`llama-3.2-11b-vision-preview`, `gemini-1.5-flash`, `moondream`).
   - Automatically calculates and applies optimal batch sizes (5 for slow local CPU, 10 for standard, 15 for fast cloud) and limits.
2. **Camera Timestamp Anti-Hallucination Guard**:
   - Added explicit prompt rules instructing the LLM to group numeric camera timestamps by date/year (e.g. `Photos/2017`) rather than guessing scene contents without Vision.
   - Added post-processing validation in `RLMOrganizer`: if an image matches `YYYYMMDD_HHMMSS` and the model returned a generic or hallucinated tag without vision, the system safely routes it to `Photos/{year}` and preserves original timestamp filenames.

### Consequences
- **Positive**: Zero-guesswork tuning tailored to user hardware; prevents bizarre photo hallucinations; provides clear guidance on when to enable Vision.

---

## ADR-009: Comprehensive Settings Architecture, Provider Auto-Detection & Persistence

### Context
1. **Settings Integrity & State Coupling**: The settings dialog manages 13 configuration controls across AI endpoints, organization rules, and performance limits. If provider switching unconditionally overwrites saved custom URLs and models, users lose custom configurations across window re-opens.
2. **Embedded GGUF Provider Dispatch**: Calling `LLMService` without explicitly passing `provider_id="embedded"` when `base_url="local://embedded"` caused fallback to `OpenAICompatibleProvider`, triggering invalid network requests instead of invoking `EmbeddedProvider`.
3. **Category Selection Volatility**: Category checkboxes (Documents, Images, Audio, Video, Archives, Code) were not persisted to `settings.json`, resetting to all-enabled on every restart.
4. **Deterministic Setting Enforcement**: Options like `ai_rename=False` and `create_folders=False` occasionally suffered from LLM non-compliance unless enforced deterministically at post-processing.

### Decision
1. **Self-Healing Provider Auto-Detection**:
   - `LLMService.__init__` automatically inspects `base_url` and detects `"local://embedded"`, switching `provider_id` to `"embedded"`.
   - UI callers (`_test_connection`, `_analyze_thread`) resolve preset IDs before dispatch.
2. **Protected Settings Preservation**:
   - `_update_provider_ui` accepts a `force_defaults: bool` flag. When initializing from disk, existing custom `llm_url` and `llm_model` values are preserved rather than overwritten by preset defaults.
3. **Full Settings & Category Persistence**:
   - `included_categories` map is saved and loaded in `settings.json`, preserving checkbox filters across application sessions.
4. **Deterministic Option Enforcement**:
   - When `ai_rename=False`, original filename is preserved in code regardless of LLM generation.
   - When `create_folders=False` with no existing folders, files are placed in destination root rather than arbitrary subfolders.
   - `_quick_organize` respects `limit`, `numbered_rename`, and `create_folders`.

### Consequences
- **Positive**: Every setting operates deterministically and predictably in both AI Organize and Quick Organize modes; zero settings drift across restarts.

---

## ADR-010: Continuous Mathematical Slider Auto-Tuning Architecture

### Context
1. **Rigid Coarse Tiers**: Earlier benchmark implementations mapped latency into 3 rigid, hardcoded tiers (<900ms -> 15 & 100; 900-2500ms -> 10 & 50; >2500ms -> 5 & 25).
2. **Static Text Entries**: Settings like batch size and file limits were presented as plain text boxes without tactile feedback, visual range constraints, or live value badges.
3. **Missing Context & Pacing Sliders**: Document peeking context budget (token overhead) and inter-batch pacing delay (TPM rate limiting) were hardcoded rather than being tunable and auto-calibrated to user hardware.

### Decision
1. **Continuous Mathematical Auto-Tuning (`BenchmarkService`)**:
   - Replaced coarse steps with continuous formulas based on measured latency ($L_{ms}$) and throughput ($TPS$):
     - $\text{Batch Size} = \text{clamp}\left(\text{round}\left(25 \times (500 / \max(L_{ms}, 500))^{0.65}\right), 3, 25\right)$
     - $\text{File Limit} = \text{clamp}\left(\text{round}\left(\frac{35000}{L_{ms}} \times \frac{B}{5} \times 12 / 5\right) \times 5, 15, 200\right)$
     - $\text{Context Peek} = \text{clamp}\left(\text{round}\left((250 - L_{ms} / 35) / 10\right) \times 10, 100, 250\right)$
     - $\text{Pacing Delay} =$ Adaptive delay (0.0s for high TPM/local GPU, 0.15s for Groq, 0.20s-0.35s for local CPU cooldown).
2. **Interactive Slider UI Controls (`main.py`)**:
   - Implemented `CTkSlider` controls with live badges for Batch Size (1–30), File Limit (0–250), Context Peek (50–350), and Pacing Delay (0.0s–2.0s).
   - "Apply Recommended Settings" smoothly updates all 4 sliders to the exact measured optimal points.
   - Dual-mode synchronization ensures full backward compatibility with manual entry inputs.

### Consequences
- **Positive**: Exact, bespoke calibration for every user machine; tactile and intuitive UI; eliminates rate-limit errors and thread starvation.
- **Negative**: Benchmark takes 1-2 seconds to complete when manually triggered by user.

---

## ADR-011: Vision Capability Safeguards and Graceful Text RLM Fallback

### Context
1. **Spammed Vision Errors**: When running against an image folder using embedded in-process GGUF models (`EmbeddedProvider`) or text-focused local models with `analyze_images=True`, `EmbeddedProvider.analyze_image()` raised `NotImplementedError` on every image file. `_process_images_hierarchical()` caught the exception per file, dumped error logs for 100+ files to stdout, and dumped all images into a generic `Images/` folder.
2. **Text Model Camera Hallucinations**: When photos with numeric timestamps (e.g., `20170926_112101.jpg`) were sent to text models without vision, the models hallucinated generic tags like `Animals/` or `Cars/`.
3. **UI Mismatch**: In Settings, the AI Vision checkbox remained active when switching to text-only presets without visual indication.

### Decision
1. **Provider Capability Flag**:
   - Added `@property def has_vision(self) -> bool` to `BaseAIProvider` (defaults to `True`), `EmbeddedProvider` (`False`), and `ProviderPreset` (`bool(vision_model)`).
2. **Graceful Engine Fallback (`RLMOrganizer`)**:
   - Pre-checks `getattr(self.provider, "has_vision", True)` before attempting image vision analysis.
   - If vision fails or raises `NotImplementedError`, it immediately aborts the vision loop on the first failure, emits a single informative message, and routes all images into `_process_regular_rlm()`.
3. **Robust Camera Timestamp Anti-Hallucination Guard**:
   - In `_analyze_cluster()`, files with numeric camera timestamps (e.g. `20170926_112101.jpg`, `20200818170048...webp`, `20220813...jpg`) are automatically sorted into `Photos/{year}/` (e.g. `Photos/2017/`), preserving original filenames rather than hallucinating categories.
4. **UI Guidance & Auto-Disabling (`main.py`)**:
   - Automatically disables or warns on the vision checkbox when text-only models (like Embedded GGUF) are selected.

### Consequences
- **Positive**: Zero terminal error spam, zero dropped images, seamless date-based grouping for camera rolls, and clear UI feedback.





