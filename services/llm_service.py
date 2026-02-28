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
    
    def analyze_files(self, files: list, model: str, create_new_folders: bool = True, 
                      existing_folders: list = None, analyze_images: bool = False,
                      numbered_rename: bool = False, ai_rename: bool = True,
                      target_folder: str = "", output_folder: str = "") -> list[FileChange]:
        
        if not output_folder:
            output_folder = target_folder or ""
        
        if not output_folder:
            output_folder = os.path.dirname(files[0]) if files else ""
        
        image_files = [f for f in files if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS]
        other_files = [f for f in files if f not in image_files]
        
        results = []
        
        if image_files and analyze_images:
            results.extend(self._analyze_image_files(image_files, model, create_new_folders, existing_folders, output_folder))
        
        if other_files or (image_files and not analyze_images):
            non_image = other_files if not analyze_images else [f for f in files if f not in image_files]
            results.extend(self._analyze_regular_files(non_image, model, create_new_folders, existing_folders, ai_rename))
        
        # Apply numbered rename to all results BEFORE matching (so it persists)
        if numbered_rename and results:
            results = self._apply_numbered_rename(results, output_folder)
        
        # Return early with numbered rename already applied - don't let main.py reconstruct paths
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
            
            # Debug: log first 200 chars of response
            print(f"AI response (first 200): {result_text[:200] if result_text else 'EMPTY'}")
            
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
            
            print(f"DEBUG AI: Got {len(results)} results, first result keys: {results[0].keys() if results else 'NONE'}")
            print(f"DEBUG AI: First result: {results[0] if results else 'NONE'}")
            
            # Validate results
            if not isinstance(results, list):
                results = []
            
            # Flexible key matching
            parsed_results = []
            for r in results:
                original = r.get("original") or r.get("source") or r.get("file") or r.get("file_path") or r.get("path", "")
                new_path = r.get("new_path") or r.get("destination") or r.get("target") or r.get("new_path") or r.get("output") or ""
                
                if original and new_path:
                    parsed_results.append(FileChange(
                        original=original,
                        action=r.get("action", "move"),
                        new_path=new_path
                    ))
            
            return parsed_results
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
        
        # Ensure target_folder is valid
        if not target_folder:
            target_folder = os.path.dirname(files[0]) if files else ""
        
        import base64
        
        existing = existing_folders or []
        existing_str = "\n".join([f"- {f}" for f in existing]) if existing else "None"
        
        # Send images to AI for vision analysis
        messages = [{"role": "user", "content": []}]
        
        # Add each image to the message
        for img_path in files:
            try:
                with open(img_path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode("utf-8")
                
                # Add image to message
                messages[0]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_data}"
                    }
                })
            except Exception:
                pass  # Skip if can't read image
        
        # Add analysis request
        file_list = "\n".join([f"- {os.path.basename(f)}" for f in files])
        messages[0]["content"].append({
            "type": "text",
            "text": f"""Analyze these images and suggest folder organization.

Image files: {file_list}

Existing folders: {existing_str}

For each image:
1. Analyze what's in the image (landscape, person, screenshot, document, meme, etc.)
2. Suggest a descriptive folder name (e.g., "Nature", "People", "Screenshots", "Documents", "Memes")
3. Keep or suggest a better filename

Respond with JSON array:
[
  {{"filename": "image.jpg", "folder": "Suggested_Folder", "new_name": "optional_better_name.jpg"}}
]

ALL images must be included. Return ONLY valid JSON."""
        })
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content
            
            # Parse JSON from response
            result_text = result_text.strip()
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            results = json.loads(result_text)
            
            # Map results back to actual files
            file_changes = []
            for result in results:
                filename = result.get("filename", "")
                folder = result.get("folder", "General")
                new_name = result.get("new_name", filename)
                
                # Find matching file
                for f in files:
                    if os.path.basename(f) == filename:
                        # If create_new_folders is False, use existing folder only
                        if not create_new_folders:
                            # Only use existing folders - find best match
                            new_folder = self._find_existing_folder_by_ai_suggestion(folder, existing, target_folder)
                        else:
                            new_folder = os.path.join(target_folder, folder)
                        
                        new_path = os.path.join(new_folder, new_name)
                        file_changes.append(FileChange(
                            original=f,
                            action="move",
                            new_path=new_path
                        ))
                        break
            
            return file_changes
            
        except Exception as e:
            raise LLMError(f"Failed to analyze images: {str(e)}")
    
    def _find_existing_folder_by_ai_suggestion(self, ai_folder: str, existing_folders: list, target_folder: str) -> str:
        """Find an existing folder that best matches the AI's folder suggestion"""
        if not existing_folders or not target_folder:
            return target_folder or ""
        
        ai_folder_lower = ai_folder.lower().strip()
        
        # First try exact or close match
        for folder in existing_folders:
            if folder.lower() == ai_folder_lower:
                return os.path.join(target_folder, folder)
        
        # Try partial match
        for folder in existing_folders:
            if ai_folder_lower in folder.lower() or folder.lower() in ai_folder_lower:
                return os.path.join(target_folder, folder)
        
        # Use first existing folder as fallback
        return os.path.join(target_folder, existing_folders[0])
    
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
    
    def _find_existing_folder(self, extension: str, existing_folders: list, target_folder: str) -> str:
        """Find an existing folder that matches the file extension"""
        ext_to_category = {
            ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images", ".bmp": "Images", ".webp": "Images",
            ".pdf": "Documents", ".doc": "Documents", ".docx": "Documents", ".txt": "Documents",
            ".mp4": "Videos", ".avi": "Videos", ".mkv": "Videos", ".mov": "Videos",
            ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio",
            ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
            ".py": "Code", ".js": "Code", ".ts": "Code", ".java": "Code",
        }
        
        # Try to find folder by category
        category = ext_to_category.get(extension.lower(), "Other")
        
        # Check if folder exists
        for folder in existing_folders:
            if folder.lower() == category.lower():
                return os.path.join(target_folder, folder)
        
        # Return first existing folder or target
        if existing_folders:
            return os.path.join(target_folder, existing_folders[0])
        
        return target_folder
    
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
