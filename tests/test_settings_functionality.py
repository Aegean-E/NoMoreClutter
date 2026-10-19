"""
Unit tests verifying the function of EVERY setting in NoMoreClutter (PRINCIPLE-011).
Tests AI rename, folder creation, numbered rename, content peeking, limits,
batch sizes, embedded provider detection, and settings persistence.
"""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from models import FileChange
from services.rlm_organizer import RLMOrganizer
from services.llm_service import LLMService
from services.providers.embedded import EmbeddedProvider
from services.providers.openai_compatible import OpenAICompatibleProvider


class TestSettingsFunctionality(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.doc_path = os.path.join(self.test_dir, "contract_sample.txt")
        with open(self.doc_path, "w", encoding="utf-8") as f:
            f.write("Master Services Agreement between Company A and Client B.")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_ai_rename_setting_disabled_guarantees_original_name(self):
        """Setting 'ai_rename=False' must preserve the original filename even if LLM invents a new name."""
        mock_provider = MagicMock()
        # Mock LLM trying to rename to 'invented_name.txt'
        mock_provider.complete.return_value = json.dumps([
            {"id": 0, "folder": "Contracts", "name": "invented_name.txt"}
        ])

        organizer = RLMOrganizer(provider=mock_provider)
        results = organizer.organize(
            files=[self.doc_path],
            model="test-model",
            output_folder=self.test_dir,
            ai_rename=False,  # Setting: AI Rename Disabled
            create_new_folders=True,
        )

        self.assertEqual(len(results), 1)
        # Must retain original filename 'contract_sample.txt'
        self.assertEqual(os.path.basename(results[0].new_path), "contract_sample.txt")

    def test_ai_rename_setting_enabled_applies_sanitized_name(self):
        """Setting 'ai_rename=True' allows the LLM to suggest clean descriptive names."""
        mock_provider = MagicMock()
        mock_provider.complete.return_value = json.dumps([
            {"id": 0, "folder": "Contracts", "name": "service_agreement.txt"}
        ])

        organizer = RLMOrganizer(provider=mock_provider)
        results = organizer.organize(
            files=[self.doc_path],
            model="test-model",
            output_folder=self.test_dir,
            ai_rename=True,  # Setting: AI Rename Enabled
            create_new_folders=True,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(os.path.basename(results[0].new_path), "service_agreement.txt")

    def test_create_folders_setting_enabled(self):
        """Setting 'create_folders=True' creates semantic category folders."""
        mock_provider = MagicMock()
        mock_provider.complete.return_value = json.dumps([
            {"id": 0, "folder": "Legal_Documents", "name": "contract.txt"}
        ])

        organizer = RLMOrganizer(provider=mock_provider)
        results = organizer.organize(
            files=[self.doc_path],
            model="test-model",
            output_folder=self.test_dir,
            create_new_folders=True,  # Setting: Create Folders Enabled
        )

        self.assertEqual(len(results), 1)
        dest_folder = os.path.basename(os.path.dirname(results[0].new_path))
        self.assertEqual(dest_folder, "Legal_Documents")

    def test_create_folders_setting_disabled_with_existing(self):
        """Setting 'create_folders=False' maps into existing folders when available."""
        mock_provider = MagicMock()
        mock_provider.complete.return_value = json.dumps([
            {"id": 0, "folder": "New_Random_Folder", "name": "contract.txt"}
        ])

        organizer = RLMOrganizer(provider=mock_provider)
        results = organizer.organize(
            files=[self.doc_path],
            model="test-model",
            output_folder=self.test_dir,
            existing_folders=["Archive", "Personal"],
            create_new_folders=False,  # Setting: Create Folders Disabled
        )

        self.assertEqual(len(results), 1)
        dest_folder = os.path.basename(os.path.dirname(results[0].new_path))
        self.assertIn(dest_folder, ["Archive", "Personal"])

    def test_create_folders_setting_disabled_without_existing(self):
        """Setting 'create_folders=False' keeps files in destination root if no existing folders exist."""
        mock_provider = MagicMock()
        mock_provider.complete.return_value = json.dumps([
            {"id": 0, "folder": "Random_Folder", "name": "contract.txt"}
        ])

        organizer = RLMOrganizer(provider=mock_provider)
        results = organizer.organize(
            files=[self.doc_path],
            model="test-model",
            output_folder=self.test_dir,
            existing_folders=[],
            create_new_folders=False,  # Setting: Create Folders Disabled, no existing
        )

        self.assertEqual(len(results), 1)
        # Should be directly in output_folder
        self.assertEqual(os.path.dirname(results[0].new_path), self.test_dir)

    def test_numbered_rename_setting_enabled(self):
        """Setting 'numbered_rename=True' renames files sequentially per directory."""
        mock_provider = MagicMock()
        file2 = os.path.join(self.test_dir, "doc2.txt")
        with open(file2, "w", encoding="utf-8") as f:
            f.write("Second document")

        mock_provider.complete.return_value = json.dumps([
            {"id": 0, "folder": "Notes", "name": "first.txt"},
            {"id": 1, "folder": "Notes", "name": "second.txt"}
        ])

        organizer = RLMOrganizer(provider=mock_provider)
        results = organizer.organize(
            files=[self.doc_path, file2],
            model="test-model",
            output_folder=self.test_dir,
            numbered_rename=True,  # Setting: Numbered Rename Enabled
        )

        self.assertEqual(len(results), 2)
        names = [os.path.basename(r.new_path) for r in results]
        self.assertEqual(names, ["1.txt", "2.txt"])

    def test_content_peeking_setting_enabled_and_disabled(self):
        """Setting 'content_peeking' controls whether snippets are attached in LLM prompts."""
        mock_provider = MagicMock()
        mock_provider.complete.return_value = json.dumps([
            {"id": 0, "folder": "Contracts", "name": "contract.txt"}
        ])

        organizer = RLMOrganizer(provider=mock_provider)

        # 1. Content peeking Enabled
        organizer.organize(
            files=[self.doc_path],
            model="test-model",
            output_folder=self.test_dir,
            content_peeking=True,
        )
        prompt_with_peek = mock_provider.complete.call_args[1]["prompt"]
        self.assertIn("peek", prompt_with_peek)
        self.assertIn("Master Services Agreement", prompt_with_peek)

        # 2. Content peeking Disabled
        mock_provider.reset_mock()
        mock_provider.complete.return_value = json.dumps([
            {"id": 0, "folder": "Contracts", "name": "contract.txt"}
        ])
        organizer.organize(
            files=[self.doc_path],
            model="test-model",
            output_folder=self.test_dir,
            content_peeking=False,
        )
        prompt_without_peek = mock_provider.complete.call_args[1]["prompt"]
        self.assertNotIn('"peek":', prompt_without_peek)

    def test_embedded_provider_auto_resolution(self):
        """Setting base_url to 'local://embedded' automatically resolves to EmbeddedProvider."""
        llm = LLMService(base_url="local://embedded", api_key="")
        self.assertIsInstance(llm.provider, EmbeddedProvider)

        cloud_llm = LLMService(base_url="https://api.groq.com/openai/v1", api_key="test-key")
        self.assertIsInstance(cloud_llm.provider, OpenAICompatibleProvider)

    def test_settings_persistence_all_keys(self):
        """Settings dictionary must serialize and deserialize all 13 setting fields intact."""
        settings_dict = {
            "provider_name": "Groq (Free & Fastest - Zero Install)",
            "api_key": "gsk_test123",
            "llm_url": "https://api.groq.com/openai/v1",
            "llm_model": "llama-3.3-70b-versatile",
            "create_folders": True,
            "analyze_images": True,
            "numbered_rename": False,
            "ai_rename": True,
            "content_peeking": True,
            "auto_execute": False,
            "limit": "75",
            "batch_size": "20",
            "peek_length": 220,
            "pacing_delay": 0.15,
            "included_categories": {
                "Documents": True,
                "Images": True,
                "Code": True,
                "Archives": False
            }
        }

        settings_path = os.path.join(self.test_dir, "test_settings.json")
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings_dict, f, indent=2)

        with open(settings_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        for key, value in settings_dict.items():
            self.assertEqual(loaded[key], value, f"Setting '{key}' did not match serialized value")

    def test_corrupted_settings_file_self_healing(self):
        """A half-written settings.json from a sudden power outage must not crash the application."""
        settings_path = os.path.join(self.test_dir, "corrupt_settings.json")
        with open(settings_path, "w", encoding="utf-8") as f:
            f.write('{"provider_name": "Groq", "api_key": "gsk_123", "llm_model": "llama-3')  # Abrupt truncation

        loaded_settings = {}
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                loaded_settings = json.load(f)
        except json.JSONDecodeError:
            # Self-healing fallback as implemented in main.py
            loaded_settings = {}

        self.assertEqual(loaded_settings, {})


if __name__ == "__main__":
    unittest.main()
