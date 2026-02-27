import json
import os
from models import FileChange, IMAGE_EXTENSIONS


class LLMService:
    def __init__(self, base_url: str, api_key: str = "not-needed"):
        from openai import OpenAI
        self.client = OpenAI(base_url=base_url, api_key=api_key)
    
    def test_connection(self, model: str = None) -> tuple[bool, str]:
        """Test if the LLM is accessible"""
        try:
            test_model = model or "test"
            response = self.client.chat.completions.create(
                model=test_model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5
            )
            return True, "Connected"
        except Exception as e:
            error_msg = str(e)
            return False, error_msg
    
    def _get_base_path(self, file_path: str) -> str:
        return os.path.dirname(file_path)
    
    def _adjust_path_for_output(self, original_path: str, new_path: str, output_folder: str) -> str:
        if not output_folder:
            return new_path
        
        base = self._get_base_path(original_path)
        if base != output_folder:
            new_path = new_path.replace(base, output_folder, 1)
        return new_path
    
    def analyze_files(self, files: list, model: str, create_new_folders: bool = True, 
                      existing_folders: list = None, analyze_images: bool = False,
                      numbered_rename: bool = False, ai_rename: bool = True,
                      target_folder: str = "", output_folder: str = "") -> list[FileChange]:
        
        if not output_folder:
            output_folder = target_folder
        
        image_files = [f for f in files if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS]
        other_files = [f for f in files if f not in image_files]
        
        results = []
        
        if image_files and analyze_images:
            results.extend(self._analyze_image_files(image_files, model, create_new_folders, existing_folders, output_folder))
        
        if other_files or (image_files and not analyze_images):
            non_image = other_files if not analyze_images else [f for f in files if f not in image_files]
            results.extend(self._analyze_regular_files(non_image, model, create_new_folders, existing_folders, ai_rename))
        
        for r in results:
            r.new_path = self._adjust_path_for_output(r.original, r.new_path, output_folder)
        
        if numbered_rename:
            results = self._apply_numbered_rename(results, output_folder)
        
        return results
    
    def _analyze_regular_files(self, files: list, model: str, create_new_folders: bool, 
                               existing_folders: list, ai_rename: bool = True) -> list[FileChange]:
        if not files:
            return []
        
        # Send EXACT file paths to AI - these must be used exactly as provided!
        file_list = "\n".join([f"- {f}" for f in files])
        existing = existing_folders or []
        existing_str = "\n".join([f"- {f}" for f in existing]) if existing else "None"
        
        if create_new_folders:
            rename_instruction = "Also analyze the filename to provide a better, descriptive name for each file (e.g., 'IMG_001.jpg' → 'vacation_beach_2024.jpg')." if ai_rename else "Keep original filename, only organize into folders."
            prompt = f"""You are a file organizer AI. Given this list of EXACT file paths:
{file_list}

Existing folders in output directory:
{existing_str}

For EVERY file path above, you MUST use the EXACT path as the "original" value. Do NOT change or simplify the paths!

IMPORTANT: 
- Use EACH file path exactly as shown above
- Output folder is where files will go (not the source folder in the path)
- Create descriptive folder names or use existing ones
- {rename_instruction}

Respond with a JSON array:
[
  {{"original": "EXACT_PATH_FROM_ABOVE", "action": "move", "new_path": "OUTPUT_PATH"}}
]

Use EXACT paths from the input list! Do NOT use placeholder paths like "full/path/to/..."!
ALL files must be included.
Return ONLY valid JSON."""
        else:
            rename_instruction = "Also analyze the filename to provide a better, descriptive name (e.g., 'IMG_001.jpg' → 'vacation_beach_2024.jpg')." if ai_rename else "Keep original filename."
            prompt = f"""You are a file organizer AI. Given this list of EXACT file paths:
{file_list}

Existing folders in output directory:
{existing_str}

For EVERY file path above, you MUST use the EXACT path as the "original" value. Do NOT change or simplify the paths!

IMPORTANT:
- Use EACH file path exactly as shown above
- Only use EXISTING folders from the list above
- {rename_instruction}

Respond with a JSON array:
[
  {{"original": "EXACT_PATH_FROM_ABOVE", "action": "move", "new_path": "EXISTING_FOLDER_PATH"}}
]

Use EXACT paths from the input list! Do NOT use placeholder paths!
ALL files must be included.
Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content
            
            if not result_text or not result_text.strip():
                raise LLMError("AI returned empty response")
            
            # Try to find JSON in the response
            result_text = result_text.strip()
            
            # Remove markdown code blocks
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result_text = result_text.strip()
            
            if not result_text:
                raise LLMError("AI returned empty response after parsing")
            
            results = json.loads(result_text)
            
            # Validate results
            if not isinstance(results, list):
                results = []
            
            return [
                FileChange(
                    original=r.get("original", ""),
                    action=r.get("action", "move"),
                    new_path=r.get("new_path", "")
                )
                for r in results if r.get("original") and r.get("new_path")
            ]
        except json.JSONDecodeError as e:
            raise LLMError(f"Failed to parse AI response: {str(e)}")
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f"Failed to analyze files: {str(e)}")
    
    def _analyze_image_files(self, files: list, model: str, create_new_folders: bool,
                             existing_folders: list, target_folder: str) -> list[FileChange]:
        if not files:
            return []
        
        existing = existing_folders or []
        existing_str = "\n".join([f"- {f}" for f in existing]) if existing else "None"
        
        file_list = "\n".join([f"- {os.path.basename(f)}" for f in files])
        
        prompt = f"""You are a vision-capable AI that analyzes images and organizes them.
Image filenames to analyze:
{file_list}

Existing folders in target directory:
{existing_str}

For each image, infer what it might contain based on the filename (e.g., "vacation_photo.jpg" likely contains vacation photos, "screenshot_2024.png" is a screenshot).
Propose folder organization and new names.

Respond with a JSON array of objects:
{{
  "original": "full/path/to/image.ext",
  "action": "move",
  "new_path": "full/path/to/FolderName/image.ext"
}}

Use descriptive folder names. Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content
            results = json.loads(result_text)
            
            return [
                FileChange(
                    original=r["original"],
                    action=r.get("action", "move"),
                    new_path=r.get("new_path", "")
                )
                for r in results
            ]
        except Exception as e:
            raise LLMError(f"Failed to analyze images: {str(e)}")
    
    def _apply_numbered_rename(self, changes: list[FileChange], target_folder: str) -> list[FileChange]:
        folder_counts = {}
        
        for change in changes:
            folder = os.path.dirname(change.new_path)
            ext = os.path.splitext(change.new_path)[1].lower()
            
            if folder not in folder_counts:
                folder_counts[folder] = self._count_files_in_folder(folder, ext)
            
            folder_counts[folder] += 1
            new_num = folder_counts[folder]
            new_name = f"{new_num}{ext}"
            change.new_path = os.path.join(folder, new_name)
        
        return changes
    
    def _count_files_in_folder(self, folder: str, extension: str) -> int:
        if not os.path.exists(folder):
            return 0
        
        count = 0
        for f in os.listdir(folder):
            if os.path.isfile(os.path.join(folder, f)):
                ext = os.path.splitext(f)[1].lower()
                if ext == extension.lower():
                    count += 1
        return count


class LLMError(Exception):
    pass
