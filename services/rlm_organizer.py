"""
Recursive Language Model (RLM) File Organizer Engine
Implements PRINCIPLE-001 (RLM Compatibility), PRINCIPLE-007 (Performance),
and PRINCIPLE-009 (Token Frugality & Context Budgeting).
"""

import json
import os
import re
from typing import List, Dict, Any, Optional
from models import FileChange, IMAGE_EXTENSIONS, FILE_TYPE_CATEGORIES
from .providers.base import BaseAIProvider
from .document_peeker import DocumentPeeker


class RLMOrganizerError(Exception):
    """Base exception for RLM Organizer operations."""
    pass


class RLMOrganizer:
    """Recursive Language Model File Organization Engine."""

    def __init__(self, provider: BaseAIProvider):
        self.provider = provider

    def organize(
        self,
        files: List[str],
        model: str,
        output_folder: str,
        existing_folders: Optional[List[str]] = None,
        create_new_folders: bool = True,
        analyze_images: bool = False,
        ai_rename: bool = True,
        numbered_rename: bool = False,
        content_peeking: bool = True,
        cluster_batch_size: int = 15,
        progress_callback=None,
    ) -> List[FileChange]:
        """Perform hierarchical RLM organization on file collection."""
        if not files:
            return []

        existing = existing_folders or []
        changes: List[FileChange] = []

        # 1. Hierarchical Domain Partitioning (Media vs Non-Media)
        image_files = [f for f in files if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS]
        regular_files = [f for f in files if f not in image_files]

        # 2. Vision Pipeline (Single-pass analysis for images)
        if image_files and analyze_images:
            img_results = self._process_images_hierarchical(
                files=image_files,
                model=model,
                output_folder=output_folder,
                existing_folders=existing,
                create_new_folders=create_new_folders,
                ai_rename=ai_rename,
                progress_callback=progress_callback,
            )
            changes.extend(img_results)

        # Non-image files or images when vision is disabled
        other_files = regular_files if analyze_images else files
        if other_files:
            # 3. RLM Clustering and Recursive Bounded Batching with Document Content Peeking
            reg_results = self._process_regular_rlm(
                files=other_files,
                model=model,
                output_folder=output_folder,
                existing_folders=existing,
                create_new_folders=create_new_folders,
                ai_rename=ai_rename,
                content_peeking=content_peeking,
                cluster_batch_size=cluster_batch_size,
                progress_callback=progress_callback,
            )
            changes.extend(reg_results)

        # 4. Optional Numbered Rename Layer
        if numbered_rename and changes:
            changes = self._apply_numbered_rename(changes)

        return changes

    def _process_regular_rlm(
        self,
        files: List[str],
        model: str,
        output_folder: str,
        existing_folders: List[str],
        create_new_folders: bool,
        ai_rename: bool,
        content_peeking: bool,
        cluster_batch_size: int,
        progress_callback=None,
    ) -> List[FileChange]:
        """Recursive bounded batch processing with compact payload serialization."""
        all_changes: List[FileChange] = []
        total = len(files)

        # Decompose into bounded recursive clusters
        for i in range(0, total, cluster_batch_size):
            batch = files[i:i + cluster_batch_size]
            cluster_changes = self._analyze_cluster(
                batch=batch,
                model=model,
                output_folder=output_folder,
                existing_folders=existing_folders,
                create_new_folders=create_new_folders,
                ai_rename=ai_rename,
                content_peeking=content_peeking,
            )
            all_changes.extend(cluster_changes)

            if progress_callback:
                progress_callback(len(cluster_changes), len(all_changes), total)

        return all_changes

    def _analyze_cluster(
        self,
        batch: List[str],
        model: str,
        output_folder: str,
        existing_folders: List[str],
        create_new_folders: bool,
        ai_rename: bool,
        content_peeking: bool = True,
    ) -> List[FileChange]:
        """Analyze a scoped cluster using compact token-efficient payload schemas."""
        # Dense payload: Transmit relative filenames + IDs rather than full paths (saves ~70% tokens)
        dense_items = []
        id_to_filepath: Dict[int, str] = {}
        for idx, path in enumerate(batch):
            id_to_filepath[idx] = path
            item_data = {"id": idx, "name": os.path.basename(path)}
            if content_peeking:
                peek_snippet = DocumentPeeker.peek(path, max_chars=180)
                if peek_snippet:
                    item_data["peek"] = peek_snippet
            dense_items.append(item_data)

        items_json = json.dumps(dense_items, ensure_ascii=False)
        existing_json = json.dumps(existing_folders, ensure_ascii=False) if existing_folders else "[]"

        rename_rule = (
            "Suggest clean, descriptive filename (keep same extension). Examples: 'receipt_march.pdf', 'client_presentation.pptx'."
            if ai_rename
            else "Keep original filename exactly."
        )

        folder_rule = (
            "Create meaningful category folder (e.g. 'Invoices', 'Work_Reports', 'Code_Scripts', 'Personal')."
            if create_new_folders
            else f"Choose the best matching folder from existing folders: {existing_json}. If none fit, use 'General'."
        )

        peek_rule = (
            "3. If a file includes a 'peek' snippet, use its text content (e.g. invoice details, project topic, author) to choose the best folder and descriptive filename."
            if content_peeking
            else ""
        )

        camera_photo_rule = (
            "4. For photos or image files with numeric or camera timestamps (e.g. '20170926_112101.jpg', 'IMG_0001.jpg', 'DSC_100.jpg'): "
            "do NOT guess or hallucinate specific animal, object, or scene contents (such as 'Animals' or 'Cars') unless explicit keywords exist in the filename. "
            "Instead, organize them by year/date or general photo albums (e.g. 'Photos/2017', 'Photos/2018', 'Camera_Roll') based on the timestamp."
        )

        prompt = f"""You are a fast, structured file organizer. Categorize these files:
{items_json}

Available existing folders:
{existing_json}

Rules:
1. {folder_rule}
2. {rename_rule}
{peek_rule}
{camera_photo_rule}
Respond ONLY with a valid JSON array of objects:
[{{"id": 0, "folder": "Folder_Name", "name": "descriptive_filename.ext"}}]"""

        try:
            raw_response = self.provider.complete(prompt=prompt, model=model, temperature=0.2)
            parsed = self._extract_json(raw_response)
            
            changes: List[FileChange] = []
            visited_ids = set()

            if isinstance(parsed, list):
                for item in parsed:
                    item_id = item.get("id")
                    if item_id is not None and item_id in id_to_filepath:
                        orig_path = id_to_filepath[item_id]
                        visited_ids.add(item_id)
                        
                        folder_name = self._sanitize_folder_name(item.get("folder", "General"))
                        
                        # Deterministic AI rename setting enforcement
                        if ai_rename:
                            new_filename = self._sanitize_filename(item.get("name", os.path.basename(orig_path)), orig_path)
                        else:
                            new_filename = os.path.basename(orig_path)

                        # Camera timestamp anti-hallucination guard for images without vision
                        ext = os.path.splitext(orig_path)[1].lower()
                        basename = os.path.basename(orig_path)
                        if ext in IMAGE_EXTENSIONS:
                            date_match = re.search(r"\b(19\d{2}|20\d{2})(\d{2})\d{2}[-_]\d{4,6}", basename)
                            if date_match:
                                year = date_match.group(1)
                                hallucinated_tags = {"animals", "animal", "pets", "pet", "general", "other", "random", "misc", "untitled", "images", "photos"}
                                if folder_name.lower() in hallucinated_tags:
                                    folder_name = f"Photos/{year}"
                                if not new_filename or any(new_filename.lower().startswith(p) for p in ["animal", "image", "photo_1", "photo_2"]):
                                    new_filename = basename
                        
                        # Preserve existing folder constraint if create_new_folders is False
                        if not create_new_folders:
                            if existing_folders:
                                folder_name = self._match_closest_folder(folder_name, existing_folders)
                                target_path = os.path.join(output_folder, folder_name, new_filename)
                            else:
                                target_path = os.path.join(output_folder, new_filename)
                        else:
                            target_path = os.path.join(output_folder, folder_name, new_filename)

                        changes.append(FileChange(
                            original=orig_path,
                            action="move",
                            new_path=target_path
                        ))

            # Defensive fallback for any files missed by the LLM
            for idx, orig_path in id_to_filepath.items():
                if idx not in visited_ids:
                    cat = self.get_heuristic_category(orig_path)
                    target_path = os.path.join(output_folder, cat, os.path.basename(orig_path))
                    changes.append(FileChange(original=orig_path, action="move", new_path=target_path))

            return changes

        except Exception as e:
            # Graceful Heuristic Degradation (PRINCIPLE-008)
            print(f"RLM Cluster error: {e}. Falling back to heuristic classification.")
            return self._heuristic_fallback_batch(batch, output_folder, existing_folders)

    def _process_images_hierarchical(
        self,
        files: List[str],
        model: str,
        output_folder: str,
        existing_folders: List[str],
        create_new_folders: bool,
        ai_rename: bool,
        progress_callback=None,
    ) -> List[FileChange]:
        """Single-pass token-frugal vision analysis (reduces 5 roundtrips down to 1)."""
        results: List[FileChange] = []
        total = len(files)

        prompt = (
            "Analyze this image. Output JSON with:\n"
            "- 'folder': 1-word category (e.g. Nature, People, Screenshots, Documents, Artwork, Animals, Memes, Wallpapers, Other)\n"
            "- 'name': short descriptive filename (1-3 words, e.g. sunset_ocean, tax_receipt)\n"
            "Format: {\"folder\": \"Category\", \"name\": \"descriptive_name\"}"
        )

        for idx, img_path in enumerate(files):
            try:
                if os.path.getsize(img_path) < 100:
                    continue

                raw = self.provider.analyze_image(image_path=img_path, prompt=prompt, model=model)
                parsed = self._extract_json(raw)

                if isinstance(parsed, list) and parsed:
                    parsed = parsed[0]

                if isinstance(parsed, dict):
                    folder = self._sanitize_folder_name(parsed.get("folder", "Images"))
                    raw_name = parsed.get("name", "")
                    ext = os.path.splitext(img_path)[1].lower()
                    
                    if ai_rename and raw_name:
                        clean_name = re.sub(r"[^\w\-_]", "_", raw_name).strip("_")
                        new_filename = f"{clean_name}{ext}" if not clean_name.endswith(ext) else clean_name
                    else:
                        new_filename = os.path.basename(img_path)
                else:
                    folder = "Images"
                    new_filename = os.path.basename(img_path)

                if not create_new_folders:
                    if existing_folders:
                        folder = self._match_closest_folder(folder, existing_folders)
                        new_path = os.path.join(output_folder, folder, new_filename)
                    else:
                        new_path = os.path.join(output_folder, new_filename)
                else:
                    new_path = os.path.join(output_folder, folder, new_filename)
                results.append(FileChange(original=img_path, action="move", new_path=new_path))

            except Exception as e:
                print(f"Vision error on {img_path}: {e}")
                cat = "Images"
                new_path = os.path.join(output_folder, cat, os.path.basename(img_path))
                results.append(FileChange(original=img_path, action="move", new_path=new_path))

            if progress_callback:
                progress_callback(1, len(results), total)

        return results

    @staticmethod
    def get_heuristic_category(file_path: str) -> str:
        """Instant zero-install heuristic categorization by file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        for cat, extensions in FILE_TYPE_CATEGORIES.items():
            if ext in extensions:
                return cat
        return "Other"

    def _heuristic_fallback_batch(self, files: List[str], output_folder: str, existing_folders: List[str]) -> List[FileChange]:
        """Pure Python rule-based classification when LLM is unreachable."""
        changes = []
        for f in files:
            cat = self.get_heuristic_category(f)
            folder = cat
            if existing_folders:
                folder = self._match_closest_folder(cat, existing_folders)
            changes.append(FileChange(
                original=f,
                action="move",
                new_path=os.path.join(output_folder, folder, os.path.basename(f))
            ))
        return changes

    @staticmethod
    def _apply_numbered_rename(changes: List[FileChange]) -> List[FileChange]:
        """Apply sequential numbering (1.jpg, 2.jpg) scoped per folder."""
        folder_counters: Dict[str, int] = {}
        for c in changes:
            dest_dir = os.path.dirname(c.new_path)
            ext = os.path.splitext(c.new_path)[1].lower()
            key = f"{dest_dir}::{ext}"
            
            folder_counters[key] = folder_counters.get(key, 0) + 1
            idx = folder_counters[key]
            c.new_path = os.path.join(dest_dir, f"{idx}{ext}")
        return changes

    @staticmethod
    def _match_closest_folder(target: str, existing_folders: List[str]) -> str:
        """Find best match among existing directories."""
        if not existing_folders:
            return target
        t_low = target.lower().strip()
        for f in existing_folders:
            if f.lower().strip() == t_low:
                return f
        for f in existing_folders:
            if t_low in f.lower() or f.lower() in t_low:
                return f
        return existing_folders[0]

    @staticmethod
    def _sanitize_folder_name(name: str) -> str:
        clean = re.sub(r'[<>:"/\\|?*]', '_', name).strip().strip('.')
        return clean if clean else "General"

    @staticmethod
    def _sanitize_filename(name: str, original_path: str) -> str:
        orig_ext = os.path.splitext(original_path)[1]
        clean = re.sub(r'[<>:"/\\|?*]', '_', name).strip()
        if not clean:
            return os.path.basename(original_path)
        if not os.path.splitext(clean)[1]:
            clean += orig_ext
        return clean

    @staticmethod
    def _extract_json(text: str) -> Any:
        """Cleanly extract JSON payloads from markdown blocks or raw text."""
        if not text or not text.strip():
            return None
        t = text.strip()
        if "```json" in t:
            t = t.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in t:
            t = t.split("```", 1)[1].split("```", 1)[0]
        t = t.strip()
        try:
            return json.loads(t)
        except Exception:
            # Fallback regex search for json list or dict
            match = re.search(r"(\[.*\]|\{.*\})", t, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
            return None
