# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across the NoMoreClutter repository.

---

## 📦 Module Summary Table

| Module Path | Lines | Size (Bytes) | Classes | Functions |
|-------------|-------|--------------|---------|-----------|
| `main.py` | 1668 | 82246 | 1 | 0 |
| `models/__init__.py` | 44 | 1399 | 2 | 0 |
| `services/__init__.py` | 39 | 1266 | 0 | 9 |
| `services/benchmark_service.py` | 223 | 10469 | 2 | 0 |
| `services/document_peeker.py` | 151 | 5969 | 1 | 0 |
| `services/file_executor.py` | 232 | 8492 | 1 | 0 |
| `services/file_scanner.py` | 40 | 1408 | 1 | 0 |
| `services/llm_service.py` | 211 | 8710 | 2 | 0 |
| `services/model_downloader.py` | 181 | 6535 | 2 | 0 |
| `services/ollama_manager.py` | 158 | 5646 | 2 | 0 |
| `services/providers/__init__.py` | 44 | 1198 | 0 | 1 |
| `services/providers/base.py` | 43 | 1407 | 1 | 0 |
| `services/providers/embedded.py` | 94 | 4160 | 1 | 0 |
| `services/providers/openai_compatible.py` | 108 | 4397 | 1 | 0 |
| `services/providers/registry.py` | 130 | 4668 | 1 | 3 |
| `services/rlm_organizer.py` | 412 | 17184 | 2 | 0 |
| `tests/test_ai_status.py` | 118 | 5346 | 1 | 0 |
| `tests/test_benchmark_service.py` | 152 | 6518 | 3 | 0 |
| `tests/test_deploy_manager.py` | 189 | 7764 | 4 | 0 |
| `tests/test_document_peeker.py` | 122 | 4569 | 2 | 0 |
| `tests/test_file_executor.py` | 156 | 6060 | 1 | 0 |
| `tests/test_file_scanner.py` | 96 | 3707 | 1 | 0 |
| `tests/test_llm_service.py` | 88 | 3573 | 1 | 0 |
| `tests/test_providers.py` | 54 | 1795 | 1 | 0 |
| `tests/test_rlm_organizer.py` | 78 | 3409 | 2 | 0 |
| `tests/test_settings_functionality.py` | 234 | 9382 | 1 | 0 |
| `tests/test_sync_and_knowledge.py` | 87 | 3297 | 1 | 0 |

---

## 🔍 Deep Symbol Breakdown

