# Service Layer Specification ⚙️

This document provides a deep dive into the business logic services in `services/`.

---

## 1. `RLMOrganizer` (`services/rlm_organizer.py`)

The recursive organization engine responsible for intelligent file categorization and token optimization.

### Key Concepts
- **Hierarchical Clustering**: Groups files by broad category domain (e.g., `IMAGES`, `DOCUMENTS`, `CODE`) before prompting.
- **Dense Token Payloads**: Serializes candidate files into compact JSON records:
  ```json
  [
    {"id": 0, "name": "invoice_march.pdf", "ext": ".pdf"},
    {"id": 1, "name": "portrait_john.png", "ext": ".png"}
  ]
  ```
  This reduces prompt token overhead by **~70%** compared to verbose absolute paths.
- **Deterministic ID Resolution**: Maps responses via `res["id"] -> file_lookup[id]`. This prevents hallucinations or array offset errors from corrupting file paths.

### Methods
- `cluster_files(files: List[FileInfo]) -> Dict[str, List[FileInfo]]`:
  Partitions files into logical buckets to optimize batch size and prompt context.
- `build_dense_payload(files: List[FileInfo]) -> str`:
  Encodes file metadata into a minimal JSON array string.
- `organize_batch(files: List[FileInfo], existing_categories: List[str] = None, allow_new_categories: bool = True, rename_files: bool = True) -> List[Tuple[FileInfo, str, Optional[str]]]`:
  Processes a batch of files through the configured provider, falling back to heuristic categorization if the provider fails.
- `organize_heuristic(files: List[FileInfo]) -> List[Tuple[FileInfo, str, Optional[str]]]`:
  Instant local rule-based organization based on file extensions and sub-types.
- `analyze_image_single_pass(image_path: str, existing_categories: List[str] = None) -> Tuple[str, Optional[str]]`:
  Performs single-pass vision analysis to extract both category and descriptive filename.
- `has_vision` Pre-check & Graceful Fallback:
  Before running vision on image files, checks `getattr(provider, "has_vision", True)`. If unsupported or `NotImplementedError` is raised, routes images seamlessly into text RLM (`Photos/YYYY` date albums and semantic clusters) without error spam.

---

## 2. Pluggable Providers (`services/providers/`)

### Abstract Interface: `BaseAIProvider` (`base.py`)
```python
class BaseAIProvider(ABC):
    @property
    def has_vision(self) -> bool:
        """Indicates whether this provider supports multimodal image vision analysis."""
        return True

    @abstractmethod
    def test_connection(self, model: Optional[str] = None) -> Tuple[bool, str]:
        """Test API connectivity and return (success, message)."""

    @abstractmethod
    def complete(self, prompt: str, model: str, temperature: float = 0.2, max_tokens: int = 1500) -> str:
        """Execute text completion."""

    @abstractmethod
    def analyze_image(self, image_path: str, prompt: str, model: str, max_tokens: int = 100) -> str:
        """Execute vision analysis on a local image."""
```

### Provider Registry: `ProviderRegistry` (`registry.py`)
Maintains presets and factory constructors:
- **`ProviderType`**: Enum with `GROQ`, `GEMINI`, `OPENAI`, `OPENROUTER`, `LM_STUDIO`, `OLLAMA`, `CUSTOM`.
- **`PRESETS`**: Pre-configured dictionary mapping provider names to default endpoints, recommended models, and documentation links.
- **`create_provider(...)`**: Factory method instantiating the appropriate provider client.

### Standard Client: `OpenAICompatibleProvider` (`openai_compatible.py`)
Implements `BaseAIProvider` over standard OpenAI-compatible REST endpoints.
- Auto-encodes images to Base64 data URLs for vision models.
- Gracefully handles connection timeouts and API error formatting.

---

## 3. `FileExecutor` (`services/file_executor.py`)

Handles safe disk operations and maintains persistent, multi-session rollback history.

