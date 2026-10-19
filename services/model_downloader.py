"""
Model Downloader Utility (PRINCIPLE-003, PRINCIPLE-007, PRINCIPLE-008)
Provides 1-click streaming download of compact, quantized GGUF models from HuggingFace
with visual progress reporting, atomic writes, and cancellation support.
Zero external dependencies (uses standard library urllib).
"""

import os
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from pathlib import Path


@dataclass
class ModelCatalogItem:
    id: str
    name: str
    filename: str
    url: str
    size_mb: int
    description: str
    has_vision: bool = False
    mmproj_filename: str = ""
    mmproj_url: str = ""
    mmproj_size_mb: int = 0
    is_default: bool = False

    @property
    def total_size_mb(self) -> int:
        """Total size in MB including vision projector if present."""
        return self.size_mb + self.mmproj_size_mb

    @property
    def capability_badge(self) -> str:
        """Return visual badge indicating model capabilities."""
        return "[👁️ Vision Supported]" if self.has_vision else "[📝 Text-Only]"


# Curated catalog of compact, high-efficiency models optimized for file organization
GGUF_CATALOG: Dict[str, ModelCatalogItem] = {
    "qwen2.5-1.5b": ModelCatalogItem(
        id="qwen2.5-1.5b",
        name="Qwen 2.5 1.5B Instruct (Recommended)",
        filename="qwen2.5-1.5b-instruct-q4_k_m.gguf",
        url="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf",
        size_mb=986,
        description="Best balance of reasoning accuracy and download size (~986MB). High categorization accuracy.",
        has_vision=False,
        is_default=True,
    ),
    "moondream2-vision": ModelCatalogItem(
        id="moondream2-vision",
        name="Moondream 2 Vision & Text (Multimodal)",
        filename="moondream2-text-model-f16.gguf",
        url="https://huggingface.co/moondream/moondream2-gguf/resolve/main/moondream2-text-model-f16.gguf",
        size_mb=2708,
        description="Multimodal vision model. Analyzes photo scenes, objects, and visual documents offline.",
        has_vision=True,
        mmproj_filename="moondream2-mmproj-f16.gguf",
        mmproj_url="https://huggingface.co/moondream/moondream2-gguf/resolve/main/moondream2-mmproj-f16.gguf",
        mmproj_size_mb=868,
        is_default=False,
    ),
    "qwen2.5-0.5b": ModelCatalogItem(
        id="qwen2.5-0.5b",
        name="Qwen 2.5 0.5B Instruct (Ultra-Light)",
        filename="qwen2.5-0.5b-instruct-q4_k_m.gguf",
        url="https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf",
        size_mb=398,
        description="Fastest download (~398MB), minimal RAM usage, ideal for low-end hardware.",
        has_vision=False,
        is_default=False,
    ),
    "smollm2-1.7b": ModelCatalogItem(
        id="smollm2-1.7b",
        name="SmolLM2 1.7B Instruct (Compact)",
        filename="smollm2-1.7b-instruct-q4_k_m.gguf",
        url="https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF/resolve/main/smollm2-1.7b-instruct-q4_k_m.gguf",
        size_mb=1060,
        description="High-quality reasoning from HuggingFace (~1.06GB), robust JSON parsing.",
        has_vision=False,
        is_default=False,
    ),
}


