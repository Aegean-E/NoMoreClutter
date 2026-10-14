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

Handles safe disk operations and maintains rollback history.

### Safety Features
- **Collision Avoidance**: If `Target/report.pdf` exists, `get_safe_destination_path()` automatically increments to `Target/report (1).pdf`, `Target/report (2).pdf`, etc.
- **Batch History**: Every executed move is appended to an in-memory stack `_undo_stack: List[List[FileMoveRecord]]`.

### Methods
- `execute_moves(moves: List[Tuple[FileInfo, str, Optional[str]]], base_target_dir: str, callback: Optional[Callable[[str], None]] = None) -> List[Tuple[FileInfo, str]]`:
  Executes file moves, creates destination folders, and logs moves.
- `undo_last_batch(callback: Optional[Callable[[str], None]] = None) -> int`:
  Rolls back the most recent batch of moved files to their original paths.
- `get_safe_destination_path(target_folder: str, filename: str) -> str`:
  Returns a guaranteed non-colliding path.

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

