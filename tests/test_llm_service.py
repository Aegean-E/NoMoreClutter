"""
Unit tests for LLMService Facade (PRINCIPLE-011).
Tests initialization, error encapsulation, and integration with RLM organizer.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from services.llm_service import LLMService, LLMError
from models import FileChange


class TestLLMService(unittest.TestCase):
    def setUp(self):
        self.service = LLMService(
            base_url="http://mock-api.local/v1",
            api_key="mock-key",
            provider_id="mock"
        )

    def test_initialization(self):
        """Service should initialize with expected provider and organizer."""
        self.assertEqual(self.service.base_url, "http://mock-api.local/v1")
        self.assertEqual(self.service.api_key, "mock-key")
        self.assertEqual(self.service.provider_id, "mock")
        self.assertIsNotNone(self.service.provider)
        self.assertIsNotNone(self.service.organizer)

    @patch("services.providers.openai_compatible.OpenAICompatibleProvider.test_connection")
    def test_test_connection_delegation(self, mock_test):
        """test_connection should delegate to the underlying provider."""
        mock_test.return_value = (True, "Connection successful")
        success, msg = self.service.test_connection(model="test-model")
        self.assertTrue(success)
        self.assertEqual(msg, "Connection successful")
        mock_test.assert_called_once_with(model="test-model")

    def test_analyze_files_empty(self):
        """Analyzing an empty file list should return an empty list without error."""
        result = self.service.analyze_files(
            files=[],
            model="test-model"
        )
        self.assertEqual(result, [])

    def test_analyze_files_error_wrapping(self):
        """Underlying exceptions should be wrapped as LLMError."""
        with patch.object(self.service.organizer, "organize", side_effect=ValueError("Test crash")):
            with self.assertRaises(LLMError) as ctx:
                self.service.analyze_files(
                    files=["dummy/file.txt"],
                    model="test-model"
                )
            self.assertIn("Test crash", str(ctx.exception))

    def test_analyze_files_destination_resolution(self):
        """If output_folder is empty, destination should default to the first file's parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "photo.jpg")
            with open(file_path, "w") as f:
                f.write("content")

            # Mock organizer.organize to inspect the output_folder parameter
            with patch.object(self.service.organizer, "organize") as mock_org:
                mock_org.return_value = [
                    FileChange(
                        original=file_path,
                        action="move",
                        new_path=os.path.join(tmpdir, "Images", "photo.jpg"),
                        file_type="Images"
                    )
                ]

                results = self.service.analyze_files(
                    files=[file_path],
                    model="test-model",
                    target_folder=""
                )
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].file_type, "Images")
                # Verify that output_folder passed to organize was tmpdir
                _, kwargs = mock_org.call_args
                self.assertEqual(kwargs["output_folder"], tmpdir)


if __name__ == "__main__":
    unittest.main()
