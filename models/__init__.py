from dataclasses import dataclass
from typing import Optional, List


@dataclass
class FileChange:
    original: str
    action: str
    new_path: str
    file_type: Optional[str] = None


@dataclass
class AppSettings:
    llm_url: str = "http://localhost:1234/v1"
    llm_model: str = "llama3"
    target_folder: str = ""
    selected_types: list = None
    create_new_folders: bool = True
    analyze_images: bool = False
    numbered_rename: bool = False
    
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
