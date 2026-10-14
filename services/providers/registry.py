"""
AI Provider Registry & Presets (PRINCIPLE-003, PRINCIPLE-008)
Centralized catalog of zero-install cloud providers and local server presets.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ProviderPreset:
    id: str
    name: str
    base_url: str
    default_model: str
    vision_model: str
    requires_api_key: bool
    signup_url: str
    description: str
    recommended_pacing_sec: float = 0.0


PROVIDER_PRESETS: Dict[str, ProviderPreset] = {
    "groq": ProviderPreset(
        id="groq",
        name="Groq (Free & Fastest - Zero Install)",
        base_url="https://api.groq.com/openai/v1",
        default_model="llama-3.3-70b-versatile",
        vision_model="llama-3.2-11b-vision-preview",
        requires_api_key=True,
        signup_url="https://console.groq.com/keys",
        description="Free tier available, ultra-fast (hundreds tokens/sec), vision supported.",
        recommended_pacing_sec=0.2,
    ),
    "embedded": ProviderPreset(
        id="embedded",
        name="Built-In Embedded AI (100% Offline GGUF)",
        base_url="local://embedded",
        default_model="qwen2.5-1.5b-instruct-q4_k_m.gguf",
        vision_model="",
        requires_api_key=False,
        signup_url="",
        description="Runs 100% offline inside the application using embedded GGUF weights without external software.",
        recommended_pacing_sec=0.0,
    ),
    "gemini": ProviderPreset(
        id="gemini",
        name="Google Gemini (Free Tier - Zero Install)",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        default_model="gemini-1.5-flash",
        vision_model="gemini-1.5-flash",
        requires_api_key=True,
        signup_url="https://aistudio.google.com/app/apikey",
        description="Generous free tier from Google, built-in vision and reasoning.",
        recommended_pacing_sec=0.2,
    ),
    "openai": ProviderPreset(
        id="openai",
        name="OpenAI (GPT-4o-mini - Zero Install)",
        base_url="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
        vision_model="gpt-4o-mini",
        requires_api_key=True,
        signup_url="https://platform.openai.com/api-keys",
        description="Fast, reliable multimodal intelligence from OpenAI.",
        recommended_pacing_sec=0.0,
    ),
    "openrouter": ProviderPreset(
        id="openrouter",
        name="OpenRouter (Multi-Model - Zero Install)",
        base_url="https://openrouter.ai/api/v1",
        default_model="meta-llama/llama-3.3-70b-instruct",
        vision_model="meta-llama/llama-3.2-11b-vision-instruct",
        requires_api_key=True,
        signup_url="https://openrouter.ai/keys",
        description="Access hundreds of open-source and commercial models with one key.",
        recommended_pacing_sec=0.2,
    ),
    "lmstudio": ProviderPreset(
        id="lmstudio",
        name="LM Studio (Local Server)",
        base_url="http://localhost:1234/v1",
        default_model="llama3",
        vision_model="qwen2.5-vl-7b",
        requires_api_key=False,
        signup_url="https://lmstudio.ai/",
        description="Runs 100% offline on your own GPU/CPU via LM Studio desktop app.",
        recommended_pacing_sec=2.0,
    ),
    "ollama": ProviderPreset(
        id="ollama",
        name="Ollama (Local Server)",
        base_url="http://localhost:11434/v1",
        default_model="llama3",
        vision_model="llava",
        requires_api_key=False,
        signup_url="https://ollama.ai/",
        description="Local inference server running via `ollama serve` on port 11434.",
        recommended_pacing_sec=1.0,
    ),
    "custom": ProviderPreset(
        id="custom",
        name="Custom OpenAI-Compatible Endpoint",
        base_url="http://localhost:8000/v1",
        default_model="default",
        vision_model="default",
        requires_api_key=False,
        signup_url="",
        description="Connect to any custom self-hosted proxy or OpenAI-compatible endpoint.",
        recommended_pacing_sec=0.5,
    ),
}


def get_preset(provider_id: str) -> ProviderPreset:
    """Retrieve preset by ID or return custom preset."""
    return PROVIDER_PRESETS.get(provider_id, PROVIDER_PRESETS["custom"])


def get_preset_by_name(display_name: str) -> Optional[ProviderPreset]:
    """Find preset by UI display name."""
    for preset in PROVIDER_PRESETS.values():
        if preset.name == display_name:
            return preset
    return None


def list_provider_names() -> List[str]:
    """Return all provider display names for UI dropdowns."""
    return [preset.name for preset in PROVIDER_PRESETS.values()]
