"""
Unit tests for AI Providers and Registry (PRINCIPLE-003, PRINCIPLE-008)
"""

import unittest
from services.providers import (
    PROVIDER_PRESETS,
    get_preset,
    get_preset_by_name,
    list_provider_names,
    get_provider,
    OpenAICompatibleProvider,
)


class TestProviders(unittest.TestCase):
    def test_presets_exist(self):
        self.assertIn("groq", PROVIDER_PRESETS)
        self.assertIn("gemini", PROVIDER_PRESETS)
        self.assertIn("openai", PROVIDER_PRESETS)
        self.assertIn("lmstudio", PROVIDER_PRESETS)
        self.assertIn("ollama", PROVIDER_PRESETS)

    def test_preset_retrieval(self):
        groq_preset = get_preset("groq")
        self.assertEqual(groq_preset.id, "groq")
        self.assertTrue(groq_preset.requires_api_key)
        self.assertIn("groq.com", groq_preset.base_url)

        lmstudio_preset = get_preset("lmstudio")
        self.assertFalse(lmstudio_preset.requires_api_key)
        self.assertIn("1234", lmstudio_preset.base_url)

    def test_list_provider_names(self):
        names = list_provider_names()
        self.assertIsInstance(names, list)
        self.assertGreaterEqual(len(names), 5)
        self.assertTrue(any("Groq" in n for n in names))
        self.assertTrue(any("LM Studio" in n for n in names))

    def test_get_preset_by_name(self):
        names = list_provider_names()
        preset = get_preset_by_name(names[0])
        self.assertIsNotNone(preset)

    def test_get_provider_factory(self):
        provider = get_provider("groq", api_key="test-key")
        self.assertIsInstance(provider, OpenAICompatibleProvider)
        self.assertEqual(provider.api_key, "test-key")
        self.assertEqual(provider.base_url, "https://api.groq.com/openai/v1")


if __name__ == "__main__":
    unittest.main()
