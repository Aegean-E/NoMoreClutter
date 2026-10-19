# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across this repository.

---

## 📊 Codebase Metrics
- **Total Python Modules**: `41`
- **Total Classes**: `57`
- **Total Top-Level Functions**: `25`
- **Total Class Methods**: `420`
- **Total Source Lines**: `11135`

---

## 📦 Modules & Exported Symbols

### [`main.py`](main.py)
**Size**: `2110` lines (`101138` bytes)

**Classes:**
- `class NoMoreClutterApp`
  - Method `.__init__()`
  - Method `._load_settings()` - *Load settings with self-healing crash resilience against power loss (PRINCIPLE-012).*
  - Method `._save_settings(silent)` - *Atomically persist settings with buffer flush and fsync (PRINCIPLE-012).*
  - Method `._select_all_categories()`
  - Method `._deselect_all_categories()`
  - Method `._clear_log()`
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
  - Method `._refresh_ai_status_async()` - *Non-blocking background check of whether current AI provider is plugged in (PRINCIPLE-007).*
  - Method `._ai_status_worker()`
  - Method `._apply_ai_status_ui(is_plugged, badge_label, detail_msg)`
  - Method `._on_ai_status_clicked()` - *Handle user clicks on the interactive AI status indicator pill.*
  - Method `._run_benchmark_action()` - *Start asynchronous model benchmarking on synthetic test files (PRINCIPLE-007).*
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
  - Method `._download_engine_action()`
  - Method `._download_engine_worker()`
  - Method `._on_engine_download_success()`
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
  - Method `._quick_organize()` - *Instant zero-install heuristic categorization (PRINCIPLE-008).*
  - Method `._analyze()`
  - Method `._analyze_thread(files)`
  - Method `._append_batch_log(results)`
  - Method `._update_progress(count, results)`
  - Method `._analysis_complete(results)`
  - Method `._show_error(error)`
  - Method `._execute()`
  - Method `._execute_confirmed(selected_changes)`
  - Method `._open_duplicate_finder()`
  - Method `._open_junk_cleaner()`
  - Method `._open_file_viewer(filepath)`
  - Method `._undo_moves()` - *Revert last batch of moves safely (PRINCIPLE-007).*

---

### [`models/__init__.py`](models/__init__.py)
**Size**: `97` lines (`2903` bytes)

**Classes:**
- `class FileChange`
- `class DuplicateGroup`
  - Property `.reclaimable_bytes`
  - Property `.all_files`
  - Method `.set_as_original(new_original)` - *Designate a duplicate as the canonical original to keep, moving prior original to duplicates.*
- `class CleanupItem`
- `class CleanupReport`
  - Method `.__post_init__()`
- `class AppSettings`
  - Method `.__post_init__()`

---

### [`scripts/dogfood_app.py`](scripts/dogfood_app.py)
> *scripts/dogfood_app.py*

**Size**: `812` lines (`36918` bytes)

**Classes:**
- `class DogfoodBlastRadiusJail` - *Enforces zero-blast-radius containment to guarantee no harm to the user's PC (PRINCIPLE-016).*
  - Method `.assert_confined(target_path, sandbox_root)`
- `class SyntheticTestFixtureFactory` - *Generates 100% synthetic, harmless test files for operational dogfooding.*
  - Method `.populate(target_dir)`
- `class DogfoodHarness`
  - Method `.__init__(verbose)`
  - Method `.log(msg)`
  - Method `.record_exception(exc_type, exc_value, exc_tb)`
  - Method `._safe_destroy(widget)`
  - Method `.setup_sandbox()` - *Creates an ephemeral sandbox strictly isolated from user files.*
  - Method `.teardown_sandbox()` - *Cleanly wipes ephemeral sandbox, leaving zero clutter on the user's PC.*
  - Method `.test_blast_radius_security_jail()` - *Verify that blast-radius safety checks block any mutation to user's real folders.*
  - Method `.test_gui_lifecycle_and_quick_organize()` - *Test CTk window initialization, event loop, and Quick Organize.*
  - Method `.test_tree_preview_and_undo_rollback()` - *Test TreePreviewDialog per-file selection, execution, and persistent Undo rollback.*
  - Method `.test_file_viewer_dialog_rendering()` - *Test FileViewerDialog rendering text and image files without modal lock.*
  - Method `.test_junk_cleaner_and_chaos_abort()` - *Test JunkCleanerDialog and chaos stress: aborting mid-scan.*
  - Method `.test_junk_cleaner_full_purge()` - *Test JunkCleanerDialog full scan and purge of empty directories and debris.*
  - Method `.test_duplicate_finder_and_set_original()` - *Test DuplicateFinderDialog, duplicate clustering, and 'Set as Original'.*
  - Method `.test_duplicate_isolation_action()` - *Test DuplicateFinderDialog isolating redundant duplicate files into _duplicates/.*
  - Method `.test_settings_and_slider_persistence()` - *Test settings panel adjustments, slider values, and atomic JSON persistence.*
  - Method `.test_quick_deploy_window_navigation()` - *Test 1-Click AI Quick Deploy window initialization and tab navigation.*
  - Method `.test_live_or_simulated_ai_organization()` - *Test real end-to-end AI organization on diverse synthetic files (categories, renames, and vision).*
  - Method `.test_offline_api_chaos_fuzzing()` - *Fuzz RLM and cleaner parsing with realistic dirty LLM outputs (0 tokens).*
  - Method `.run_all()`

---

### [`services/__init__.py`](services/__init__.py)
**Size**: `51` lines (`1672` bytes)

