"""
Embedded Local AI Provider (PRINCIPLE-003: Modularity, PRINCIPLE-008: Zero-Friction)
Runs 100% offline in-process using downloaded GGUF weights via llama-cpp-python.
"""

import os
from pathlib import Path
from typing import Tuple, Optional
from .base import BaseAIProvider
from ..model_downloader import ModelDownloader, GGUF_CATALOG


class EmbeddedProvider(BaseAIProvider):
    """Provider running local quantized GGUF models directly within the application."""

    def __init__(self, model_filename: str = "qwen2.5-1.5b-instruct-q4_k_m.gguf", **kwargs):
        super().__init__(base_url="local://embedded", api_key="not-needed", **kwargs)
        self.model_filename = model_filename
        self._llm_instance = None
        self._loaded_model_path = None

    @property
    def has_vision(self) -> bool:
        """Embedded local quantized GGUF models are text-focused and do not support vision."""
        return False

    def _get_model_path(self, model: Optional[str] = None) -> Path:
        """Resolve model filename to local path."""
        target_name = (model or self.model_filename).strip()
        # Check if target_name is a catalog ID (e.g. 'qwen2.5-1.5b')
        if target_name in GGUF_CATALOG:
            target_name = GGUF_CATALOG[target_name].filename
        return ModelDownloader.get_model_path(target_name)

    def _get_llm(self, model: Optional[str] = None):
        """Lazy load Llama instance when first needed."""
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
                    "llama-cpp-python is not installed. To run embedded models in-process, "
                    "run `pip install llama-cpp-python` or use Ollama / Cloud providers."
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

        try:
            import llama_cpp
            return True, f"Embedded engine ready! Model: {model_path.name} ({size_mb:.0f} MB)"
        except ImportError:
            return True, f"Model weights ready ({size_mb:.0f} MB). Note: llama-cpp-python needed for in-process inference."

    def complete(self, prompt: str, model: str, temperature: float = 0.2, max_tokens: int = 1500) -> str:
        """Run text completion using the in-process model."""
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
        """Embedded GGUF text models do not support vision analysis directly."""
        raise NotImplementedError(
            "Embedded GGUF models are text-focused. "
            "For image analysis with vision, please use Groq (llama-3.2-11b-vision) or Google Gemini."
        )
