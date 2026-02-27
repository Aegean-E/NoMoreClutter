import os
import shutil
from models import FileChange


class FileExecutor:
    @staticmethod
    def execute(changes: list[FileChange]) -> tuple[int, int]:
        success = 0
        errors = 0
        
        for change in changes:
            try:
                os.makedirs(os.path.dirname(change.new_path), exist_ok=True)
                
                if change.action == "move":
                    shutil.move(change.original, change.new_path)
                else:
                    shutil.copy2(change.original, change.new_path)
                    os.remove(change.original)
                
                success += 1
            except Exception as e:
                errors += 1
                print(f"Error processing {change.original}: {e}")
        
        return success, errors
