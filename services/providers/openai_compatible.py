"""
OpenAI-Compatible AI Provider Implementation (PRINCIPLE-003, PRINCIPLE-007, PRINCIPLE-009)
Unifies cloud APIs (Groq, Gemini, OpenAI, OpenRouter) and local servers (LM Studio, Ollama).
"""

import base64
import os
from typing import Tuple, Optional
from .base import BaseAIProvider


class OpenAICompatibleProvider(BaseAIProvider):
    """Universal provider for all endpoints following the OpenAI API standard."""

    def __init__(self, base_url: str, api_key: str = "not-needed", timeout_sec: float = 45.0, **kwargs):
        super().__init__(base_url=base_url, api_key=api_key, **kwargs)
        self.timeout_sec = timeout_sec
        self._client = None

    def _get_client(self):
        """Lazy load OpenAI client for fast application startup."""
        if self._client is None:
            from openai import OpenAI
            key = self.api_key if self.api_key and self.api_key != "not-needed" else "not-needed"
            self._client = OpenAI(
                base_url=self.base_url,
                api_key=key,
                timeout=self.timeout_sec,
            )
        return self._client

    def test_connection(self, model: Optional[str] = None) -> Tuple[bool, str]:
        """Verify API accessibility and credentials."""
        try:
            client = self._get_client()
            target_model = model.strip() if model else "test"
            response = client.chat.completions.create(
                model=target_model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            )
            reply = response.choices[0].message.content or "Connected"
            return True, f"Successfully connected to {target_model}!"
        except Exception as e:
            err = str(e)
            if "Connection refused" in err or "1234" in err:
                return False, "Local server is not running on port 1234 (start LM Studio server)."
            if "11434" in err:
                return False, "Ollama is not running on port 11434 (run `ollama serve`)."
            if "401" in err or "Incorrect API key" in err:
                return False, "Invalid API key. Please check your key in Settings."
            if "404" in err:
                return False, f"Model '{model}' not found or URL path invalid."
            return False, f"Connection failed: {err}"

    def complete(self, prompt: str, model: str, temperature: float = 0.2, max_tokens: int = 1500) -> str:
        """Execute text completion and extract output text cleanly."""
        client = self._get_client()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        return content.strip()

    def analyze_image(self, image_path: str, prompt: str, model: str, max_tokens: int = 150) -> str:
        """Perform vision inference on a single image file."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        mime_type = self._get_mime_type(image_path)
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")

        client = self._get_client()
        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{encoded}"}
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }]

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=max_tokens,
        )
        return (response.choices[0].message.content or "").strip()

    @staticmethod
    def _get_mime_type(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
            ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
            ".svg": "image/svg+xml", ".ico": "image/x-icon", ".tiff": "image/tiff"
        }
        return mime_types.get(ext, "image/jpeg")
