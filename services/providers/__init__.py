"""
Services Provider Module (PRINCIPLE-003: Modularity)
"""

from .base import BaseAIProvider
from .openai_compatible import OpenAICompatibleProvider
from .embedded import EmbeddedProvider
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
    if preset.id == "embedded" or provider_id == "embedded":
        model_name = kwargs.get("model", preset.default_model)
        return EmbeddedProvider(model_filename=model_name, **kwargs)

    url = base_url if base_url else preset.base_url
    key = api_key if api_key else ("not-needed" if not preset.requires_api_key else "")
    return OpenAICompatibleProvider(base_url=url, api_key=key, **kwargs)


__all__ = [
    "BaseAIProvider",
    "OpenAICompatibleProvider",
    "EmbeddedProvider",
    "ProviderPreset",
    "PROVIDER_PRESETS",
    "get_preset",
    "get_preset_by_name",
    "list_provider_names",
    "get_provider",
]