### `main.py`
#### Classes
- **`NoMoreClutterApp`**
  - Method `.__init__()`
  - Method `._load_settings()`
  - Method `._save_settings(silent)`
  - Method `._build_ui()`
  - Method `._build_settings_window()`
  - Method `._on_batch_size_slider_changed(value)`
  - Method `._on_limit_slider_changed(value)`
  - Method `._on_peek_length_slider_changed(value)`
  - Method `._on_pacing_slider_changed(value)`
  - Method `._on_provider_changed(choice)`
  - Method `._update_provider_ui(provider_name, force_defaults)`
  - Method `._on_vision_toggled()`
  - Method `._toggle_show_key()`
  - Method `._open_signup_url()`
  - Method `._test_connection()`
  - Method `._refresh_ai_status_async()`
  - Method `._ai_status_worker()`
  - Method `._apply_ai_status_ui(is_plugged, badge_label, detail_msg)`
  - Method `._on_ai_status_clicked()`
  - Method `._run_benchmark_action()`
  - Method `._benchmark_worker()`
  - Method `._update_benchmark_progress_ui(msg, val)`
  - Method `._on_benchmark_complete(result)`
  - Method `._on_benchmark_error(err_msg)`
  - Method `._apply_benchmark_settings()`
  - Method `._open_settings()`
  - Method `._hide_settings()`
  - Method `._open_quick_deploy()`
  - Method `._hide_quick_deploy()`
  - Method `._build_quick_deploy_window()`
  - Method `._on_embed_catalog_changed(choice)`
  - Method `._update_embed_status_ui()`
  - Method `._download_embedded_action()`
  - Method `._cancel_embedded_download()`
  - Method `._download_embedded_worker(model_id)`
  - Method `._update_embed_progress_ui(val, txt)`
  - Method `._on_embedded_download_success(filename)`
  - Method `._on_embedded_download_cancelled()`
  - Method `._on_embedded_download_error(err)`
  - Method `._activate_selected_embedded_model()`
  - Method `._activate_embedded_model(filename)`
  - Method `._refresh_ollama_status()`
  - Method `._pull_ollama_action()`
  - Method `._cancel_ollama_pull()`
  - Method `._pull_ollama_worker(model_tag)`
  - Method `._update_ollama_progress_ui(val, txt)`
  - Method `._on_ollama_pull_success(model_tag)`
  - Method `._on_ollama_pull_cancelled()`
  - Method `._on_ollama_pull_error(err)`
  - Method `._activate_ollama_model(model_tag)`
  - Method `._on_cloud_provider_changed(choice)`
  - Method `._open_cloud_key_url()`
  - Method `._activate_cloud_action()`
  - Method `._select_source()`
  - Method `._select_output()`
  - Method `._update_folder_info()`
  - Method `._get_selected_extensions()`
  - Method `._get_existing_folders()`
  - Method `._quick_organize()`
  - Method `._analyze()`
  - Method `._analyze_thread(files)`
  - Method `._append_batch_log(results)`
  - Method `._update_progress(count, results)`
  - Method `._analysis_complete(results)`
  - Method `._show_error(error)`
  - Method `._execute()`
  - Method `._undo_moves()`

### `models/__init__.py`
#### Classes
- **`FileChange`**
- **`AppSettings`**
  - Method `.__post_init__()`

### `services/__init__.py`
#### Functions
- `def get_FileScanner()`
- `def get_LLMService()`
- `def get_RLMOrganizer()`
- `def get_FileExecutor()`
- `def get_provider_registry()`
- `def get_model_downloader()`
- `def get_ollama_manager()`
- `def get_document_peeker()`
- `def get_benchmark_service()`

### `services/benchmark_service.py`
> Automatic Performance Benchmark & Settings Auto-Tuner (PRINCIPLE-007: Speed & Lean Architecture).
Benchmarks active AI models on the user's PC using lightweight synthetic test files,
measures latency, evaluates schema compliance and vision support, and calculates optimal settings.

#### Classes
- **`BenchmarkResult`**
  - *Structured report card of hardware and model performance with continuous slider tuning.*
- **`BenchmarkService`**
  - *Benchmark runner that probes latency, vision, and calculates continuous optimal settings.*
  - Method `.run_benchmark(cls, provider, model, provider_name, progress_callback)`

### `services/document_peeker.py`
> Document Content Peeker (PRINCIPLE-007: Performance, PRINCIPLE-009: Token Frugality)
Extracts brief, token-budgeted text snippets from documents (TXT, MD, PDF, DOCX, CSV, Code)
to empower semantic AI categorization without dumping entire files into prompts.
Zero external dependencies (uses standard library zipfile, zlib, re, os).

#### Classes
- **`DocumentPeeker`**
  - *Safely extracts compact text snippets from documents for intelligent categorization.*
  - Method `.peek(cls, file_path, max_chars)`
  - Method `._extract_plain_text(file_path, max_bytes)`
  - Method `._extract_docx(file_path)`
  - Method `._extract_pdf(file_path, max_scan_bytes)`
  - Method `._clean_and_truncate(text, max_chars)`

### `services/file_executor.py`
> Safe File Operations & Persistent Multi-Session Undo Management (PRINCIPLE-007: Reliability)
Guarantees collision avoidance, directory creation, atomic persistent history logging,
and multi-session rollback capabilities that survive application restarts.

