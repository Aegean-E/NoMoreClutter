"""
Unit tests for 1-Click AI Model Deployment (PRINCIPLE-003, PRINCIPLE-008, PRINCIPLE-011)
Tests ModelDownloader, OllamaManager, and EmbeddedProvider with mock streaming.
"""

import io
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

from services.model_downloader import ModelDownloader, GGUF_CATALOG
from services.ollama_manager import OllamaManager, RECOMMENDED_OLLAMA_MODELS
from services.providers.embedded import EmbeddedProvider
from services.providers import get_preset, get_provider


class TestModelDownloader(unittest.TestCase):
    def test_catalog_integrity(self):
        self.assertIn("qwen2.5-1.5b", GGUF_CATALOG)
        self.assertIn("qwen2.5-0.5b", GGUF_CATALOG)
        self.assertIn("smollm2-1.7b", GGUF_CATALOG)
        self.assertIn("moondream2-vision", GGUF_CATALOG)
        
        default_item = GGUF_CATALOG["qwen2.5-1.5b"]
        self.assertTrue(default_item.is_default)
        self.assertTrue(default_item.url.startswith("https://huggingface.co/"))
        self.assertTrue(default_item.filename.endswith(".gguf"))
        self.assertEqual(default_item.capability_badge, "[📝 Text-Only]")

    def test_vision_catalog_item(self):
        vision_item = GGUF_CATALOG["moondream2-vision"]
        self.assertTrue(vision_item.has_vision)
        self.assertEqual(vision_item.capability_badge, "[👁️ Vision Supported]")
        self.assertEqual(vision_item.mmproj_filename, "moondream2-mmproj-f16.gguf")
        self.assertTrue(vision_item.mmproj_url.startswith("https://huggingface.co/"))
        self.assertEqual(vision_item.total_size_mb, vision_item.size_mb + vision_item.mmproj_size_mb)

    def test_weights_dir(self):
        weights_dir = ModelDownloader.get_weights_dir()
        self.assertTrue(isinstance(weights_dir, Path))
        self.assertTrue(weights_dir.exists())

    def test_is_model_downloaded_nonexistent(self):
        self.assertFalse(ModelDownloader.is_model_downloaded("non_existent_file_9999.gguf"))

    @patch("urllib.request.urlopen")
    def test_download_model_mock_success(self, mock_urlopen):
        # Create a mock HTTP response with 1024 bytes
        fake_content = b"GGUF_MOCK_DATA" * 64
        mock_resp = MagicMock()
        mock_resp.headers = {"content-length": str(len(fake_content))}
        mock_resp.read.side_effect = [fake_content[:256], fake_content[256:], b""]
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        progress_calls = []
        def on_progress(downloaded, total, speed, percent):
            progress_calls.append((downloaded, total, percent))

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(ModelDownloader, "get_weights_dir", return_value=Path(tmpdir)):
                res_path = ModelDownloader.download_model(
                    model_id="qwen2.5-0.5b",
                    progress_callback=on_progress,
                )
                self.assertTrue(res_path.exists())
                self.assertGreater(len(progress_calls), 0)
                self.assertEqual(progress_calls[-1][0], len(fake_content))
                self.assertEqual(progress_calls[-1][2], 100.0)

    @patch("urllib.request.urlopen")
    def test_download_model_cancellation(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.headers = {"content-length": "1000"}
        mock_resp.read.return_value = b"x" * 100
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        cancel_event = threading.Event()
        cancel_event.set()  # Cancel immediately

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(ModelDownloader, "get_weights_dir", return_value=Path(tmpdir)):
                with self.assertRaises(InterruptedError):
                    ModelDownloader.download_model(
                        model_id="qwen2.5-0.5b",
                        cancel_event=cancel_event
                    )


    @patch("urllib.request.urlopen")
    def test_download_multimodal_model_mock_success(self, mock_urlopen):
        fake_content = b"GGUF_MOCK_DATA" * 64
        mock_resp = MagicMock()
        mock_resp.headers = {"content-length": str(len(fake_content))}
        mock_resp.read.side_effect = [fake_content[:256], fake_content[256:], b"", fake_content[:256], fake_content[256:], b""]
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        progress_calls = []
        def on_progress(downloaded, total, speed, percent):
            progress_calls.append((downloaded, total, percent))

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(ModelDownloader, "get_weights_dir", return_value=Path(tmpdir)):
                res_path = ModelDownloader.download_model(
                    model_id="moondream2-vision",
                    progress_callback=on_progress,
                )
                self.assertTrue(res_path.exists())
                mmproj_path = ModelDownloader.get_mmproj_path(res_path.name)
                self.assertIsNotNone(mmproj_path)
                self.assertTrue(mmproj_path.exists())
                self.assertGreater(len(progress_calls), 0)


class TestOllamaManager(unittest.TestCase):
    def test_recommended_catalog(self):
        self.assertIn("llama3.2:1b", RECOMMENDED_OLLAMA_MODELS)
        self.assertIn("qwen2.5:1.5b", RECOMMENDED_OLLAMA_MODELS)
        self.assertIn("moondream:latest", RECOMMENDED_OLLAMA_MODELS)
        self.assertIn("llama3.2-vision:latest", RECOMMENDED_OLLAMA_MODELS)
        self.assertTrue(RECOMMENDED_OLLAMA_MODELS["moondream:latest"].has_vision)
        self.assertTrue(RECOMMENDED_OLLAMA_MODELS["llama3.2-vision:latest"].has_vision)
        self.assertFalse(RECOMMENDED_OLLAMA_MODELS["llama3.2:1b"].has_vision)
        self.assertEqual(RECOMMENDED_OLLAMA_MODELS["moondream:latest"].capability_badge, "[👁️ Vision Supported]")
        self.assertEqual(RECOMMENDED_OLLAMA_MODELS["llama3.2:1b"].capability_badge, "[📝 Text-Only]")

    @patch("urllib.request.urlopen")
    def test_check_status_online(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        is_running, msg = OllamaManager.check_status("http://localhost:11434")
        self.assertTrue(is_running)
        self.assertIn("running", msg)

    @patch("urllib.request.urlopen")
    def test_check_status_offline(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        is_running, msg = OllamaManager.check_status("http://localhost:11434")
        self.assertFalse(is_running)
        self.assertIn("not running", msg)

    @patch("urllib.request.urlopen")
    def test_list_installed_models(self, mock_urlopen):
        fake_json = b'{"models": [{"name": "llama3.2:1b"}, {"name": "qwen2.5:1.5b"}]}'
        mock_resp = MagicMock()
        mock_resp.read.return_value = fake_json
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        models = OllamaManager.list_installed_models("http://localhost:11434")
        self.assertEqual(len(models), 2)
        self.assertIn("llama3.2:1b", models)
        self.assertIn("qwen2.5:1.5b", models)

    @patch("urllib.request.urlopen")
    def test_pull_model_streaming(self, mock_urlopen):
        stream_lines = [
            b'{"status": "pulling manifest"}\n',
            b'{"status": "downloading", "completed": 500, "total": 1000}\n',
            b'{"status": "downloading", "completed": 1000, "total": 1000}\n',
            b'{"status": "success"}\n',
        ]
        mock_resp = MagicMock()
        mock_resp.__iter__.return_value = stream_lines
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        progress_statuses = []
        def on_progress(status, completed, total, pct):
            progress_statuses.append((status, pct))

        success = OllamaManager.pull_model(
            model_name="llama3.2:1b",
            base_url="http://localhost:11434",
            progress_callback=on_progress,
        )
        self.assertTrue(success)
        self.assertGreaterEqual(len(progress_statuses), 3)
        self.assertEqual(progress_statuses[-1][0], "success")


class TestEmbeddedProvider(unittest.TestCase):
    def test_preset_exists(self):
        preset = get_preset("embedded")
        self.assertEqual(preset.id, "embedded")
        self.assertFalse(preset.requires_api_key)
        self.assertEqual(preset.base_url, "local://embedded")

    def test_factory_instantiation(self):
        provider = get_provider("embedded")
        self.assertIsInstance(provider, EmbeddedProvider)

    def test_provider_vision_attribute(self):
        text_prov = EmbeddedProvider(model_filename="qwen2.5-1.5b")
        self.assertFalse(text_prov.has_vision)

        vision_prov = EmbeddedProvider(model_filename="moondream2-vision")
        self.assertTrue(vision_prov.has_vision)

    def test_test_connection_not_downloaded(self):
        provider = EmbeddedProvider(model_filename="non_existent_model.gguf")
        success, msg = provider.test_connection()
        self.assertFalse(success)
        self.assertIn("not downloaded", msg)

    def test_analyze_image_text_model_raises_not_implemented(self):
        provider = EmbeddedProvider(model_filename="test.gguf")
        with self.assertRaises(NotImplementedError):
            provider.analyze_image("dummy.jpg", "test prompt", "test.gguf")

    def test_analyze_image_vision_model_raises_file_not_found(self):
        provider = EmbeddedProvider(model_filename="moondream2-vision")
        with self.assertRaises(FileNotFoundError):
            provider.analyze_image("dummy.jpg", "test prompt", "moondream2-vision")


class TestAppDeploymentLogic(unittest.TestCase):
    def test_service_accessors(self):
        from services import get_model_downloader, get_ollama_manager
        dl, catalog = get_model_downloader()
        self.assertIsNotNone(dl)
        self.assertIn("qwen2.5-1.5b", catalog)

        om, recommended = get_ollama_manager()
        self.assertIsNotNone(om)
        self.assertIn("llama3.2:1b", recommended)

    def test_embedded_model_activation_updates_preset(self):
        from services.providers import get_preset_by_name
        preset = get_preset_by_name("Built-In Embedded AI (100% Offline GGUF)")
        self.assertIsNotNone(preset)
        self.assertEqual(preset.id, "embedded")
        self.assertEqual(preset.base_url, "local://embedded")


if __name__ == "__main__":
    unittest.main()
