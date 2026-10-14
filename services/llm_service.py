"""
LLM Service Facade (PRINCIPLE-001, PRINCIPLE-003, PRINCIPLE-009)
Adapts the pluggable AI provider and RLM Organizer for backward compatibility and clean orchestration.
"""

import os
from typing import List, Optional, Tuple
from models import FileChange
from .providers import get_provider
from .rlm_organizer import RLMOrganizer, RLMOrganizerError


class LLMError(Exception):
    """Legacy exception class maintained for backward compatibility."""
    pass


class LLMService:
    """Unified service facade interfacing with Pluggable AI Providers and RLM Engine."""

    def __init__(self, base_url: str = "http://localhost:1234/v1", api_key: str = "not-needed", provider_id: str = "custom", **kwargs):
        self.base_url = base_url
        self.api_key = api_key
        
        # Auto-detect embedded provider if base_url is local://embedded
        if provider_id == "custom" and (base_url == "local://embedded" or "embedded" in str(base_url).lower()):
            provider_id = "embedded"
            
        self.provider_id = provider_id
        
        self.provider = get_provider(
            provider_id=self.provider_id,
            base_url=self.base_url,
            api_key=self.api_key,
            **kwargs
        )
        self.organizer = RLMOrganizer(provider=self.provider)

    def test_connection(self, model: Optional[str] = None) -> Tuple[bool, str]:
        """Test if the configured AI endpoint and model are reachable."""
        return self.provider.test_connection(model=model)

    @classmethod
    def check_ai_status(
        cls,
        provider_name: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Tuple[bool, str, str]:
        """
        Evaluate whether the selected AI provider is plugged in (ready/connected) or unplugged.

        Returns:
            Tuple[bool, str, str]: (is_plugged, badge_label, detailed_description)
        """
        from .providers.registry import get_preset_by_name
        from .model_downloader import ModelDownloader
        from .ollama_manager import OllamaManager

        # 1. Resolve preset by name or fallback
        preset = get_preset_by_name(provider_name) if provider_name else None

        if preset:
            provider_id = preset.id
            name_map = {
                "groq": "Groq",
                "gemini": "Gemini",
                "openai": "OpenAI",
                "openrouter": "OpenRouter",
                "embedded": "Embedded",
                "ollama": "Ollama",
                "lmstudio": "LM Studio",
                "custom": "Custom AI",
            }
            display_name = name_map.get(preset.id, preset.id.title())
        else:
            p_lower = (provider_name or "").lower()
            u_lower = (base_url or "").lower()
            if "embedded" in p_lower or "embedded" in u_lower:
                provider_id = "embedded"
                display_name = "Embedded"
            elif "ollama" in p_lower or "11434" in u_lower:
                provider_id = "ollama"
                display_name = "Ollama"
            elif "groq" in p_lower:
                provider_id = "groq"
                display_name = "Groq"
            elif "gemini" in p_lower:
                provider_id = "gemini"
                display_name = "Gemini"
            else:
                provider_id = "custom"
                display_name = "Custom AI"

        effective_base_url = (base_url or (preset.base_url if preset else "")).strip()
        effective_key = (api_key if api_key is not None else "").strip()
        effective_model = (model or (preset.default_model if preset else "")).strip()

        # 2. Check: Cloud API key requirement (zero network latency)
        if preset and preset.requires_api_key and not effective_key:
            return (
                False,
                f"{display_name}: No Key",
                f"API key is missing for {preset.name}. Please enter your key in Settings or click '1-Click AI Deploy' to get a free key."
            )

        # 3. Check: Embedded local model (zero network latency)
        if provider_id == "embedded" or effective_base_url == "local://embedded":
            target_model = effective_model or (preset.default_model if preset else "qwen2.5-1.5b-instruct-q4_k_m.gguf")
            if ModelDownloader.is_model_downloaded(target_model):
                model_stem = target_model.split(".")[0].replace("-instruct", "").replace("-q4_k_m", "")
                return (
                    True,
                    f"Embedded: {model_stem}",
                    f"Embedded model '{target_model}' is downloaded and ready for 100% offline organization."
                )
            else:
                return (
                    False,
                    "Embedded: No Model",
                    f"Embedded model '{target_model}' is not downloaded yet. Click '1-Click AI Deploy' to download offline weights."
                )

        # 4. Check: Ollama server
        if provider_id == "ollama" or "11434" in effective_base_url:
            is_running, msg = OllamaManager.check_status(base_url=effective_base_url or "http://localhost:11434")
            if not is_running:
                return (
                    False,
                    "Ollama Offline",
                    f"Ollama daemon is not running on {effective_base_url or 'http://localhost:11434'}. Start with `ollama serve`."
                )
            installed = OllamaManager.list_installed_models(base_url=effective_base_url or "http://localhost:11434")
            tag_name = effective_model.split(":")[0] if effective_model else "Online"
            return (
                True,
                f"Ollama: {tag_name}",
                f"Ollama is running on {effective_base_url} ({len(installed)} models installed)."
            )

        # 5. Check: Cloud endpoint or LM Studio / custom server with key or URL
        try:
            service = cls(
                base_url=effective_base_url or (preset.base_url if preset else "http://localhost:1234/v1"),
                api_key=effective_key or "not-needed",
                provider_id=provider_id,
            )
            success, msg = service.test_connection(model=effective_model or (preset.default_model if preset else None))
            if success:
                return (
                    True,
                    f"{display_name} Ready",
                    f"Successfully connected to {display_name} ({effective_model or 'default'}): {msg}"
                )
            else:
                short_err = "Offline"
                if "401" in msg or "Invalid API key" in msg or "Incorrect API key" in msg:
                    short_err = "Invalid Key"
                elif "1234" in msg or "Connection refused" in msg:
                    short_err = "Server Offline"
                elif "404" in msg:
                    short_err = "Model Missing"
                return (
                    False,
                    f"{display_name}: {short_err}",
                    f"Connection failed for {display_name}: {msg}"
                )
        except Exception as e:
            return (
                False,
                f"{display_name}: Offline",
                f"Connection error for {display_name}: {str(e)}"
            )

    def analyze_files(
        self,
        files: List[str],
        model: str,
        create_new_folders: bool = True,
        existing_folders: Optional[List[str]] = None,
        analyze_images: bool = False,
        numbered_rename: bool = False,
        ai_rename: bool = True,
        content_peeking: bool = True,
        target_folder: str = "",
        output_folder: str = "",
        progress_callback=None,
    ) -> List[FileChange]:
        """Analyze and organize files using the RLM hierarchical engine."""
        dest = output_folder or target_folder
        if not dest and files:
            dest = os.path.dirname(files[0])

        try:
            return self.organizer.organize(
                files=files,
                model=model,
                output_folder=dest,
                existing_folders=existing_folders or [],
                create_new_folders=create_new_folders,
                analyze_images=analyze_images,
                ai_rename=ai_rename,
                numbered_rename=numbered_rename,
                content_peeking=content_peeking,
                progress_callback=progress_callback,
            )
        except Exception as e:
            raise LLMError(str(e)) from e
