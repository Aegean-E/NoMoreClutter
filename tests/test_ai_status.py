"""
Unit tests for AI Status Indicator & Health Checks (PRINCIPLE-007, PRINCIPLE-008, PRINCIPLE-011).
Tests plugged/unplugged evaluation across cloud zero-install, embedded GGUF, Ollama, and local servers.
"""

import unittest
from unittest.mock import patch, MagicMock
from services.llm_service import LLMService


class TestAIStatus(unittest.TestCase):
    def test_cloud_missing_api_key(self):
        """Cloud providers requiring API keys should be reported unplugged without network calls."""
        is_plugged, badge, detail = LLMService.check_ai_status(
            provider_name="Groq (Free & Fastest - Zero Install)",
            api_key="",
        )
        self.assertFalse(is_plugged)
        self.assertIn("No Key", badge)
        self.assertIn("API key is missing", detail)

    def test_gemini_missing_api_key(self):
        """Google Gemini with empty key should be flagged as unplugged."""
        is_plugged, badge, detail = LLMService.check_ai_status(
            provider_name="Google Gemini (Free Tier - Zero Install)",
            api_key="   ",
        )
        self.assertFalse(is_plugged)
        self.assertIn("No Key", badge)

    @patch("services.llm_service.LLMService.test_connection")
    def test_cloud_valid_connection(self, mock_test):
        """Successful connection test should result in plugged status."""
        mock_test.return_value = (True, "Connected to llama-3.3-70b-versatile")
        is_plugged, badge, detail = LLMService.check_ai_status(
            provider_name="Groq (Free & Fastest - Zero Install)",
            api_key="gsk_valid_test_key",
        )
        self.assertTrue(is_plugged)
        self.assertIn("Ready", badge)
        self.assertIn("Successfully connected", detail)

    @patch("services.llm_service.LLMService.test_connection")
    def test_cloud_invalid_key_error(self, mock_test):
        """Invalid API key response should flag provider as unplugged with clear badge."""
        mock_test.return_value = (False, "401 Invalid API key provided.")
        is_plugged, badge, detail = LLMService.check_ai_status(
            provider_name="Groq (Free & Fastest - Zero Install)",
            api_key="gsk_invalid_test_key",
        )
        self.assertFalse(is_plugged)
        self.assertIn("Invalid Key", badge)

    @patch("services.model_downloader.ModelDownloader.is_model_downloaded")
    def test_embedded_not_downloaded(self, mock_is_dl):
        """Embedded provider without downloaded weights should be flagged as unplugged."""
        mock_is_dl.return_value = False
        is_plugged, badge, detail = LLMService.check_ai_status(
            provider_name="Built-In Embedded AI (100% Offline GGUF)",
            model="qwen2.5-1.5b-instruct-q4_k_m.gguf",
        )
        self.assertFalse(is_plugged)
        self.assertIn("No Model", badge)
        self.assertIn("not downloaded yet", detail)

    @patch("services.model_downloader.ModelDownloader.is_model_downloaded")
    def test_embedded_downloaded_and_ready(self, mock_is_dl):
        """Embedded provider with downloaded weights should be flagged as plugged & ready."""
        mock_is_dl.return_value = True
        is_plugged, badge, detail = LLMService.check_ai_status(
            provider_name="Built-In Embedded AI (100% Offline GGUF)",
            model="qwen2.5-1.5b-instruct-q4_k_m.gguf",
        )
        self.assertTrue(is_plugged)
        self.assertIn("Embedded", badge)
        self.assertIn("ready for 100% offline", detail)

    @patch("services.ollama_manager.OllamaManager.check_status")
    def test_ollama_offline(self, mock_status):
        """Ollama server offline should be flagged as unplugged."""
        mock_status.return_value = (False, "Ollama daemon unreachable on port 11434")
        is_plugged, badge, detail = LLMService.check_ai_status(
            provider_name="Ollama (Local Server)",
            base_url="http://localhost:11434/v1",
        )
        self.assertFalse(is_plugged)
        self.assertIn("Ollama Offline", badge)
        self.assertIn("not running", detail)

    @patch("services.ollama_manager.OllamaManager.list_installed_models")
    @patch("services.ollama_manager.OllamaManager.check_status")
    def test_ollama_online(self, mock_status, mock_list):
        """Ollama server running should be flagged as plugged."""
        mock_status.return_value = (True, "Ollama running")
        mock_list.return_value = ["llama3.2:1b", "qwen2.5:1.5b"]
        is_plugged, badge, detail = LLMService.check_ai_status(
            provider_name="Ollama (Local Server)",
            base_url="http://localhost:11434/v1",
            model="llama3.2:1b",
        )
        self.assertTrue(is_plugged)
        self.assertIn("Ollama", badge)
        self.assertIn("running", detail)

    @patch("services.llm_service.LLMService.test_connection")
    def test_local_server_offline(self, mock_test):
        """LM Studio server not responding should be flagged as server offline."""
        mock_test.return_value = (False, "Connection refused on port 1234")
        is_plugged, badge, detail = LLMService.check_ai_status(
            provider_name="LM Studio (Local Server)",
            base_url="http://localhost:1234/v1",
        )
        self.assertFalse(is_plugged)
        self.assertIn("Offline", badge)


if __name__ == "__main__":
    unittest.main()