**Functions:**
- `def get_FileScanner()`
- `def get_LLMService()`
- `def get_RLMOrganizer()`
- `def get_FileExecutor()`
- `def get_provider_registry()`
- `def get_model_downloader()`
- `def get_ollama_manager()`
- `def get_document_peeker()`
- `def get_benchmark_service()`
- `def get_deduplicator()`
- `def get_cleaner_service()`
- `def get_llama_server_manager()`

---

### [`services/benchmark_service.py`](services/benchmark_service.py)
> *Automatic Performance Benchmark & Settings Auto-Tuner (PRINCIPLE-007: Speed & Lean Architecture).*

**Size**: `223` lines (`10469` bytes)

**Classes:**
- `class BenchmarkResult` - *Structured report card of hardware and model performance with continuous slider tuning.*
- `class BenchmarkService` - *Benchmark runner that probes latency, vision, and calculates continuous optimal settings.*
  - Method `.run_benchmark(provider, model, provider_name, progress_callback)` - *Run automated hardware and model benchmark using synthetic test files.*

---

### [`services/cleaner_service.py`](services/cleaner_service.py)
> *Orphan Folder & Junk Pruner Service (PRINCIPLE-003: Modularity, PRINCIPLE-007: Speed & Safety)*

**Size**: `221` lines (`8479` bytes)

**Classes:**
- `class CleanerService` - *Safely cleans empty folders, zero-byte artifacts, and system junk.*
  - Method `.is_os_debris(filename)` - *Check if a filename is known operating system debris or thumbnail cache.*
  - Method `.scan(folder, scan_empty_dirs, scan_zero_byte, scan_os_debris, progress_callback, cancel_event)` - *Scan directory and return a structured list of cleanup candidates.*
  - Method `.prune(items, progress_callback)` - *Execute cleanup on specified items safely.*

---

### [`services/deduplicator.py`](services/deduplicator.py)
> *Smart Duplicate File Finder & Storage Reclaimer (PRINCIPLE-007: Speed & Lean Architecture)*

**Size**: `259` lines (`10605` bytes)

**Classes:**
- `class DeduplicationService` - *High-performance file deduplication engine.*
  - Method `.format_bytes(size_bytes)` - *Format raw byte counts into human-readable strings.*
  - Method `.compute_header_hash(file_path)` - *Fast 8KB header hash for quick pre-filtering.*
  - Method `.compute_full_hash(file_path)` - *Buffered streaming SHA-256 calculation for exact match validation.*
  - Method `.scan_duplicates(folder, recursive, min_size_bytes, progress_callback, on_group_found)` - *Scan directory and return list of duplicate groups.*
  - Method `.isolate_duplicates(duplicate_paths, base_folder, isolate_folder_name)` - *Safely move selected duplicate files into a dedicated isolation folder.*
  - Method `.delete_duplicates(duplicate_paths)` - *Permanently delete specified duplicate files safely.*

---

### [`services/document_peeker.py`](services/document_peeker.py)
> *Document Content Peeker (PRINCIPLE-007: Performance, PRINCIPLE-009: Token Frugality)*

**Size**: `151` lines (`6086` bytes)

**Classes:**
- `class DocumentPeeker` - *Safely extracts compact text snippets from documents for intelligent categorization.*
  - Method `.peek(file_path, max_chars)` - *Extract a brief, clean snippet (first max_chars) from a document.*
  - Method `._extract_plain_text(file_path, max_bytes)` - *Read beginning of text file with utf-8 and latin-1 fallback.*
  - Method `._extract_docx(file_path)` - *Extract text from docx zip archive word/document.xml without external libraries.*
  - Method `._extract_pdf(file_path, max_scan_bytes)` - *Extract text from PDF streams using standard library decompresion.*
  - Method `._clean_and_truncate(text, max_chars)` - *Sanitize text to a single-line snippet and truncate to max_chars.*

---

### [`services/file_executor.py`](services/file_executor.py)
> *Safe File Operations & Persistent Multi-Session Undo Management (PRINCIPLE-007: Reliability)*

**Size**: `268` lines (`10432` bytes)

**Classes:**
- `class FileExecutor` - *Safe execution engine with persistent multi-session undo tracking and collision resolution.*
  - Method `.reset_state()` - *Purge in-memory history cache and reset load state (for testing / restart simulation).*
  - Method `._ensure_loaded()` - *Lazy load history from disk on first access.*
  - Method `._load_history()` - *Load persistent history from disk with crash self-healing (PRINCIPLE-012).*
  - Method `._save_history()` - *Atomically persist operation history to disk with fsync (PRINCIPLE-012).*
  - Method `.execute(changes)` - *Safely execute a list of file changes with incremental WAL journaling (PRINCIPLE-012).*
  - Method `.undo_last_batch()` - *Revert the most recent batch of moved files back to their original locations.*
  - Method `.has_undo()` - *Check if any operations can be undone (including from previous sessions).*
  - Method `.get_history_summary()` - *Return a user-readable summary of past batches for UI display.*
  - Method `.clear_history()` - *Reset in-memory and persistent operation history.*
  - Method `._resolve_collision(target_path)` - *If destination file exists, append a counter: 'file (1).ext' to avoid data loss.*

---

### [`services/file_scanner.py`](services/file_scanner.py)
**Size**: `40` lines (`1408` bytes)

**Classes:**
- `class FileScanner`
  - Method `.scan_folder(folder_path, extensions, include_subfolders)`
  - Method `.get_extension(filename)`
  - Method `.get_category(extension, categories)`

---

### [`services/llama_server_manager.py`](services/llama_server_manager.py)
> *Standalone llama-server.exe Manager & Local Inference Engine (PRINCIPLE-003, PRINCIPLE-007, PRINCIPLE-008)*

**Size**: `409` lines (`16096` bytes)

