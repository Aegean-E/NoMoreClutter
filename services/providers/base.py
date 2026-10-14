"""
Base AI Provider Interface (PRINCIPLE-003: Modularity & Pluggable Architecture)
Defines the standard abstraction for all AI providers (Cloud, Embedded, and Local Server).
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional


class BaseAIProvider(ABC):
    """Abstract base class for all AI model providers."""

    def __init__(self, base_url: str, api_key: str = "not-needed", **kwargs):
        self.base_url = base_url.strip() if base_url else ""
        self.api_key = api_key.strip() if api_key else "not-needed"
        self.extra_config = kwargs

    @abstractmethod
    def test_connection(self, model: Optional[str] = None) -> Tuple[bool, str]:
        """Test if the AI endpoint is accessible and responsive.
        
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        pass

    @abstractmethod
    def complete(self, prompt: str, model: str, temperature: float = 0.2, max_tokens: int = 1500) -> str:
        """Execute a text completion request.
        
        Returns:
            str: Raw response text from the model.
        """
        pass

    @abstractmethod
    def analyze_image(self, image_path: str, prompt: str, model: str, max_tokens: int = 100) -> str:
        """Execute a vision model analysis on a local image.
        
        Returns:
            str: Raw response text from the model.
        """
        pass