class ModelDownloader:
    """Manages downloading, caching, and verification of embedded model weights."""

    @staticmethod
    def get_weights_dir() -> Path:
        """Return the directory path where GGUF weights are stored."""
        base_dir = Path(__file__).resolve().parent.parent
        weights_dir = base_dir / "models" / "weights"
        weights_dir.mkdir(parents=True, exist_ok=True)
        return weights_dir

    @classmethod
    def get_model_path(cls, filename: str) -> Path:
        """Return absolute path for a model filename."""
        return cls.get_weights_dir() / filename

    @classmethod
    def get_mmproj_path(cls, filename: str) -> Optional[Path]:
        """Return path to mmproj projector file if associated with the given model filename."""
        for item in GGUF_CATALOG.values():
            if (item.filename == filename or item.id == filename) and item.mmproj_filename:
                return cls.get_weights_dir() / item.mmproj_filename
        return None

    @classmethod
    def is_model_downloaded(cls, filename: str) -> bool:
        """Check if model exists locally and has non-trivial size (>10MB).
        If the model is associated with an mmproj projector, verifies both files exist."""
        path = cls.get_model_path(filename)
        if not (path.exists() and path.stat().st_size > 10 * 1024 * 1024):
            return False

        # If model requires an mmproj projector, check it too
        for item in GGUF_CATALOG.values():
            if (item.filename == filename or item.id == filename) and item.mmproj_filename:
                proj_path = cls.get_model_path(item.mmproj_filename)
                if not (proj_path.exists() and proj_path.stat().st_size > 10 * 1024 * 1024):
                    return False
        return True

    @classmethod
    def get_downloaded_models(cls) -> List[ModelCatalogItem]:
        """Return all catalog items that are currently downloaded locally."""
        downloaded = []
        for item in GGUF_CATALOG.values():
            if cls.is_model_downloaded(item.filename):
                downloaded.append(item)
        return downloaded

    @classmethod
    def _download_file(
        cls,
        url: str,
        dest_file: Path,
        progress_callback: Optional[Callable[[int, int, float, float], None]] = None,
        cancel_event=None,
        bytes_already_done: int = 0,
        combined_total_bytes: int = 0,
        start_time: Optional[float] = None,
    ) -> int:
        """Download a single file to dest_file via an atomic .part replacement."""
        if start_time is None:
            start_time = time.time()

        part_file = dest_file.with_suffix(".part")
        if part_file.exists():
            try:
                part_file.unlink()
            except Exception:  # hygiene: allow cleanup of stale part file before download is best-effort
                pass

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "NoMoreClutter-ModelDownloader/1.0"
            }
        )

        chunk_size = 128 * 1024  # 128KB chunks for smooth progress updates
        file_downloaded = 0

        try:
            with urllib.request.urlopen(req, timeout=30) as response, open(part_file, "wb") as out_file:
                content_len = int(response.headers.get("content-length", 0))
                total_for_file = content_len if content_len > 0 else 0
                effective_total = combined_total_bytes if combined_total_bytes > 0 else (bytes_already_done + total_for_file)

                while True:
                    if cancel_event and cancel_event.is_set():
                        raise InterruptedError("Download was cancelled by user.")

                    chunk = response.read(chunk_size)
                    if not chunk:
                        break

                    out_file.write(chunk)
                    file_downloaded += len(chunk)
                    cumulative_down = bytes_already_done + file_downloaded

                    now = time.time()
                    elapsed = max(0.001, now - start_time)
                    speed_mb_s = (cumulative_down / (1024 * 1024)) / elapsed
                    percentage = (cumulative_down / effective_total * 100.0) if effective_total > 0 else 0.0

                    if progress_callback:
                        progress_callback(cumulative_down, effective_total, speed_mb_s, min(100.0, percentage))

            # Atomic rename from .part to final destination
            if part_file.exists():
                part_file.replace(dest_file)

            return file_downloaded

        except Exception as e:
            if part_file.exists():
                try:
                    part_file.unlink()
                except Exception:  # hygiene: allow cleanup of partial download on error is best-effort
                    pass
            raise e

    @classmethod
    def download_model(
        cls,
        model_id: str,
        progress_callback: Optional[Callable[[int, int, float, float], None]] = None,
        cancel_event=None,
    ) -> Path:
        """
        Download a model from the catalog with progress tracking and cancellation.
        Supports multimodal dual-file downloads (base language model + mmproj projector).
        
        Args:
            model_id: Identifier from GGUF_CATALOG (e.g. 'qwen2.5-1.5b', 'moondream2-vision') or custom URL.
            progress_callback: Called with (downloaded_bytes, total_bytes, speed_mb_s, percentage).
            cancel_event: threading.Event to signal abort.
            
        Returns:
            Path: Absolute path to the completed main .gguf file.
        """
        item = GGUF_CATALOG.get(model_id)
        if item:
            url = item.url
            filename = item.filename
        else:
            url = model_id
            filename = os.path.basename(model_id.split("?")[0]) or "model.gguf"

        dest_file = cls.get_model_path(filename)
        
        # Check if already fully downloaded (including mmproj if applicable)
        if cls.is_model_downloaded(filename):
            if progress_callback:
                size = dest_file.stat().st_size
                if item and item.mmproj_filename:
                    proj = cls.get_model_path(item.mmproj_filename)
                    if proj.exists():
                        size += proj.stat().st_size
                progress_callback(size, size, 0.0, 100.0)
            return dest_file

        start_time = time.time()
        combined_total_bytes = (item.total_size_mb * 1024 * 1024) if (item and item.total_size_mb > 0) else 0
        total_downloaded = 0

        # Step 1: Download main model file if needed
        main_already_done = dest_file.exists() and dest_file.stat().st_size > 10 * 1024 * 1024
        if not main_already_done:
            bytes_done = cls._download_file(
                url=url,
                dest_file=dest_file,
                progress_callback=progress_callback,
                cancel_event=cancel_event,
                bytes_already_done=total_downloaded,
                combined_total_bytes=combined_total_bytes,
                start_time=start_time,
            )
            total_downloaded += bytes_done
        else:
            total_downloaded += dest_file.stat().st_size

        # Step 2: Download multimodal projector (mmproj) if model is a vision model
        if item and item.has_vision and item.mmproj_url and item.mmproj_filename:
            proj_file = cls.get_model_path(item.mmproj_filename)
            proj_already_done = proj_file.exists() and proj_file.stat().st_size > 10 * 1024 * 1024
            if not proj_already_done:
                bytes_done = cls._download_file(
                    url=item.mmproj_url,
                    dest_file=proj_file,
                    progress_callback=progress_callback,
                    cancel_event=cancel_event,
                    bytes_already_done=total_downloaded,
                    combined_total_bytes=combined_total_bytes,
                    start_time=start_time,
                )
                total_downloaded += bytes_done

        if progress_callback:
            progress_callback(total_downloaded, total_downloaded, 0.0, 100.0)

        return dest_file