**Classes:**
- `class LlamaServerManager` - *Manages the background execution, lifecycle, and inference requests for llama-server.exe.*
  - Method `.get_effective_exe_path()` - *Resolve path to executable (local models/bin or system PATH).*
  - Method `.is_server_running(port)` - *Check if llama-server is currently active and healthy on the given port.*
  - Method `.start_server(model_path, mmproj_path, port, threads, timeout)` - *Start the standalone llama-server subprocess hosting the specified model.*
  - Method `.stop_server()` - *Terminate the running llama-server subprocess gracefully.*
  - Method `.complete(prompt, model_path, temperature, max_tokens, port)` - *Execute text completion using the standalone llama-server.*
  - Method `.analyze_image(image_path, prompt, model_path, mmproj_path, max_tokens, port)` - *Analyze an image using the standalone llama-server with multimodal vision projector.*

**Functions:**
- `def get_bin_dir()` - *Return the directory path where standalone binaries are stored.*
- `def get_server_exe_path()` - *Return the absolute path to llama-server.exe.*
- `def is_server_installed()` - *Return True if the standalone server executable is present and valid.*
- `def download_server(progress_callback, cancel_event)` - *Download and extract the official standalone llama-server release.*

---

### [`services/llm_service.py`](services/llm_service.py)
> *LLM Service Facade (PRINCIPLE-001, PRINCIPLE-003, PRINCIPLE-009)*

**Size**: `226` lines (`9504` bytes)

**Classes:**
- `class LLMError` - *Legacy exception class maintained for backward compatibility.*
- `class LLMService` - *Unified service facade interfacing with Pluggable AI Providers and RLM Engine.*
  - Method `.__init__(base_url, api_key, provider_id, **kwargs)`
  - Method `.test_connection(model)` - *Test if the configured AI endpoint and model are reachable.*
  - Method `.check_ai_status(provider_name, base_url, api_key, model)` - *Evaluate whether the selected AI provider is plugged in (ready/connected) or unplugged.*
  - Method `.analyze_files(files, model, create_new_folders, existing_folders, analyze_images, numbered_rename, ai_rename, content_peeking, peek_max_chars, target_folder, output_folder, progress_callback)` - *Analyze and organize files using the RLM hierarchical engine.*

---

### [`services/model_downloader.py`](services/model_downloader.py)
> *Model Downloader Utility (PRINCIPLE-003, PRINCIPLE-007, PRINCIPLE-008)*

**Size**: `290` lines (`11670` bytes)

**Classes:**
- `class ModelCatalogItem`
  - Property `.total_size_mb` - *Total size in MB including vision projector if present.*
  - Property `.capability_badge` - *Return visual badge indicating model capabilities.*
- `class ModelDownloader` - *Manages downloading, caching, and verification of embedded model weights.*
  - Method `.get_weights_dir()` - *Return the directory path where GGUF weights are stored.*
  - Method `.get_model_path(filename)` - *Return absolute path for a model filename.*
  - Method `.get_mmproj_path(filename)` - *Return path to mmproj projector file if associated with the given model filename.*
  - Method `.is_model_downloaded(filename)` - *Check if model exists locally and has non-trivial size (>10MB).*
  - Method `.get_downloaded_models()` - *Return all catalog items that are currently downloaded locally.*
  - Method `._download_file(url, dest_file, progress_callback, cancel_event, bytes_already_done, combined_total_bytes, start_time)` - *Download a single file to dest_file via an atomic .part replacement.*
  - Method `.download_model(model_id, progress_callback, cancel_event)` - *Download a model from the catalog with progress tracking and cancellation.*

---

### [`services/ollama_manager.py`](services/ollama_manager.py)
> *Ollama Auto-Manager & Model Deployer (PRINCIPLE-003, PRINCIPLE-008)*

**Size**: `171` lines (`6292` bytes)

**Classes:**
- `class OllamaRecommendedModel`
  - Property `.capability_badge` - *Return visual badge indicating model capabilities.*
- `class OllamaManager` - *Manages interactions with local Ollama daemon for 1-click model deployment.*
  - Method `.check_status(base_url)` - *Check if Ollama server is running and reachable.*
  - Method `.list_installed_models(base_url)` - *Return list of model tags already installed in Ollama.*
  - Method `.pull_model(model_name, base_url, progress_callback, cancel_event)` - *Pull a model with live streaming progress from Ollama.*

---

### [`services/providers/__init__.py`](services/providers/__init__.py)
> *Services Provider Module (PRINCIPLE-003: Modularity)*

**Size**: `44` lines (`1198` bytes)

**Functions:**
- `def get_provider(provider_id, base_url, api_key, **kwargs)` - *Instantiate and return the appropriate AI provider.*

---

### [`services/providers/base.py`](services/providers/base.py)
> *Base AI Provider Interface (PRINCIPLE-003: Modularity & Pluggable Architecture)*

**Size**: `48` lines (`1565` bytes)

**Classes:**
- `class BaseAIProvider` - *Abstract base class for all AI model providers.*
  - Method `.__init__(base_url, api_key, **kwargs)`
  - Property `.has_vision` - *Indicates whether this provider supports multimodal image vision analysis.*
  - Method `.test_connection(model)` - *Test if the AI endpoint is accessible and responsive.*
  - Method `.complete(prompt, model, temperature, max_tokens)` - *Execute a text completion request.*
  - Method `.analyze_image(image_path, prompt, model, max_tokens)` - *Execute a vision model analysis on a local image.*

---

### [`services/providers/embedded.py`](services/providers/embedded.py)
> *Embedded Local AI Provider (PRINCIPLE-003: Modularity, PRINCIPLE-008: Zero-Friction)*

**Size**: `193` lines (`8491` bytes)

