"""
Services Provider Module (PRINCIPLE-003: Modularity)
"""

from .base import BaseAIProvider
from .openai_compatible import OpenAICompatibleProvider
from .registry import (
    ProviderPreset,
    PROVIDER_PRESETS,
    get_preset,
    get_preset_by_name,
    list_provider_names,
)


def get_provider(
    provider_id: str = "custom",
    base_url: str = None,
    api_key: str = None,
    **kwargs
) -> BaseAIProvider:
    """Instantiate and return the appropriate AI provider."""
    preset = get_preset(provider_id)
    url = base_url if base_url else preset.base_url
    key = api_key if api_key else ("not-needed" if not preset.requires_api_key else "")
    return OpenAICompatibleProvider(base_url=url, api_key=key, **kwargs)


__all__ = [
    "BaseAIProvider",
    "OpenAICompatibleProvider",
    "ProviderPreset",
    "PROVIDER_PRESETS",
    "get_preset",
    "get_preset_by_name",
    "list_provider_names",
    "get_provider",
]
