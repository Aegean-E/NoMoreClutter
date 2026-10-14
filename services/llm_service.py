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