**Classes:**
- `class EmbeddedProvider` - *Provider running local quantized GGUF models directly within the application.*
  - Method `.__init__(model_filename, **kwargs)`
  - Property `.has_vision` - *Return True if the configured model is a multimodal vision model.*
  - Method `._get_model_path(model)` - *Resolve model filename to local path.*
  - Method `._get_llm(model)` - *Lazy load in-process Llama instance when llama-cpp-python is used.*
  - Method `.test_connection(model)` - *Test if the local model is downloaded and inference engine is ready.*
  - Method `.complete(prompt, model, temperature, max_tokens)` - *Run text completion using the standalone llama-server or fallback in-process model.*
  - Method `.analyze_image(image_path, prompt, model, max_tokens)` - *Analyze an image using the local multimodal vision model.*

---

### [`services/providers/openai_compatible.py`](services/providers/openai_compatible.py)
> *OpenAI-Compatible AI Provider Implementation (PRINCIPLE-003, PRINCIPLE-007, PRINCIPLE-009)*

**Size**: `108` lines (`4397` bytes)

**Classes:**
- `class OpenAICompatibleProvider` - *Universal provider for all endpoints following the OpenAI API standard.*
  - Method `.__init__(base_url, api_key, timeout_sec, **kwargs)`
  - Method `._get_client()` - *Lazy load OpenAI client for fast application startup.*
  - Method `.test_connection(model)` - *Verify API accessibility and credentials.*
  - Method `.complete(prompt, model, temperature, max_tokens)` - *Execute text completion and extract output text cleanly.*
  - Method `.analyze_image(image_path, prompt, model, max_tokens)` - *Perform vision inference on a single image file.*
  - Method `._get_mime_type(file_path)`

---

### [`services/providers/registry.py`](services/providers/registry.py)
> *AI Provider Registry & Presets (PRINCIPLE-003, PRINCIPLE-008)*

**Size**: `135` lines (`4892` bytes)

**Classes:**
- `class ProviderPreset`
  - Property `.has_vision` - *Return True if this preset configures a vision-capable model.*

**Functions:**
- `def get_preset(provider_id)` - *Retrieve preset by ID or return custom preset.*
- `def get_preset_by_name(display_name)` - *Find preset by UI display name.*
- `def list_provider_names()` - *Return all provider display names for UI dropdowns.*

---

### [`services/rlm_organizer.py`](services/rlm_organizer.py)
> *Recursive Language Model (RLM) File Organizer Engine*

**Size**: `488` lines (`21747` bytes)

**Classes:**
- `class RLMOrganizerError` - *Base exception for RLM Organizer operations.*
- `class RLMOrganizer` - *Recursive Language Model File Organization Engine.*
  - Method `.__init__(provider)`
  - Method `.organize(files, model, output_folder, existing_folders, create_new_folders, analyze_images, ai_rename, numbered_rename, content_peeking, peek_max_chars, cluster_batch_size, progress_callback)` - *Perform hierarchical RLM organization on file collection.*
  - Method `._process_regular_rlm(files, model, output_folder, existing_folders, create_new_folders, ai_rename, content_peeking, peek_max_chars, cluster_batch_size, progress_callback)` - *Recursive bounded batch processing with compact payload serialization.*
  - Method `._analyze_cluster(batch, model, output_folder, existing_folders, create_new_folders, ai_rename, content_peeking, peek_max_chars)` - *Analyze a scoped cluster using compact token-efficient payload schemas.*
  - Method `._process_images_hierarchical(files, model, output_folder, existing_folders, create_new_folders, ai_rename, progress_callback)` - *Single-pass token-frugal vision analysis (reduces 5 roundtrips down to 1).*
  - Method `._extract_image_year(file_path)` - *Extract 4-digit year from image filename or file modification timestamp.*
  - Method `._get_smart_image_folder(file_path)` - *Categorize an image into a date album (Photos/YYYY) or general Photos folder.*
  - Method `.get_heuristic_category(file_path)` - *Instant zero-install heuristic categorization by file extension.*
  - Method `._heuristic_fallback_batch(files, output_folder, existing_folders)` - *Pure Python rule-based classification when LLM is unreachable.*
  - Method `._apply_numbered_rename(changes)` - *Apply sequential numbering (1.jpg, 2.jpg) scoped per folder.*
  - Method `._match_closest_folder(target, existing_folders)` - *Find best match among existing directories.*
  - Method `._sanitize_folder_name(name)`
  - Method `._sanitize_filename(name, original_path)`
  - Method `._extract_json(text)` - *Cleanly extract JSON payloads from markdown blocks or raw text.*

---

### [`tests/test_ai_status.py`](tests/test_ai_status.py)
> *Unit tests for AI Status Indicator & Health Checks (PRINCIPLE-007, PRINCIPLE-008, PRINCIPLE-011).*

**Size**: `118` lines (`5346` bytes)

**Classes:**
- `class TestAIStatus`
  - Method `.test_cloud_missing_api_key()` - *Cloud providers requiring API keys should be reported unplugged without network calls.*
  - Method `.test_gemini_missing_api_key()` - *Google Gemini with empty key should be flagged as unplugged.*
  - Method `.test_cloud_valid_connection(mock_test)` - *Successful connection test should result in plugged status.*
  - Method `.test_cloud_invalid_key_error(mock_test)` - *Invalid API key response should flag provider as unplugged with clear badge.*
  - Method `.test_embedded_not_downloaded(mock_is_dl)` - *Embedded provider without downloaded weights should be flagged as unplugged.*
  - Method `.test_embedded_downloaded_and_ready(mock_is_dl)` - *Embedded provider with downloaded weights should be flagged as plugged & ready.*
  - Method `.test_ollama_offline(mock_status)` - *Ollama server offline should be flagged as unplugged.*
  - Method `.test_ollama_online(mock_status, mock_list)` - *Ollama server running should be flagged as plugged.*
  - Method `.test_local_server_offline(mock_test)` - *LM Studio server not responding should be flagged as server offline.*