#### Classes
- **`FileExecutor`**
  - *Safe execution engine with persistent multi-session undo tracking and collision resolution.*
  - Method `._ensure_loaded(cls)`
  - Method `._load_history(cls)`
  - Method `._save_history(cls)`
  - Method `.execute(cls, changes)`
  - Method `.undo_last_batch(cls)`
  - Method `.has_undo(cls)`
  - Method `.get_history_summary(cls)`
  - Method `.clear_history(cls)`
  - Method `._resolve_collision(target_path)`

### `services/file_scanner.py`
#### Classes
- **`FileScanner`**
  - Method `.scan_folder(folder_path, extensions, include_subfolders)`
  - Method `.get_extension(filename)`
  - Method `.get_category(extension, categories)`

### `services/llm_service.py`
> LLM Service Facade (PRINCIPLE-001, PRINCIPLE-003, PRINCIPLE-009)
Adapts the pluggable AI provider and RLM Organizer for backward compatibility and clean orchestration.

#### Classes
- **`LLMError`**
  - *Legacy exception class maintained for backward compatibility.*
- **`LLMService`**
  - *Unified service facade interfacing with Pluggable AI Providers and RLM Engine.*
  - Method `.__init__(base_url, api_key, provider_id)`
  - Method `.test_connection(model)`
  - Method `.check_ai_status(cls, provider_name, base_url, api_key, model)`
  - Method `.analyze_files(files, model, create_new_folders, existing_folders, analyze_images, numbered_rename, ai_rename, content_peeking, peek_max_chars, target_folder, output_folder, progress_callback)`

### `services/model_downloader.py`
> Model Downloader Utility (PRINCIPLE-003, PRINCIPLE-007, PRINCIPLE-008)
Provides 1-click streaming download of compact, quantized GGUF models from HuggingFace
with visual progress reporting, atomic writes, and cancellation support.
Zero external dependencies (uses standard library urllib).

#### Classes
- **`ModelCatalogItem`**
- **`ModelDownloader`**
  - *Manages downloading, caching, and verification of embedded model weights.*
  - Method `.get_weights_dir()`
  - Method `.get_model_path(cls, filename)`
  - Method `.is_model_downloaded(cls, filename)`
  - Method `.get_downloaded_models(cls)`
  - Method `.download_model(cls, model_id, progress_callback, cancel_event)`

### `services/ollama_manager.py`
> Ollama Auto-Manager & Model Deployer (PRINCIPLE-003, PRINCIPLE-008)
Provides 1-click discovery, connection verification, and streaming model pulling
via Ollama's local REST API (http://localhost:11434).
Zero external dependencies (uses standard library urllib and json).

#### Classes
- **`OllamaRecommendedModel`**
- **`OllamaManager`**
  - *Manages interactions with local Ollama daemon for 1-click model deployment.*
  - Method `.check_status(base_url)`
  - Method `.list_installed_models(base_url)`
  - Method `.pull_model(cls, model_name, base_url, progress_callback, cancel_event)`

### `services/providers/__init__.py`
> Services Provider Module (PRINCIPLE-003: Modularity)

#### Functions
- `def get_provider(provider_id, base_url, api_key)`
  - *Instantiate and return the appropriate AI provider.*

### `services/providers/base.py`
> Base AI Provider Interface (PRINCIPLE-003: Modularity & Pluggable Architecture)
Defines the standard abstraction for all AI providers (Cloud, Embedded, and Local Server).

#### Classes
- **`BaseAIProvider`**
  - *Abstract base class for all AI model providers.*
  - Method `.__init__(base_url, api_key)`
  - Method `.test_connection(model)`
  - Method `.complete(prompt, model, temperature, max_tokens)`
  - Method `.analyze_image(image_path, prompt, model, max_tokens)`

### `services/providers/embedded.py`
> Embedded Local AI Provider (PRINCIPLE-003: Modularity, PRINCIPLE-008: Zero-Friction)
Runs 100% offline in-process using downloaded GGUF weights via llama-cpp-python.

