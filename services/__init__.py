# Lazy imports to avoid loading heavy dependencies at startup
def get_FileScanner():
    from .file_scanner import FileScanner
    return FileScanner

def get_LLMService():
    from .llm_service import LLMService, LLMError
    return LLMService, LLMError

def get_FileExecutor():
    from .file_executor import FileExecutor
    return FileExecutor