---

### [`tests/test_benchmark_service.py`](tests/test_benchmark_service.py)
> *Unit tests for BenchmarkService & Camera Photo Anti-Hallucination Guard (PRINCIPLE-007, PRINCIPLE-011).*

**Size**: `152` lines (`6554` bytes)

**Classes:**
- `class MockBenchProvider`
  - Method `.__init__(delay_sec, return_json)`
  - Method `.test_connection(model)`
  - Method `.complete(prompt, model, temperature, max_tokens)`
  - Method `.analyze_image(image_path, prompt, model, max_tokens)`
- `class MockAnimalsHallucinatingProvider` - *Simulates the bug where model assigns 'Animals' to all camera timestamps.*
  - Method `.__init__()`
  - Method `.test_connection(model)`
  - Method `.complete(prompt, model, temperature, max_tokens)`
  - Method `.analyze_image(image_path, prompt, model, max_tokens)`
- `class TestBenchmarkService`
  - Method `.test_fast_cloud_benchmark()` - *Fast latency (<800ms) should calibrate high continuous slider values.*
  - Method `.test_continuous_slider_tuning_fast_vs_slow()` - *Continuous slider auto-tuning must yield scaled values based on latency.*
  - Method `.test_vision_model_detection()` - *Models with vision in their name should be flagged as vision-capable.*
  - Method `.test_camera_photo_anti_hallucination_guard()` - *Verify that when a model erroneously assigns 'Animals' to camera timestamps,*

---

### [`tests/test_cleaner_service.py`](tests/test_cleaner_service.py)
> *Unit tests for CleanerService (PRINCIPLE-003, PRINCIPLE-007, PRINCIPLE-011)*

**Size**: `93` lines (`3377` bytes)

**Classes:**
- `class TestCleanerService`
  - Method `.setUp()`
  - Method `.tearDown()`
  - Method `.test_detect_empty_folders()`
  - Method `.test_detect_zero_byte_and_os_debris()`
  - Method `.test_prune_removes_debris_and_empty_dirs()`
  - Method `.test_scan_cancellation()`

---

### [`tests/test_deduplicator.py`](tests/test_deduplicator.py)
> *Unit tests for DeduplicationService (PRINCIPLE-007, PRINCIPLE-011)*

**Size**: `172` lines (`6881` bytes)

**Classes:**
- `class TestDeduplicationService`
  - Method `.setUp()`
  - Method `.tearDown()`
  - Method `.test_format_bytes()`
  - Method `.test_no_duplicates()`
  - Method `.test_exact_duplicates_detected()`
  - Method `.test_same_size_different_content_not_flagged()`
  - Method `.test_isolate_duplicates()`
  - Method `.test_delete_duplicates()`
  - Method `.test_realtime_on_group_found_callback()` - *DeduplicationService must invoke on_group_found in real-time as duplicate clusters are identified.*
  - Method `.test_duplicate_group_set_as_original()`

---

### [`tests/test_deploy_manager.py`](tests/test_deploy_manager.py)
> *Unit tests for 1-Click AI Model Deployment (PRINCIPLE-003, PRINCIPLE-008, PRINCIPLE-011)*

**Size**: `241` lines (`10685` bytes)

**Classes:**
- `class TestModelDownloader`
  - Method `.test_catalog_integrity()`
  - Method `.test_vision_catalog_item()`
  - Method `.test_weights_dir()`
  - Method `.test_is_model_downloaded_nonexistent()`
  - Method `.test_download_model_mock_success(mock_urlopen)`
  - Method `.test_download_model_cancellation(mock_urlopen)`
  - Method `.test_download_multimodal_model_mock_success(mock_urlopen)`
- `class TestOllamaManager`
  - Method `.test_recommended_catalog()`
  - Method `.test_check_status_online(mock_urlopen)`
  - Method `.test_check_status_offline(mock_urlopen)`
  - Method `.test_list_installed_models(mock_urlopen)`
  - Method `.test_pull_model_streaming(mock_urlopen)`
- `class TestEmbeddedProvider`
  - Method `.test_preset_exists()`
  - Method `.test_factory_instantiation()`
  - Method `.test_provider_vision_attribute()`
  - Method `.test_test_connection_not_downloaded()`
  - Method `.test_analyze_image_text_model_raises_not_implemented()`
  - Method `.test_analyze_image_vision_model_raises_file_not_found()`
- `class TestAppDeploymentLogic`
  - Method `.test_service_accessors()`
  - Method `.test_embedded_model_activation_updates_preset()`

---

### [`tests/test_document_peeker.py`](tests/test_document_peeker.py)
> *Unit tests for Document Content Peeker (PRINCIPLE-007, PRINCIPLE-009, PRINCIPLE-011)*

**Size**: `122` lines (`4587` bytes)

**Classes:**
- `class DummyProvider`
  - Method `.__init__()`
  - Method `.test_connection(model)`
  - Method `.complete(prompt, model, temperature, max_tokens)`
  - Method `.analyze_image(image_path, prompt, model, max_tokens)`
- `class TestDocumentPeeker`
  - Method `.setUp()`
  - Method `.tearDown()`
  - Method `.test_plain_text_peeking()`
  - Method `.test_code_file_peeking()`
  - Method `.test_docx_peeking()`
  - Method `.test_pdf_peeking_uncompressed()`
  - Method `.test_nonexistent_or_empty_file()`
  - Method `.test_rlm_organizer_content_peeking_integration()` - *Verify that RLMOrganizer includes 'peek' key in candidate items when enabled.*