#### Classes
- **`EmbeddedProvider`**
  - *Provider running local quantized GGUF models directly within the application.*
  - Method `.__init__(model_filename)`
  - Method `._get_model_path(model)`
  - Method `._get_llm(model)`
  - Method `.test_connection(model)`
  - Method `.complete(prompt, model, temperature, max_tokens)`
  - Method `.analyze_image(image_path, prompt, model, max_tokens)`

### `services/providers/openai_compatible.py`
> OpenAI-Compatible AI Provider Implementation (PRINCIPLE-003, PRINCIPLE-007, PRINCIPLE-009)
Unifies cloud APIs (Groq, Gemini, OpenAI, OpenRouter) and local servers (LM Studio, Ollama).

#### Classes
- **`OpenAICompatibleProvider`**
  - *Universal provider for all endpoints following the OpenAI API standard.*
  - Method `.__init__(base_url, api_key, timeout_sec)`
  - Method `._get_client()`
  - Method `.test_connection(model)`
  - Method `.complete(prompt, model, temperature, max_tokens)`
  - Method `.analyze_image(image_path, prompt, model, max_tokens)`
  - Method `._get_mime_type(file_path)`

### `services/providers/registry.py`
> AI Provider Registry & Presets (PRINCIPLE-003, PRINCIPLE-008)
Centralized catalog of zero-install cloud providers and local server presets.

#### Classes
- **`ProviderPreset`**
#### Functions
- `def get_preset(provider_id)`
  - *Retrieve preset by ID or return custom preset.*
- `def get_preset_by_name(display_name)`
  - *Find preset by UI display name.*
- `def list_provider_names()`
  - *Return all provider display names for UI dropdowns.*

### `services/rlm_organizer.py`
> Recursive Language Model (RLM) File Organizer Engine
Implements PRINCIPLE-001 (RLM Compatibility), PRINCIPLE-007 (Performance),
and PRINCIPLE-009 (Token Frugality & Context Budgeting).

#### Classes
- **`RLMOrganizerError`**
  - *Base exception for RLM Organizer operations.*
- **`RLMOrganizer`**
  - *Recursive Language Model File Organization Engine.*
  - Method `.__init__(provider)`
  - Method `.organize(files, model, output_folder, existing_folders, create_new_folders, analyze_images, ai_rename, numbered_rename, content_peeking, peek_max_chars, cluster_batch_size, progress_callback)`
  - Method `._process_regular_rlm(files, model, output_folder, existing_folders, create_new_folders, ai_rename, content_peeking, peek_max_chars, cluster_batch_size, progress_callback)`
  - Method `._analyze_cluster(batch, model, output_folder, existing_folders, create_new_folders, ai_rename, content_peeking, peek_max_chars)`
  - Method `._process_images_hierarchical(files, model, output_folder, existing_folders, create_new_folders, ai_rename, progress_callback)`
  - Method `.get_heuristic_category(file_path)`
  - Method `._heuristic_fallback_batch(files, output_folder, existing_folders)`
  - Method `._apply_numbered_rename(changes)`
  - Method `._match_closest_folder(target, existing_folders)`
  - Method `._sanitize_folder_name(name)`
  - Method `._sanitize_filename(name, original_path)`
  - Method `._extract_json(text)`

### `tests/test_ai_status.py`
> Unit tests for AI Status Indicator & Health Checks (PRINCIPLE-007, PRINCIPLE-008, PRINCIPLE-011).
Tests plugged/unplugged evaluation across cloud zero-install, embedded GGUF, Ollama, and local servers.

#### Classes
- **`TestAIStatus`**
  - Method `.test_cloud_missing_api_key()`
  - Method `.test_gemini_missing_api_key()`
  - Method `.test_cloud_valid_connection(mock_test)`
  - Method `.test_cloud_invalid_key_error(mock_test)`
  - Method `.test_embedded_not_downloaded(mock_is_dl)`
  - Method `.test_embedded_downloaded_and_ready(mock_is_dl)`
  - Method `.test_ollama_offline(mock_status)`
  - Method `.test_ollama_online(mock_status, mock_list)`
  - Method `.test_local_server_offline(mock_test)`

