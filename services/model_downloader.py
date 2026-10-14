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
    is_default: bool = False


# Curated catalog of compact, high-efficiency models optimized for file organization
GGUF_CATALOG: Dict[str, ModelCatalogItem] = {
    "qwen2.5-0.5b": ModelCatalogItem(
        id="qwen2.5-0.5b",
        name="Qwen 2.5 0.5B Instruct (Ultra-Light)",
        filename="qwen2.5-0.5b-instruct-q4_k_m.gguf",
        url="https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf",
        size_mb=398,
        description="Fastest download (~398MB), minimal RAM usage, ideal for low-end hardware.",
        is_default=False,
    ),
    "qwen2.5-1.5b": ModelCatalogItem(
        id="qwen2.5-1.5b",
        name="Qwen 2.5 1.5B Instruct (Recommended)",
        filename="qwen2.5-1.5b-instruct-q4_k_m.gguf",
        url="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf",
        size_mb=986,
        description="Best balance of reasoning accuracy and download size (~986MB). High categorization accuracy.",
        is_default=True,
    ),
    "smollm2-1.7b": ModelCatalogItem(
        id="smollm2-1.7b",
        name="SmolLM2 1.7B Instruct (Compact)",
        filename="smollm2-1.7b-instruct-q4_k_m.gguf",
        url="https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF/resolve/main/smollm2-1.7b-instruct-q4_k_m.gguf",
        size_mb=1060,
        description="High-quality reasoning from HuggingFace (~1.06GB), robust JSON parsing.",
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
    def is_model_downloaded(cls, filename: str) -> bool:
        """Check if model exists locally and has non-trivial size (>10MB)."""
        path = cls.get_model_path(filename)
        return path.exists() and path.stat().st_size > 10 * 1024 * 1024

    @classmethod
    def get_downloaded_models(cls) -> List[ModelCatalogItem]:
        """Return all catalog items that are currently downloaded locally."""
        downloaded = []
        for item in GGUF_CATALOG.values():
            if cls.is_model_downloaded(item.filename):
                downloaded.append(item)
        return downloaded

    @classmethod
    def download_model(
        cls,
        model_id: str,
        progress_callback: Optional[Callable[[int, int, float, float], None]] = None,
        cancel_event=None,
    ) -> Path:
        """
        Download a model from the catalog with progress tracking and cancellation.
        
        Args:
            model_id: Identifier from GGUF_CATALOG (e.g. 'qwen2.5-1.5b') or custom URL.
            progress_callback: Called with (downloaded_bytes, total_bytes, speed_mb_s, percentage).
            cancel_event: threading.Event to signal abort.
            
        Returns:
            Path: Absolute path to the completed .gguf file.
        """
        if model_id in GGUF_CATALOG:
            item = GGUF_CATALOG[model_id]
            url = item.url
            filename = item.filename
        else:
            url = model_id
            filename = os.path.basename(model_id.split("?")[0]) or "model.gguf"

        dest_file = cls.get_model_path(filename)
        if cls.is_model_downloaded(filename):
            # Already downloaded
            if progress_callback:
                size = dest_file.stat().st_size
                progress_callback(size, size, 0.0, 100.0)
            return dest_file

        part_file = dest_file.with_suffix(".part")

        # Clean prior interrupted partial download if any
        if part_file.exists():
            try:
                part_file.unlink()
            except Exception:
                pass

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "NoMoreClutter-ModelDownloader/1.0"
            }
        )

        chunk_size = 128 * 1024  # 128KB chunks for smooth progress updates
        start_time = time.time()
        downloaded_bytes = 0

        try:
            with urllib.request.urlopen(req, timeout=30) as response, open(part_file, "wb") as out_file:
                total_bytes = int(response.headers.get("content-length", 0))

                while True:
                    if cancel_event and cancel_event.is_set():
                        raise InterruptedError("Download was cancelled by user.")

                    chunk = response.read(chunk_size)
                    if not chunk:
                        break

                    out_file.write(chunk)
                    downloaded_bytes += len(chunk)

                    now = time.time()
                    elapsed = max(0.001, now - start_time)
                    speed_mb_s = (downloaded_bytes / (1024 * 1024)) / elapsed
                    percentage = (downloaded_bytes / total_bytes * 100.0) if total_bytes > 0 else 0.0

                    if progress_callback:
                        progress_callback(downloaded_bytes, total_bytes, speed_mb_s, percentage)

            # Atomic rename from .part to final .gguf
            if part_file.exists():
                part_file.replace(dest_file)

            return dest_file

        except Exception as e:
            # Clean partial download on failure
            if part_file.exists():
                try:
                    part_file.unlink()
                except Exception:
                    pass
            raise e
