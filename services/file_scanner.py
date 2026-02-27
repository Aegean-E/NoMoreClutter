import os
from typing import List


class FileScanner:
    @staticmethod
    def scan_folder(folder_path: str, extensions: List[str], include_subfolders: bool = False) -> List[str]:
        if not folder_path or not extensions:
            return []
        
        files = []
        
        if include_subfolders:
            # Scan all subfolders
            for root, _, filenames in os.walk(folder_path):
                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in extensions:
                        files.append(os.path.join(root, filename))
        else:
            # Only scan the specified folder, not subfolders
            for filename in os.listdir(folder_path):
                full_path = os.path.join(folder_path, filename)
                if os.path.isfile(full_path):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in extensions:
                        files.append(full_path)
        
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
