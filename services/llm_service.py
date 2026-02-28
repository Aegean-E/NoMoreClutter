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
            
            print(f"DEBUG AI: Raw results: {results}")
            
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
    
    def _get_mime_type(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
            '.gif': 'image/gif', '.webp': 'image/webp', '.bmp': 'image/bmp',
            '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.tiff': 'image/tiff'
        }
        return mime_types.get(ext, 'image/jpeg')
    
    def _validate_image_suggestion(self, image_path: str, suggested_folder: str, model: str) -> bool:
        """Ask AI to validate if the folder suggestion is correct"""
        import base64
        
        try:
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            
            messages = [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{self._get_mime_type(image_path)};base64,{img_data}"}},
                    {"type": "text", "text": f"""Look at this image. Is the folder "{suggested_folder}" appropriate?
Respond with ONLY: true or false"""}
                ]
            }]
            
            response = self.client.chat.completions.create(model=model, messages=messages, max_tokens=5, temperature=0.1)
            answer = response.choices[0].message.content.strip().lower()
            return "true" in answer or "yes" in answer
        except:
            return True
    
    def _reanalyze_image(self, image_path: str, model: str, existing_folders: list) -> str:
        """Re-analyze an image with more careful prompting"""
        import base64
        try:
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            
            messages = [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{self._get_mime_type(image_path)};base64,{img_data}"}},
                    {"type": "text", "text": "What is in this image? Choose an appropriate category/folder name. Examples: Nature, People, Animals, Cars, Screenshots, Memes, Art, Documents, Wallpapers. Respond with ONLY the category."}
                ]
            }]
            
            response = self.client.chat.completions.create(model=model, messages=messages, max_tokens=20, temperature=0.1)
            return response.choices[0].message.content.strip()
        except:
            return "Other"
    
    def _get_descriptive_filename(self, image_path: str, model: str) -> str:
        """Ask AI to give a descriptive filename based on image content"""
        import base64
        try:
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            ext = os.path.splitext(image_path)[1].lower()
            
            messages = [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{self._get_mime_type(image_path)};base64,{img_data}"}},
                    {"type": "text", "text": "Look at this image. Give a SHORT name (1-2 words). Examples: sunset_beach, cat_portrait, family_photo. Respond with ONLY the name."}
                ]
            }]
            
            response = self.client.chat.completions.create(model=model, messages=messages, max_tokens=20, temperature=0.3)
            name = response.choices[0].message.content.strip()
            name = "".join(c for c in name if c.isalnum() or c == "_")
            return name + ext
        except:
            return ""
    
    def _validate_filename(self, image_path: str, suggested_name: str, model: str) -> bool:
        """Ask AI to validate if the filename describes the image"""
        import base64
        try:
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            
            messages = [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{self._get_mime_type(image_path)};base64,{img_data}"}},
                    {"type": "text", "text": f"""Look at this image. Is the name "{suggested_name}" appropriate? Respond with ONLY: true or false"""}
                ]
            }]
            
            response = self.client.chat.completions.create(model=model, messages=messages, max_tokens=5, temperature=0.1)
            answer = response.choices[0].message.content.strip().lower()
            return "true" in answer or "yes" in answer
        except:
            return True
    
    def _reanalyze_filename(self, image_path: str, model: str) -> str:
        """Re-analyze image to get better descriptive filename"""
        import base64
        try:
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            ext = os.path.splitext(image_path)[1].lower()
            
            messages = [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{self._get_mime_type(image_path)};base64,{img_data}"}},
                    {"type": "text", "text": "Look at this image carefully. What do you see? Give SHORT name (1-2 words). Respond with ONLY the name."}
                ]
            }]
            
            response = self.client.chat.completions.create(model=model, messages=messages, max_tokens=20, temperature=0.3)
            name = response.choices[0].message.content.strip()
            name = "".join(c for c in name if c.isalnum() or c == "_")
            return name + ext
        except:
            return ""
    
    def _analyze_image_files(self, files: list, model: str, create_new_folders: bool,
                             existing_folders: list, target_folder: str) -> list[FileChange]:
        if not files:
            return []
        
        # Ensure target_folder is valid
        if not target_folder:
            target_folder = os.path.dirname(files[0]) if files else ""
        
        print(f"DEBUG IMAGE: target_folder = {target_folder}, files[0] = {files[0] if files else 'NO FILES'}")
        
        import base64
        
        existing = existing_folders or []
        existing_str = "\n".join([f"- {f}" for f in existing]) if existing else "None"
        
        # Process images one at a time to avoid LM Studio issues
        all_results = []
        
        for idx, img_path in enumerate(files):
            try:
                import base64
                with open(img_path, "rb") as f:
                    data = f.read()
                    if len(data) < 100:
                        continue
                    img_data = base64.b64encode(data).decode("utf-8")
                
                messages = [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{self._get_mime_type(img_path)};base64,{img_data}"}
                        },
                        {
                            "type": "text",
                            "text": f"""What is in this image? Choose category: Nature, People, Animals, Cars, Screenshots, Memes, Art, Documents, Wallpapers, Other. Also give short descriptive name (1-2 words). Respond JSON: [{{"filename": "name.jpg", "folder": "Category"}}]"""
                        }
                    ]
                }]
                
                response = self.client.chat.completions.create(model=model, messages=messages, temperature=0.3)
                result_text = response.choices[0].message.content.strip()
                
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0]
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0]
                
                results = json.loads(result_text)
                
                if results:
                    r = results[0]
                    folder = r.get("folder", "Other")
                    new_name = r.get("filename", os.path.basename(img_path))
                    
                    # Validate folder
                    is_valid_folder = self._validate_image_suggestion(img_path, folder, model)
                    if not is_valid_folder:
                        folder = self._reanalyze_image(img_path, model, existing)
                    
                    # Validate name
                    is_valid_name = self._validate_filename(img_path, new_name, model)
                    if not is_valid_name:
                        new_name = self._reanalyze_filename(img_path, model)
                        if not new_name:
                            new_name = os.path.basename(img_path)
                    
                    if not create_new_folders:
                        folder = self._find_existing_folder_by_ai_suggestion(folder, existing, target_folder)
                    else:
                        folder = os.path.join(target_folder, folder)
                    
                    all_results.append(FileChange(
                        original=img_path,
                        action="move",
                        new_path=os.path.join(folder, new_name)
                    ))
                    
                print(f"DEBUG: Processed {idx+1}/{len(files)}")
                
            except Exception as e:
                print(f"DEBUG: Error processing {img_path}: {e}")
                continue
        
        return all_results
    
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