---

### [`tests/test_dogfood.py`](tests/test_dogfood.py)
> *Unit and integration tests for the interactive dogfooding harness (PRINCIPLE-016).*

**Size**: `109` lines (`5209` bytes)

**Classes:**
- `class TestDogfoodHarness`
  - Method `.setUp()`
  - Method `.tearDown()`
  - Method `.test_offline_api_chaos_fuzzing()` - *Verify that offline chaos fuzzing handles dirty LLM outputs cleanly.*
  - Method `.test_junk_cleaner_chaos_abort()` - *Verify that JunkCleanerDialog aborts cleanly without unhandled TclError.*
  - Method `.test_gui_lifecycle_and_quick_organize()` - *Verify that GUI mounts, sets folders, and organizes files.*
  - Method `.test_duplicate_finder_and_set_original()` - *Verify that DuplicateFinderDialog handles Set as Original cleanly.*
  - Method `.test_blast_radius_security_jail()` - *Verify that blast-radius jail blocks external user directories.*
  - Method `.test_blast_radius_jail_blocks_critical_paths()` - *Verify that the jail raises PermissionError when critical paths are targeted.*
  - Method `.test_synthetic_fixture_factory()` - *Verify that synthetic test fixtures are created and 100% synthetic.*
  - Method `.test_tree_preview_and_undo_rollback()` - *Verify that TreePreviewDialog unchecking, execution, and undo work cleanly.*
  - Method `.test_file_viewer_dialog_rendering()` - *Verify that FileViewerDialog renders images, text, and documents cleanly.*
  - Method `.test_junk_cleaner_full_purge()` - *Verify that JunkCleanerDialog performs complete purge without crashing.*
  - Method `.test_duplicate_isolation_action()` - *Verify that duplicate isolation action moves copies cleanly to target folder.*
  - Method `.test_settings_and_slider_persistence()` - *Verify that settings sliders persist values atomically to disk with fsync.*
  - Method `.test_quick_deploy_window_navigation()` - *Verify that 1-Click Quick Deploy window mounts cleanly.*
  - Method `.test_live_or_simulated_ai_organization()` - *Verify that AI organization pass completes successfully on synthetic fixtures.*
  - Method `.test_full_dogfood_run()` - *Verify that full harness execution reports 100% operational success.*

---

### [`tests/test_file_executor.py`](tests/test_file_executor.py)
> *Unit tests for FileExecutor (PRINCIPLE-007)*

**Size**: `219` lines (`8978` bytes)

**Classes:**
- `class TestFileExecutor`
  - Method `.setUp()`
  - Method `.tearDown()`
  - Method `.test_execute_move_and_undo()`
  - Method `.test_collision_avoidance()`
  - Method `.test_persistent_history_across_restarts()`
  - Method `.test_legacy_history_format_compatibility()`
  - Method `.test_crash_resilience_corrupted_history_quarantine()` - *A half-written/corrupt history file from a power outage must be quarantined safely without crashing.*
  - Method `.test_incremental_wal_journaling_recovers_interrupted_batch()` - *Incremental WAL records partial moves so an interrupted session can be undone.*

---

### [`tests/test_file_scanner.py`](tests/test_file_scanner.py)
> *Unit tests for FileScanner (PRINCIPLE-011).*

**Size**: `96` lines (`3797` bytes)

**Classes:**
- `class TestFileScanner`
  - Method `.setUp()`
  - Method `.tearDown()`
  - Method `.test_scan_folder_shallow()` - *Shallow scan should only return matching files in the root folder.*
  - Method `.test_scan_folder_shallow_filters_extensions()` - *Only specified extensions should be returned.*
  - Method `.test_scan_folder_recursive()` - *Recursive scan should include files across all subdirectories.*
  - Method `.test_scan_empty_or_invalid_folder()` - *Scanning an empty folder or with empty extensions should return an empty list.*
  - Method `.test_get_extension()` - *Extension extraction should be lowercase with leading dot.*
  - Method `.test_get_category()` - *Category matching should return the correct category name or 'Other'.*

---

### [`tests/test_file_viewer.py`](tests/test_file_viewer.py)
> *Unit tests for In-App File Viewer & Visual Duplicate Inspector (PRINCIPLE-003, PRINCIPLE-007, PRINCIPLE-011).*

**Size**: `198` lines (`9093` bytes)

**Classes:**
- `class TestFileViewerPureLogic`
  - Method `.setUp()`
  - Method `.tearDown()`
  - Method `.test_category_badges()`
  - Method `.test_file_meta_summary()`
  - Method `.test_binary_hexdump_generation()`
  - Method `.test_text_reading_logic()`
  - Method `.test_image_dimension_scaling()`
  - Method `.test_compare_mode_determination()`
  - Method `.test_open_file_launches_system_default()`
  - Method `.test_image_color_mode_conversion()`
- `class TestDuplicatePaginationLogic`
  - Method `.test_selection_across_unrendered_groups()`

---

### [`tests/test_llama_server_manager.py`](tests/test_llama_server_manager.py)
> *Unit tests for Standalone llama-server.exe Manager (PRINCIPLE-003, PRINCIPLE-008, PRINCIPLE-011).*

**Size**: `229` lines (`8459` bytes)

**Classes:**
- `class TestLlamaServerManager`
  - Method `.setUp()`
  - Method `.tearDown()`
  - Method `.test_paths()` - *Verify binary directory and executable path resolution.*
  - Method `.test_is_server_installed_detection()` - *Verify is_server_installed accurately detects presence of executable.*
  - Method `.test_download_server_mock()` - *Verify streaming download and zip extraction of executable and DLLs.*
  - Method `.test_start_server_missing_model()` - *Verify start_server fails gracefully if model file does not exist.*
  - Method `.test_start_server_success_and_reuse()` - *Verify server starts, polls /health, and reuses instance on identical configuration.*
  - Method `.test_complete_mock()` - *Verify text completion parses OpenAI JSON response format.*
  - Method `.test_analyze_image_mock()` - *Verify image analysis calls endpoint and returns generated description.*

