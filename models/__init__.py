from dataclasses import dataclass
from typing import Optional, List


@dataclass
class FileChange:
    original: str
    action: str
    new_path: str
    file_type: Optional[str] = None


@dataclass
class DuplicateGroup:
    file_size: int
    sha256: str
    original: str
    duplicates: List[str]

    @property
    def reclaimable_bytes(self) -> int:
        return self.file_size * len(self.duplicates)

    @property
    def all_files(self) -> List[str]:
        return [self.original] + self.duplicates


@dataclass
class CleanupItem:
    path: str
    item_type: str  # 'empty_dir', 'zero_byte_file', 'os_debris'
    size_bytes: int = 0
    reason: str = ""


@dataclass
class CleanupReport:
    scanned_items: int = 0
    empty_dirs_removed: List[str] = None
    zero_byte_files_removed: List[str] = None
    os_debris_removed: List[str] = None
    reclaimed_bytes: int = 0

    def __post_init__(self):
        if self.empty_dirs_removed is None:
            self.empty_dirs_removed = []
        if self.zero_byte_files_removed is None:
            self.zero_byte_files_removed = []
        if self.os_debris_removed is None:
            self.os_debris_removed = []


@dataclass
class AppSettings:
    provider: str = "groq"
    api_key: str = ""
    llm_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.3-70b-versatile"
    target_folder: str = ""
    selected_types: list = None
    create_new_folders: bool = True
    analyze_images: bool = False
    numbered_rename: bool = False
    ai_rename: bool = True
    content_peeking: bool = True
    auto_execute: bool = False
    limit: str = "50"
    batch_size: str = "15"
    
    def __post_init__(self):
        if self.selected_types is None:
            self.selected_types = []


FILE_TYPE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt", ".xls", ".xlsx"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Code": [".py", ".js", ".ts", ".java", ".cpp", ".c", ".html", ".css", ".json", ".xml", ".yaml"],
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff"}