### `tests/test_benchmark_service.py`
> Unit tests for BenchmarkService & Camera Photo Anti-Hallucination Guard (PRINCIPLE-007, PRINCIPLE-011).
Tests latency measurement, optimal batch calculation, vision detection, and camera date grouping.

#### Classes
- **`MockBenchProvider`**
  - Method `.__init__(delay_sec, return_json)`
  - Method `.test_connection(model)`
  - Method `.complete(prompt, model, temperature, max_tokens)`
  - Method `.analyze_image(image_path, prompt, model, max_tokens)`
- **`MockAnimalsHallucinatingProvider`**
  - *Simulates the bug where model assigns 'Animals' to all camera timestamps.*
  - Method `.__init__()`
  - Method `.test_connection(model)`
  - Method `.complete(prompt, model, temperature, max_tokens)`
  - Method `.analyze_image(image_path, prompt, model, max_tokens)`
- **`TestBenchmarkService`**
  - Method `.test_fast_cloud_benchmark()`
  - Method `.test_continuous_slider_tuning_fast_vs_slow()`
  - Method `.test_vision_model_detection()`
  - Method `.test_camera_photo_anti_hallucination_guard()`

### `tests/test_deploy_manager.py`
> Unit tests for 1-Click AI Model Deployment (PRINCIPLE-003, PRINCIPLE-008, PRINCIPLE-011)
Tests ModelDownloader, OllamaManager, and EmbeddedProvider with mock streaming.

#### Classes
- **`TestModelDownloader`**
  - Method `.test_catalog_integrity()`
  - Method `.test_weights_dir()`
  - Method `.test_is_model_downloaded_nonexistent()`
  - Method `.test_download_model_mock_success(mock_urlopen)`
  - Method `.test_download_model_cancellation(mock_urlopen)`
- **`TestOllamaManager`**
  - Method `.test_recommended_catalog()`
  - Method `.test_check_status_online(mock_urlopen)`
  - Method `.test_check_status_offline(mock_urlopen)`
  - Method `.test_list_installed_models(mock_urlopen)`
  - Method `.test_pull_model_streaming(mock_urlopen)`
- **`TestEmbeddedProvider`**
  - Method `.test_preset_exists()`
  - Method `.test_factory_instantiation()`
  - Method `.test_test_connection_not_downloaded()`
  - Method `.test_analyze_image_not_implemented()`
- **`TestAppDeploymentLogic`**
  - Method `.test_service_accessors()`
  - Method `.test_embedded_model_activation_updates_preset()`

### `tests/test_document_peeker.py`
> Unit tests for Document Content Peeker (PRINCIPLE-007, PRINCIPLE-009, PRINCIPLE-011)
Tests plain text, docx, pdf stream extraction, truncation, and RLM dense payload integration.

#### Classes
- **`DummyProvider`**
  - Method `.__init__()`
  - Method `.test_connection(model)`
  - Method `.complete(prompt, model, temperature, max_tokens)`
  - Method `.analyze_image(image_path, prompt, model, max_tokens)`
- **`TestDocumentPeeker`**
  - Method `.setUp()`
  - Method `.tearDown()`
  - Method `.test_plain_text_peeking()`
  - Method `.test_code_file_peeking()`
  - Method `.test_docx_peeking()`
  - Method `.test_pdf_peeking_uncompressed()`
  - Method `.test_nonexistent_or_empty_file()`
  - Method `.test_rlm_organizer_content_peeking_integration()`

### `tests/test_file_executor.py`
> Unit tests for FileExecutor (PRINCIPLE-007)
Tests collision avoidance, safe moves, and undo management.

