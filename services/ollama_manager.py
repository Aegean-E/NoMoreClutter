"""
Ollama Auto-Manager & Model Deployer (PRINCIPLE-003, PRINCIPLE-008)
Provides 1-click discovery, connection verification, and streaming model pulling
via Ollama's local REST API (http://localhost:11434).
Zero external dependencies (uses standard library urllib and json).
"""

import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Callable


@dataclass
class OllamaRecommendedModel:
    id: str
    name: str
    size_approx: str
    description: str
    has_vision: bool = False
    is_default: bool = False

    @property
    def capability_badge(self) -> str:
        """Return visual badge indicating model capabilities."""
        return "[👁️ Vision Supported]" if self.has_vision else "[📝 Text-Only]"


RECOMMENDED_OLLAMA_MODELS: Dict[str, OllamaRecommendedModel] = {
    "llama3.2:1b": OllamaRecommendedModel(
        id="llama3.2:1b",
        name="LLaMA 3.2 1B (Ultra-Fast)",
        size_approx="~1.3 GB",
        description="Meta's fastest lightweight model. Instant classification, low VRAM footprint.",
        has_vision=False,
        is_default=True,
    ),
    "qwen2.5:1.5b": OllamaRecommendedModel(
        id="qwen2.5:1.5b",
        name="Qwen 2.5 1.5B (High Accuracy)",
        size_approx="~986 MB",
        description="Outstanding instruction following and JSON extraction. Highly recommended.",
        has_vision=False,
        is_default=False,
    ),
    "llama3.2:3b": OllamaRecommendedModel(
        id="llama3.2:3b",
        name="LLaMA 3.2 3B (Balanced)",
        size_approx="~2.0 GB",
        description="Higher reasoning capability while remaining responsive on modern PCs.",
        has_vision=False,
        is_default=False,
    ),
    "moondream:latest": OllamaRecommendedModel(
        id="moondream:latest",
        name="Moondream 2 (Tiny Vision)",
        size_approx="~1.7 GB",
        description="Compact local vision model capable of image tagging and categorization.",
        has_vision=True,
        is_default=False,
    ),
    "llama3.2-vision:latest": OllamaRecommendedModel(
        id="llama3.2-vision:latest",
        name="LLaMA 3.2 Vision 11B (Flagship Multimodal)",
        size_approx="~7.9 GB",
        description="Meta's flagship vision model. High-fidelity scene understanding and OCR.",
        has_vision=True,
        is_default=False,
    ),
}


class OllamaManager:
    """Manages interactions with local Ollama daemon for 1-click model deployment."""

    @staticmethod
    def check_status(base_url: str = "http://localhost:11434") -> Tuple[bool, str]:
        """
        Check if Ollama server is running and reachable.
        
        Returns:
            Tuple[bool, str]: (is_running, status_message)
        """
        url = base_url.rstrip("/") + "/api/tags"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "NoMoreClutter-Ollama/1.0"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status == 200:
                    return True, "Ollama is running on localhost:11434"
                return False, f"Ollama returned HTTP {resp.status}"
        except urllib.error.URLError as e:
            return False, "Ollama is not running (start with `ollama serve` or open Ollama app)."
        except Exception as e:
            return False, f"Could not connect to Ollama: {str(e)}"

    @staticmethod
    def list_installed_models(base_url: str = "http://localhost:11434") -> List[str]:
        """Return list of model tags already installed in Ollama."""
        url = base_url.rstrip("/") + "/api/tags"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "NoMoreClutter-Ollama/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = data.get("models", [])
                return [m.get("name", "") for m in models if m.get("name")]
        except Exception:
            return []

    @classmethod
    def pull_model(
        cls,
        model_name: str,
        base_url: str = "http://localhost:11434",
        progress_callback: Optional[Callable[[str, int, int, float], None]] = None,
        cancel_event=None,
    ) -> bool:
        """
        Pull a model with live streaming progress from Ollama.
        
        Args:
            model_name: e.g. 'llama3.2:1b'
            base_url: Ollama base URL
            progress_callback: Called with (status_text, completed_bytes, total_bytes, percentage)
            cancel_event: threading.Event to signal abort
            
        Returns:
            bool: True if completed successfully, False otherwise
        """
        url = base_url.rstrip("/") + "/api/pull"
        payload = json.dumps({"name": model_name, "stream": True}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "NoMoreClutter-Ollama/1.0"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                for line in resp:
                    if cancel_event and cancel_event.is_set():
                        raise InterruptedError(f"Pulling model {model_name} cancelled by user.")

                    if not line:
                        continue

                    try:
                        chunk = json.loads(line.decode("utf-8"))
                    except Exception:
                        continue

                    status = chunk.get("status", "")
                    total = chunk.get("total", 0)
                    completed = chunk.get("completed", 0)

                    percentage = (completed / total * 100.0) if total > 0 else 0.0

                    if progress_callback:
                        progress_callback(status, completed, total, percentage)

                    if status == "success":
                        return True

            return True

        except Exception as e:
            raise e