### Safety Features
- **Collision Avoidance**: If `Target/report.pdf` exists, `_resolve_collision()` automatically increments to `Target/report (1).pdf`, `Target/report (2).pdf`, etc.
- **Persistent Multi-Session Undo**: All executed batches are logged to `history.json` via crash-proof atomic write (`history.json.tmp` -> replace). Undo operations persist and remain available across application restarts.
- **Reverse-Order Rollback**: `undo_last_batch()` restores files in strict reverse order to original locations with collision handling, and automatically cleans up empty created destination directories.
- **Legacy Compatibility**: Automatically parses both dictionary batch records and legacy raw list formats.

### Methods
- `execute(changes: List[FileChange]) -> Tuple[int, int]`:
  Safely moves/copies files, creates parent directories, records batch with timestamp to persistent history, and returns `(success_count, error_count)`.
- `undo_last_batch() -> Tuple[int, int]`:
  Reverts the most recent batch from `history.json`, cleans empty folders, and updates disk persistence.
- `has_undo() -> bool`:
  Checks if any undo operations are available across past or current sessions.
- `get_history_summary() -> List[Dict[str, Any]]`:
  Returns structured summary of past batches (`batch_id`, `timestamp_str`, `count`) for UI display and status indicators.
- `clear_history()`:
  Resets in-memory history and purges `history.json` from disk.

---

## 4. `FileScanner` (`services/file_scanner.py`)

Discovers and filters files from source folders.

### Methods
- `scan_directory(directory: str, selected_categories: Optional[List[FileCategory]] = None, max_files: int = 1000) -> ScanResult`:
  Walks directory, inspects file extensions, ignores hidden and system files, and returns categorized `ScanResult`.

---

## 5. `LLMService` (`services/llm_service.py`)

Facade maintaining backward compatibility for existing scripts, tests, and UI components while delegating to the new `RLMOrganizer` and `ProviderRegistry`.

### Methods
- `test_connection(model: Optional[str] = None) -> Tuple[bool, str]`:
  Delegates connection test to the underlying active AI provider.
- `check_ai_status(provider_name: Optional[str], base_url: Optional[str], api_key: Optional[str], model: Optional[str]) -> Tuple[bool, str, str]`:
  Evaluates whether an AI provider is plugged in (ready/connected) or unplugged:
  - Validates API key presence for cloud presets without latency.
  - Verifies local GGUF model presence on disk for embedded offline inference.
  - Pings local Ollama/LM Studio daemons with status checks.
  - Runs safe, non-blocking connection tests against configured endpoints.
  - Returns `(is_plugged, badge_label, detailed_description)`.
- `analyze_files(...) -> List[FileChange]`:
  Dispatches files to the `RLMOrganizer` hierarchical engine with token budgeting, content peeking, and image analysis.

---

## 6. `ModelDownloader` (`services/model_downloader.py`)

Provides 1-click model weight streaming, tracking, and atomic storage for embedded offline AI models.
- **`ModelCatalogItem`**: Data model representing downloadable GGUF models with `has_vision`, `capability_badge` (`[👁️ Vision Supported]` vs `[📝 Text-Only]`), `mmproj_filename`, `mmproj_url`, `mmproj_size_mb`, and `total_size_mb`.
- **`GGUF_CATALOG`**: Curated catalog of compact quantized models:
  - `qwen2.5-1.5b`: Recommended text model (~986 MB).
  - `moondream2-vision`: Multimodal vision & text model (~2.7 GB text + ~868 MB `mmproj` projector = ~3.5 GB total).
  - `qwen2.5-0.5b`: Ultra-light text model (~398 MB).
  - `smollm2-1.7b`: Compact HuggingFace text model (~1.06 GB).
- **`download_model(...)`**: Chunked streaming download from HuggingFace with progress callbacks, atomic `.part` replacement, and `threading.Event` cancellation. Supports multi-file downloads (base language model + multimodal `mmproj` vision projector).
- **`is_model_downloaded(...)`**: Verifies presence and valid size (>10 MB) of local weights in `models/weights/`. If the model specifies an `mmproj` projector, verifies that both files exist locally.
- **`get_mmproj_path(...)`**: Resolves path to the multimodal projector file associated with a given model filename.

