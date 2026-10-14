# Data Models & Schemas 📊

This document outlines the data structures, schemas, and configurations used across NoMoreClutter.

---

## 1. Domain Models (`models/__init__.py`)

### `FileCategory` (Enum)
Defines high-level file classification domains:
- `IMAGES`: `.jpg`, `.png`, `.gif`, `.bmp`, `.webp`, `.svg`, `.ico`, `.tiff`
- `DOCUMENTS`: `.pdf`, `.docx`, `.doc`, `.txt`, `.xlsx`, `.pptx`, `.csv`, `.md`, etc.
- `AUDIO`: `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`
- `VIDEO`: `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.webm`
- `ARCHIVES`: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`
- `CODE`: `.py`, `.js`, `.ts`, `.html`, `.css`, `.json`, `.cpp`, `.java`, etc.

### `FileInfo` (Dataclass)
Represents a single discovered file:
```python
@dataclass
class FileInfo:
    path: str              # Absolute filesystem path
    name: str              # Original filename with extension
    size: int              # File size in bytes
    extension: str         # Lowercase extension including dot (e.g. '.pdf')
    category: FileCategory # High-level category
    parent_dir: str        # Absolute path of directory containing the file
    modified_time: float   # Last modified timestamp
```

### `ScanResult` (Dataclass)
Aggregated results from a directory scan:
```python
@dataclass
class ScanResult:
    total_files: int
    total_size: int
    files_by_category: Dict[FileCategory, List[FileInfo]]
    source_dir: str
```

### `FileMoveRecord` (Dataclass)
Stored in the undo stack for exact reversibility:
```python
@dataclass
class FileMoveRecord:
    original_path: str   # Where the file originally came from
    new_path: str        # Where the file was moved to
    timestamp: float     # Epoch time of move
```

---

## 2. Provider Models (`services/providers/base.py` & `registry.py`)

### `ProviderConfig` (Dataclass)
Stores provider connection settings:
```python
@dataclass
class ProviderConfig:
    name: str                   # Provider display name
    api_url: str                # Base API URL
    api_key: str = ""           # API key
    default_model: str = ""     # Recommended default model
    requires_key: bool = True   # Whether an API key is mandatory
    doc_url: str = ""           # Link to obtain key or documentation
    timeout_seconds: float = 30.0
```

---

## 3. Dense Token Payloads & JSON Schemas

### Candidate File Serialization Format
Used in prompt payloads to minimize token consumption:
```json
[
  {"id": 0, "name": "IMG_2024.jpg", "ext": ".jpg"},
  {"id": 1, "name": "Q3_Financials.xlsx", "ext": ".xlsx"}
]
```

### LLM Response Format
The model returns a JSON array strictly referencing item IDs:
```json
[
  {
    "id": 0,
    "category": "Photos/Vacation",
    "suggested_name": "vacation_beach.jpg"
  },
  {
    "id": 1,
    "category": "Finance/Reports",
    "suggested_name": "Q3_Financials_2024.xlsx"
  }
]
```

---

## 4. Settings Configuration (`settings.json`)

Persisted user preferences saved at the application root:
```json
{
  "api_url": "https://api.groq.com/openai/v1",
  "api_key": "gsk_...",
  "model_name": "llama-3.3-70b-versatile",
  "provider": "Groq (Cloud)",
  "create_folders": true,
  "analyze_images": true,
  "numbered_renaming": false,
  "ai_rename": true,
  "auto_execute": false,
  "batch_size": 10,
  "max_files": 1000
}
```
*(Note: `settings.json` is explicitly gitignored to prevent accidental key leaks).*