---

### [`tests/test_llm_service.py`](tests/test_llm_service.py)
> *Unit tests for LLMService Facade (PRINCIPLE-011).*

**Size**: `88` lines (`3591` bytes)

**Classes:**
- `class TestLLMService`
  - Method `.setUp()`
  - Method `.test_initialization()` - *Service should initialize with expected provider and organizer.*
  - Method `.test_test_connection_delegation(mock_test)` - *test_connection should delegate to the underlying provider.*
  - Method `.test_analyze_files_empty()` - *Analyzing an empty file list should return an empty list without error.*
  - Method `.test_analyze_files_error_wrapping()` - *Underlying exceptions should be wrapped as LLMError.*
  - Method `.test_analyze_files_destination_resolution()` - *If output_folder is empty, destination should default to the first file's parent directory.*

---

### [`tests/test_providers.py`](tests/test_providers.py)
> *Unit tests for AI Providers and Registry (PRINCIPLE-003, PRINCIPLE-008)*

**Size**: `73` lines (`2626` bytes)

**Classes:**
- `class TestProviders`
  - Method `.test_presets_exist()`
  - Method `.test_preset_retrieval()`
  - Method `.test_list_provider_names()`
  - Method `.test_get_preset_by_name()`
  - Method `.test_get_provider_factory()`
  - Method `.test_preset_has_vision()`
  - Method `.test_provider_instance_has_vision()`

---

### [`tests/test_rlm_organizer.py`](tests/test_rlm_organizer.py)
> *Unit tests for RLM Organizer (PRINCIPLE-001, PRINCIPLE-007, PRINCIPLE-009)*

**Size**: `210` lines (`9754` bytes)

**Classes:**
- `class MockProvider`
  - Method `.__init__(mock_response)`
  - Method `.test_connection(model)`
  - Method `.complete(prompt, model, temperature, max_tokens)`
  - Method `.analyze_image(image_path, prompt, model, max_tokens)`
- `class TestRLMOrganizer`
  - Method `.test_json_extraction_raw()`
  - Method `.test_json_extraction_markdown_fenced()`
  - Method `.test_heuristic_categorization()`
  - Method `.test_numbered_rename()`
  - Method `.test_organize_mock()`
  - Method `.test_organize_non_vision_provider_routes_to_regular_rlm()`
  - Method `.test_organize_vision_not_implemented_graceful_fallback()`
  - Method `.test_organize_vision_runtime_error_aborts_immediately_and_routes_to_text_rlm()`
  - Method `.test_smart_image_folder_extraction()`
  - Method `.test_heuristic_fallback_batch_image_albums()`
  - Method `.test_sanitize_non_string_types()`
  - Method `.test_process_images_with_integer_json_fields()`

---

### [`tests/test_settings_functionality.py`](tests/test_settings_functionality.py)
> *Unit tests verifying the function of EVERY setting in NoMoreClutter (PRINCIPLE-011).*

**Size**: `250` lines (`10148` bytes)

**Classes:**
- `class TestSettingsFunctionality`
  - Method `.setUp()`
  - Method `.tearDown()`
  - Method `.test_ai_rename_setting_disabled_guarantees_original_name()` - *Setting 'ai_rename=False' must preserve the original filename even if LLM invents a new name.*
  - Method `.test_ai_rename_setting_enabled_applies_sanitized_name()` - *Setting 'ai_rename=True' allows the LLM to suggest clean descriptive names.*
  - Method `.test_create_folders_setting_enabled()` - *Setting 'create_folders=True' creates semantic category folders.*
  - Method `.test_create_folders_setting_disabled_with_existing()` - *Setting 'create_folders=False' maps into existing folders when available.*
  - Method `.test_create_folders_setting_disabled_without_existing()` - *Setting 'create_folders=False' keeps files in destination root if no existing folders exist.*
  - Method `.test_numbered_rename_setting_enabled()` - *Setting 'numbered_rename=True' renames files sequentially per directory.*
  - Method `.test_content_peeking_setting_enabled_and_disabled()` - *Setting 'content_peeking' controls whether snippets are attached in LLM prompts.*
  - Method `.test_embedded_provider_auto_resolution()` - *Setting base_url to 'local://embedded' automatically resolves to EmbeddedProvider.*
  - Method `.test_settings_persistence_all_keys()` - *Settings dictionary must serialize and deserialize all 13 setting fields intact.*
  - Method `.test_corrupted_settings_file_self_healing()` - *A half-written settings.json from a sudden power outage must not crash the application.*

---

### [`tests/test_tree_preview_model.py`](tests/test_tree_preview_model.py)
> *Unit tests for Tree Preview Data Grouping and Selection Logic (PRINCIPLE-011)*

**Size**: `56` lines (`2344` bytes)

**Classes:**
- `class TestTreePreviewLogic`
  - Method `.test_group_changes_by_destination_subfolder()`
  - Method `.test_selective_execution_filtering()`

---

### [`ui/__init__.py`](ui/__init__.py)
> *UI Modules for NoMoreClutter (PRINCIPLE-003: Modularity)*

**Size**: `10` lines (`347` bytes)

---

### [`ui/duplicate_finder.py`](ui/duplicate_finder.py)
> *Smart Duplicate File Finder & Storage Reclaimer UI Dialog*

**Size**: `755` lines (`30610` bytes)