---

## 7. `OllamaManager` (`services/ollama_manager.py`)

Provides 1-click Ollama discovery and streaming model pulling via local REST API (`http://localhost:11434`).
- **`check_status(...)`**: Non-blocking ping of `GET /api/tags`.
- **`list_installed_models(...)`**: Inspects tags of locally installed models in Ollama.
- **`pull_model(...)`**: Sends `POST /api/pull` with `stream: true`, parsing streaming progress updates.
- **`RECOMMENDED_OLLAMA_MODELS`**: Curated recommendations with capability badges:
  - `llama3.2:1b` `[📝 Text-Only]` (~1.3 GB).
  - `qwen2.5:1.5b` `[📝 Text-Only]` (~986 MB).
  - `llama3.2:3b` `[📝 Text-Only]` (~2.0 GB).
  - `moondream:latest` `[👁️ Vision Supported]` (~1.7 GB).
  - `llama3.2-vision:latest` `[👁️ Vision Supported]` (~7.9 GB).

---

## 8. `LlamaServerManager` (`services/llama_server_manager.py`)

Provides 1-click download, process lifecycle management, and high-performance local inference via the official standalone precompiled `llama-server.exe` binary (PRINCIPLE-003, PRINCIPLE-007, PRINCIPLE-008).
- **Zero Python Dependencies**: Operates completely independently of Python C++ bindings (eliminates MSVC and `llama-cpp-python` installation hurdles).
- **Official Pinned & Dynamic Releases**: Streams official Windows CPU (AVX2-optimized) releases directly from `ggml-org/llama.cpp` GitHub releases into `models/bin/` with live percentage progress and atomic extraction.
- **Process Lifecycle Management**: Spawns `llama-server.exe` as a lightweight background subprocess with hidden console (`CREATE_NO_WINDOW`), non-blocking health polling (`/health`), and automatic exit cleanup (`atexit.register`).
- **Text & Multimodal Vision Inference**:
  - `complete(prompt, model_path, ...)`: Dispatches prompt to `/v1/chat/completions` using standard OpenAI JSON schema over local HTTP.
  - `analyze_image(image_path, prompt, model_path, mmproj_path, ...)`: Dispatches native base64 image payloads to `/completion` (or `/v1/chat/completions`) with multimodal projector support for 100% offline vision inspection.

---

## 9. `DocumentPeeker` (`services/document_peeker.py`)

Zero-dependency lightweight content extractor for intelligent semantic file organization (PRINCIPLE-007, PRINCIPLE-009).

### Key Concepts
- **Zero Heavy Dependencies**: Uses standard Python libraries (`zipfile`, `re`, `zlib`) without pulling in heavy binary dependencies (`pypdf`, `python-docx`, `tika`).
- **Token-Budgeted Snippets**: Enforces strict character limits (default `max_chars=200`, truncated with `...`) to prevent token window exhaustion and preserve TPM quotas.
- **Whitespace Sanitization**: Strips control characters, collapses newlines and repeated tabs into single spaces for clean single-line JSON prompt embedding.

### Supported File Formats
- **Plain Text / Code**: `.txt`, `.md`, `.markdown`, `.rst`, `.csv`, `.tsv`, `.json`, `.xml`, `.html`, `.css`, `.js`, `.ts`, `.py`, `.java`, `.c`, `.cpp`, `.h`, `.cs`, `.go`, `.rs`, `.sh`, `.bat`, `.ps1`, `.yaml`, `.yml`, `.ini`, `.cfg`, `.conf`, `.sql`, `.log`.
- **Word Documents (`.docx`)**: Unzips `word/document.xml` using stdlib `zipfile` and parses `<w:t>` tags via regex.
- **PDF Documents (`.pdf`)**: Scans initial bytes for uncompressed `BT ... ET` text streams and decompresses FlateDecode zlib streams with standard `zlib`.