#### Classes
- **`TestFileExecutor`**
  - Method `.setUp()`
  - Method `.tearDown()`
  - Method `.test_execute_move_and_undo()`
  - Method `.test_collision_avoidance()`
  - Method `.test_persistent_history_across_restarts()`
  - Method `.test_legacy_history_format_compatibility()`

### `tests/test_file_scanner.py`
> Unit tests for FileScanner (PRINCIPLE-011).
Tests shallow and recursive scanning, extension filtering, and category lookups.

#### Classes
- **`TestFileScanner`**
  - Method `.setUp()`
  - Method `.tearDown()`
  - Method `.test_scan_folder_shallow()`
  - Method `.test_scan_folder_shallow_filters_extensions()`
  - Method `.test_scan_folder_recursive()`
  - Method `.test_scan_empty_or_invalid_folder()`
  - Method `.test_get_extension()`
  - Method `.test_get_category()`

### `tests/test_llm_service.py`
> Unit tests for LLMService Facade (PRINCIPLE-011).
Tests initialization, error encapsulation, and integration with RLM organizer.

#### Classes
- **`TestLLMService`**
  - Method `.setUp()`
  - Method `.test_initialization()`
  - Method `.test_test_connection_delegation(mock_test)`
  - Method `.test_analyze_files_empty()`
  - Method `.test_analyze_files_error_wrapping()`
  - Method `.test_analyze_files_destination_resolution()`

### `tests/test_providers.py`
> Unit tests for AI Providers and Registry (PRINCIPLE-003, PRINCIPLE-008)

#### Classes
- **`TestProviders`**
  - Method `.test_presets_exist()`
  - Method `.test_preset_retrieval()`
  - Method `.test_list_provider_names()`
  - Method `.test_get_preset_by_name()`
  - Method `.test_get_provider_factory()`

### `tests/test_rlm_organizer.py`
> Unit tests for RLM Organizer (PRINCIPLE-001, PRINCIPLE-007, PRINCIPLE-009)

#### Classes
- **`MockProvider`**
  - Method `.__init__(mock_response)`
  - Method `.test_connection(model)`
  - Method `.complete(prompt, model, temperature, max_tokens)`
  - Method `.analyze_image(image_path, prompt, model, max_tokens)`
- **`TestRLMOrganizer`**
  - Method `.test_json_extraction_raw()`
  - Method `.test_json_extraction_markdown_fenced()`
  - Method `.test_heuristic_categorization()`
  - Method `.test_numbered_rename()`
  - Method `.test_organize_mock()`

### `tests/test_settings_functionality.py`
> Unit tests verifying the function of EVERY setting in NoMoreClutter (PRINCIPLE-011).
Tests AI rename, folder creation, numbered rename, content peeking, limits,
batch sizes, embedded provider detection, and settings persistence.

#### Classes
- **`TestSettingsFunctionality`**
  - Method `.setUp()`
  - Method `.tearDown()`
  - Method `.test_ai_rename_setting_disabled_guarantees_original_name()`
  - Method `.test_ai_rename_setting_enabled_applies_sanitized_name()`
  - Method `.test_create_folders_setting_enabled()`
  - Method `.test_create_folders_setting_disabled_with_existing()`
  - Method `.test_create_folders_setting_disabled_without_existing()`
  - Method `.test_numbered_rename_setting_enabled()`
  - Method `.test_content_peeking_setting_enabled_and_disabled()`
  - Method `.test_embedded_provider_auto_resolution()`
  - Method `.test_settings_persistence_all_keys()`

### `tests/test_sync_and_knowledge.py`
> Unit tests for Principles and Knowledge Base Synchronization (PRINCIPLE-011).
Tests principle parsing, guideline content generation, and AST symbol extraction.

#### Classes
- **`TestSyncAndKnowledge`**
  - Method `.test_parse_principles()`
  - Method `.test_generate_gemini_content()`
  - Method `.test_extract_python_symbols()`
