# Lazy imports to avoid loading heavy dependencies at startup (PRINCIPLE-007)

def get_FileScanner():
    from .file_scanner import FileScanner
    return FileScanner

def get_LLMService():
    from .llm_service import LLMService, LLMError
    return LLMService, LLMError

def get_RLMOrganizer():
    from .rlm_organizer import RLMOrganizer, RLMOrganizerError
    return RLMOrganizer, RLMOrganizerError

def get_FileExecutor():
    from .file_executor import FileExecutor
    return FileExecutor

def get_provider_registry():
    from .providers import PROVIDER_PRESETS, get_preset, get_preset_by_name, list_provider_names, get_provider
    return PROVIDER_PRESETS, get_preset, get_preset_by_name, list_provider_names, get_provider

def get_model_downloader():
    from .model_downloader import ModelDownloader, GGUF_CATALOG
    return ModelDownloader, GGUF_CATALOG

def get_ollama_manager():
    from .ollama_manager import OllamaManager, RECOMMENDED_OLLAMA_MODELS
    return OllamaManager, RECOMMENDED_OLLAMA_MODELS

def get_document_peeker():
    from .document_peeker import DocumentPeeker
    return DocumentPeeker

def get_benchmark_service():
    from .benchmark_service import BenchmarkService, BenchmarkResult
    return BenchmarkService, BenchmarkResult


