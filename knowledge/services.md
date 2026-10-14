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

---

## 2. Pluggable Providers (`services/providers/`)

### Abstract Interface: `BaseAIProvider` (`base.py`)
```python
class BaseAIProvider(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        """Send chat messages and return assistant response."""

    @abstractmethod
    def chat_vision(self, prompt: str, image_path: str, temperature: float = 0.2) -> str:
        """Send a prompt with a base64-encoded image."""

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """Test API connectivity and return (success, message)."""
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

---

## 6. `ModelDownloader` (`services/model_downloader.py`)

Provides 1-click model weight streaming, tracking, and atomic storage for embedded offline AI models.
- **`GGUF_CATALOG`**: Curated catalog of compact quantized models (`qwen2.5-0.5b`, `qwen2.5-1.5b`, `smollm2-1.7b`).
- **`download_model(...)`**: Chunked streaming download from HuggingFace with progress callbacks, atomic `.part` replacement, and `threading.Event` cancellation.
- **`is_model_downloaded(...)`**: Verifies presence and valid size of local weights in `models/weights/`.

---

## 7. `OllamaManager` (`services/ollama_manager.py`)

Provides 1-click Ollama discovery and streaming model pulling via local REST API (`http://localhost:11434`).
- **`check_status(...)`**: Non-blocking ping of `GET /api/tags`.
- **`list_installed_models(...)`**: Inspects tags of locally installed models in Ollama.
- **`pull_model(...)`**: Sends `POST /api/pull` with `stream: true`, parsing streaming progress updates.
- **`RECOMMENDED_OLLAMA_MODELS`**: Curated recommendations (`llama3.2:1b`, `qwen2.5:1.5b`, `llama3.2:3b`, `moondream:latest`).

---

## 8. `DocumentPeeker` (`services/document_peeker.py`)

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