**Classes:**
- `class DuplicateFinderDialog` - *Interactive Duplicate File Finder & Storage Reclaimer.*
  - Method `.__init__(parent, initial_folder)`
  - Method `._build_ui()`
  - Method `._browse_folder()`
  - Method `._start_scan()`
  - Method `._scan_worker(folder, recursive)`
  - Method `._update_progress(msg, frac)`
  - Method `._schedule_drain()`
  - Method `._drain_discovered_groups()`
  - Method `._on_scan_error(err_msg)`
  - Method `._on_scan_complete(groups)`
  - Method `._load_more_cards(count)`
  - Method `._load_all_cards()`
  - Method `._update_load_more_bar()`
  - Method `._render_group_card(group, set_index)`
  - Method `._populate_group_card(card, group, set_index)`
  - Method `._set_as_original(group, new_orig, card, set_index)` - *Designate a duplicate as the canonical original (Keep) and relegate previous original to duplicate.*
  - Method `._select_all_dups()`
  - Method `._deselect_all_dups()`
  - Method `._get_selected_duplicate_paths()`
  - Method `._isolate_selected()`
  - Method `._delete_selected()`
  - Method `._open_file(filepath)` - *Open file directly in the default system application (e.g. Windows Photos, Notepad, Acrobat).*
  - Method `._open_viewer(filepath, compare_filepath)` - *Open the aesthetic in-app file viewer or side-by-side duplicate comparator with foreground lift.*

---

### [`ui/file_viewer.py`](ui/file_viewer.py)
> *In-App File Viewer & Visual Duplicate Inspector (PRINCIPLE-003, PRINCIPLE-007, PRINCIPLE-012)*

**Size**: `707` lines (`28029` bytes)

**Classes:**
- `class FileViewerDialog` - *Rich in-app File Viewer and Side-by-Side Duplicate Comparator.*
  - Method `.__init__(parent, filepath, compare_filepath, on_action_performed)`
  - Method `.destroy()`
  - Method `._build_ui()`
  - Method `._get_category_badge(ext)`
  - Method `._get_file_meta_summary(path)`
  - Method `._build_single_view()`
  - Method `._build_compare_view()`
  - Method `._render_file_preview(parent_widget, filepath, max_w, max_h)`
  - Method `._render_image(parent, filepath, max_w, max_h)`
  - Method `._render_text(parent, filepath)`
  - Method `._render_document(parent, filepath)`
  - Method `._render_binary(parent, filepath)`
  - Method `._copy_primary_path()`
  - Method `._reveal_in_explorer(filepath)`
  - Method `._open_system_default(filepath)`
  - Method `._delete_duplicate_action()`
  - Method `._isolate_duplicate_action()`
  - Method `._set_as_original_action()`

**Functions:**
- `def get_category_badge(ext)` - *Return a visual category badge for a given file extension.*
- `def get_file_meta_summary(path)` - *Extract human-readable file size and modified timestamp.*
- `def compute_image_preview_size(orig_w, orig_h, max_w, max_h)` - *Calculate scaled dimensions preserving aspect ratio without distortion.*
- `def read_text_preview(filepath, max_lines)` - *Read first max_lines safely across common encodings.*
- `def generate_hexdump(data)` - *Generate canonical hex dump representation of binary bytes.*

---

### [`ui/junk_cleaner.py`](ui/junk_cleaner.py)
> *Orphan Folder & Junk Pruner UI Dialog (Option 4)*

**Size**: `401` lines (`15964` bytes)

**Classes:**
- `class JunkCleanerDialog` - *Interactive Orphan Folder & Junk Pruner Dialog.*
  - Method `.__init__(parent, initial_folder)`
  - Method `.destroy()` - *Cleanly abort in-flight scan thread and unbind widgets.*
  - Method `._build_ui()`
  - Method `._browse_folder()`
  - Method `._start_scan()`
  - Method `._scan_worker(folder, empty_dirs, zero_byte, os_debris)`
  - Method `._update_progress(msg, frac)`
  - Method `._on_scan_error(err_msg)`
  - Method `._on_scan_complete(items)`
  - Method `._select_all()`
  - Method `._deselect_all()`
  - Method `._execute_prune()`

---

### [`ui/tree_preview.py`](ui/tree_preview.py)
> *Interactive Tree Preview & Per-File Checkboxes (Pre-Execution Visualizer)*

**Size**: `492` lines (`18841` bytes)

**Classes:**
- `class TreePreviewDialog` - *Interactive visual tree preview dialog with hierarchical folder grouping and checkboxes.*
  - Method `.__init__(parent, changes, output_base_folder, on_confirm)`
  - Method `._group_changes()` - *Partition proposed moves by relative destination directory.*
  - Method `._build_ui()`
  - Method `._toggle_folder(folder_name)` - *Expand or collapse a folder's children.*
  - Method `._expand_all()`
  - Method `._collapse_all()`
  - Method `._on_folder_checkbox_toggled(folder_name)` - *Set all children files to match the parent folder's check state.*
  - Method `._on_file_checkbox_toggled(folder_name)` - *Update parent folder checkbox state based on child file states.*
  - Method `._select_all()`
  - Method `._deselect_all()`
  - Method `._update_selection_counts()` - *Recalculate selected files and update badges and action buttons.*
  - Method `._on_search_changed(*args)` - *Live filter displayed file rows based on query.*
  - Method `._open_file(filepath)` - *Open file directly in the default system application (e.g. Windows Photos, Notepad, Acrobat).*
  - Method `._open_viewer(filepath)` - *Open file inside the aesthetic in-app FileViewerDialog with guaranteed foreground lift.*
  - Method `._confirm_execution()` - *Extract checked files and dispatch to callback.*

---
