"""
Embedded Local AI Provider (PRINCIPLE-003: Modularity, PRINCIPLE-008: Zero-Friction)
Runs 100% offline in-process using downloaded GGUF weights via llama-cpp-python.
"""

import os
from pathlib import Path
from typing import Tuple, Optional
from .base import BaseAIProvider
from ..model_downloader import ModelDownloader, GGUF_CATALOG
from ..llama_server_manager import LlamaServerManager, is_server_installed


class EmbeddedProvider(BaseAIProvider):
    """Provider running local quantized GGUF models directly within the application."""

    def __init__(self, model_filename: str = "qwen2.5-1.5b-instruct-q4_k_m.gguf", **kwargs):
        super().__init__(base_url="local://embedded", api_key="not-needed", **kwargs)
        self.model_filename = model_filename
        self._llm_instance = None
        self._loaded_model_path = None

    @property
    def has_vision(self) -> bool:
        """Return True if the configured model is a multimodal vision model."""
        target = (self.model_filename or "").strip()
        if target in GGUF_CATALOG:
            return GGUF_CATALOG[target].has_vision
        for item in GGUF_CATALOG.values():
            if item.filename == target:
                return item.has_vision
        lower = target.lower()
        return "vision" in lower or "moondream" in lower or "llava" in lower

    def _get_model_path(self, model: Optional[str] = None) -> Path:
        """Resolve model filename to local path."""
        target_name = (model or self.model_filename).strip()
        # Check if target_name is a catalog ID (e.g. 'qwen2.5-1.5b')
        if target_name in GGUF_CATALOG:
            target_name = GGUF_CATALOG[target_name].filename
        return ModelDownloader.get_model_path(target_name)

    def _get_llm(self, model: Optional[str] = None):
        """Lazy load in-process Llama instance when llama-cpp-python is used."""
        model_path = self._get_model_path(model)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model weights not found at {model_path}. "
                "Use '1-Click Quick Deploy' in NoMoreClutter to download the model first."
            )

        if self._llm_instance is None or self._loaded_model_path != str(model_path):
            try:
                from llama_cpp import Llama
            except ImportError:
                raise RuntimeError(
                    "Local engine not available. Please click '1-Click Quick Deploy' "
                    "in NoMoreClutter to download the official standalone engine (zero Python dependencies)."
                )

            self._llm_instance = Llama(
                model_path=str(model_path),
                n_ctx=2048,
                n_threads=min(4, os.cpu_count() or 2),
                verbose=False,
            )
            self._loaded_model_path = str(model_path)

        return self._llm_instance

    def test_connection(self, model: Optional[str] = None) -> Tuple[bool, str]:
        """Test if the local model is downloaded and inference engine is ready."""
        model_path = self._get_model_path(model)
        if not model_path.exists():
            return False, f"Model file '{model_path.name}' is not downloaded yet. Click '1-Click Quick Deploy'."

        size_mb = model_path.stat().st_size / (1024 * 1024)
        if size_mb < 10:
            return False, f"Model file '{model_path.name}' appears corrupt or incomplete ({size_mb:.1f} MB)."

        # Check vision projector if this model requires one
        mmproj_path = ModelDownloader.get_mmproj_path(model_path.name)
        if mmproj_path and not mmproj_path.exists():
            return False, f"Vision projector '{mmproj_path.name}' is missing. Re-download via '1-Click Quick Deploy'."

        badge = "[Vision Supported]" if self.has_vision else "[Text-Only]"
        if is_server_installed():
            return True, f"Embedded local engine ready (Official llama-server)! Model: {model_path.name} {badge} ({size_mb:.0f} MB)"

        try:
            import llama_cpp
            return True, f"Embedded engine ready (in-process)! Model: {model_path.name} {badge} ({size_mb:.0f} MB)"
        except ImportError:
            return False, f"Model weights ready {badge} ({size_mb:.0f} MB). Standalone engine missing. Click '1-Click Quick Deploy' to download official engine."

    def complete(self, prompt: str, model: str, temperature: float = 0.2, max_tokens: int = 1500) -> str:
        """Run text completion using the standalone llama-server or fallback in-process model."""
        model_path = self._get_model_path(model)
        if is_server_installed():
            return LlamaServerManager.complete(
                prompt=prompt,
                model_path=model_path,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        llm = self._get_llm(model)
        output = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "You are a fast, structured JSON-only file organizer."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = output["choices"][0]["message"]["content"] or ""
        return content.strip()

    def analyze_image(self, image_path: str, prompt: str, model: str, max_tokens: int = 100) -> str:
        """Analyze an image using the local multimodal vision model."""
        if not self.has_vision:
            raise NotImplementedError(
                f"Model '{self.model_filename}' is a text-focused model without vision capabilities. "
                "Download Moondream 2 via '1-Click Quick Deploy' or use Groq / Gemini for vision."
            )

        model_path = self._get_model_path(model)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Vision model weights not found at {model_path}. "
                "Use '1-Click Quick Deploy' in NoMoreClutter to download the model first."
            )

        mmproj_path = ModelDownloader.get_mmproj_path(model_path.name)
        if mmproj_path and not mmproj_path.exists():
            raise FileNotFoundError(
                f"Vision projector weights not found at {mmproj_path}. "
                "Re-download via '1-Click Quick Deploy'."
            )

        # 1. Primary engine: High-speed standalone official llama-server (zero Python C++ dependencies)
        if is_server_installed() and mmproj_path and mmproj_path.exists():
            return LlamaServerManager.analyze_image(
                image_path=image_path,
                prompt=prompt,
                model_path=model_path,
                mmproj_path=mmproj_path,
                max_tokens=max_tokens,
            )

        # 2. Secondary fallback: in-process llama_cpp if installed
        try:
            import base64
            from llama_cpp import Llama
            from llama_cpp.llama_chat_format import MoondreamChatHandler, Llava15ChatHandler
        except ImportError as e:
            raise NotImplementedError(
                "Local vision engine is not installed. Click '1-Click Quick Deploy' in NoMoreClutter "
                "to download the official standalone engine (zero Python dependencies) or use Groq / Gemini."
            ) from e

        with open(image_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode("utf-8")
        data_uri = f"data:image/jpeg;base64,{b64_img}"

        chat_handler = None
        if mmproj_path and mmproj_path.exists():
            try:
                chat_handler = MoondreamChatHandler(clip_model_path=str(mmproj_path))
            except Exception:
                chat_handler = Llava15ChatHandler(clip_model_path=str(mmproj_path))

        llm = Llama(
            model_path=str(model_path),
            chat_handler=chat_handler,
            n_ctx=2048,
            n_threads=min(4, os.cpu_count() or 2),
            verbose=False,
        )

        response = llm.create_chat_completion(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_uri}}
                    ]
                }
            ],
            max_tokens=max_tokens,
        )
        return response["choices"][0]["message"]["content"] or ""
