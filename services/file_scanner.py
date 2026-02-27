import os
from typing import List


class FileScanner:
    @staticmethod
    def scan_folder(folder_path: str, extensions: List[str]) -> List[str]:
        if not folder_path or not extensions:
            return []
        
        files = []
        for root, _, filenames in os.walk(folder_path):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in extensions:
                    files.append(os.path.join(root, filename))
        return files
    
    @staticmethod
    def get_extension(filename: str) -> str:
        return os.path.splitext(filename)[1].lower()
    
    @staticmethod
    def get_category(extension: str, categories: dict) -> str:
        for category, extensions in categories.items():
            if extension in extensions:
                return category
        return "Other"