### Methods
- `peek(file_path: str, max_chars: int = 200) -> str`:
  Dispatches to format-specific readers based on file extension; returns a sanitized, token-budgeted text preview (or `""` if unsupported or unreadable).

---

## 10. `BenchmarkService` (`services/benchmark_service.py`)

Automated hardware performance benchmarking and continuous settings auto-tuner (PRINCIPLE-007).

### Key Concepts
- **Lightweight Synthetic Testing**: Tests the active AI model against realistic synthetic payloads (invoices, Python scripts, camera timestamps, markdown docs, and archives).
- **Latency & Throughput Measurement**: Measures millisecond response latency and tokens-per-second throughput to classify hardware tiers (Ultra-Fast Cloud, Standard, Conservative).
- **Vision Capability Probing**: Detects whether the active model or provider supports multimodal visual photo inspection.
- **Continuous Mathematical Slider Auto-Tuning**: Computes continuous, mathematically-derived optimal points rather than rigid coarse steps:
  - **Batch Size Slider** ($B_{opt}$): Smoothly scaled with $25 \times (500 / \max(L_{ms}, 500))^{0.65}$, clamped between 3 and 25 files/cluster.
  - **Max File Limit Slider** ($Limit_{opt}$): Calibrates session duration to ~30-45s based on measured throughput and batch size, clamped between 15 and 200 files.
  - **Document Peek Snippet Slider** ($Peek_{opt}$): Calibrates token context budget between 100 and 250 characters based on latency.
  - **Inter-Batch Pacing Slider** ($Pacing_{opt}$): Tailored to endpoint characteristics (0.0s for Gemini/OpenAI, 0.15s for Groq free-tier TPM, 0.2s-0.35s for local CPU cooldown).

### Methods
- `run_benchmark(provider, model: str, provider_name: str, progress_callback=None) -> BenchmarkResult`:
  Runs the benchmark suite, measures latency and compliance, probes vision capability, and returns a structured `BenchmarkResult` with continuous slider recommendations.

---

## 11. `DeduplicationService` (`services/deduplicator.py`)

Zero-dependency, high-speed $O(N)$ two-stage duplicate file finder and storage reclaimer (PRINCIPLE-007).

### Key Concepts
- **Two-Stage Hashing Algorithm**:
  - **Stage 1 (Size Indexing)**: Groups files by exact file size. Files with unique sizes are skipped without reading any bytes ($O(1)$).
  - **Stage 2 (Chunked Hashing)**: For files sharing exact byte counts, reads an initial 8KB header hash to filter out false positives. Only matching headers are subjected to full streaming SHA-256 (64KB chunks).
- **Cluster Hierarchy**:
  - Automatically identifies the canonical original (oldest modification time `mtime` or shortest path) and marks the rest as redundant duplicates.
- **Safety Actions**:
  - `isolate_duplicates(duplicates, base_folder)`: Moves duplicates safely into `_Duplicates/` with collision-safe names (`file (1).ext`) without data loss.
  - `delete_duplicates(duplicates)`: Permanently deletes redundant copies while leaving originals intact.

---

## 12. `CleanerService` (`services/cleaner_service.py`)

Safe, recursive orphan folder pruner and operating system debris cleaner (PRINCIPLE-003, PRINCIPLE-007).

### Key Concepts
- **Bottom-Up Leaf Traversal**:
  - Identifies empty directory branches from the deepest leaf folders upward (`os.walk(..., topdown=False)`).
  - Uses `os.rmdir()` which strictly refuses to delete directories containing files, preventing accidental data loss.
- **Zero-Byte File Pruning**:
  - Identifies 0-byte abandoned temporary files (`.tmp`, incomplete downloads).
- **Operating System Debris**:
  - Detects Windows and macOS metadata artifacts (`Thumbs.db`, `.DS_Store`, `desktop.ini`, `ehthumbs.db`, `.Spotlight-V100`).
- **Structured Report**:
  - Returns a `CleanupReport` detailing empty folders pruned, zero-byte files removed, OS debris removed, and total bytes reclaimed.



