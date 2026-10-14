"""
Unit tests for Standalone llama-server.exe Manager (PRINCIPLE-003, PRINCIPLE-008, PRINCIPLE-011).
Validates path resolution, installation detection, mock download & zip extraction,
process lifecycle, and OpenAI-compatible HTTP communication.
Zero GUI dependencies (runs 100% headless).
"""

import os
import io
import json
import zipfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from services.llama_server_manager import (
    get_bin_dir,
    get_server_exe_path,
    is_server_installed,
    download_server,
    LlamaServerManager,
)


class TestLlamaServerManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        self.bin_dir = self.root / "models" / "bin"
        self.bin_dir.mkdir(parents=True, exist_ok=True)
        LlamaServerManager.stop_server()

    def tearDown(self):
        LlamaServerManager.stop_server()
        self.tmpdir.cleanup()

    def test_paths(self):
        """Verify binary directory and executable path resolution."""
        bin_dir = get_bin_dir()
        self.assertTrue(bin_dir.exists())
        exe_path = get_server_exe_path()
        self.assertTrue(str(exe_path).endswith("llama-server.exe") or str(exe_path).endswith("llama-server"))

    def test_is_server_installed_detection(self):
        """Verify is_server_installed accurately detects presence of executable."""
        with patch("services.llama_server_manager.get_server_exe_path") as mock_path, \
             patch("services.llama_server_manager.shutil.which", return_value=None):
            fake_exe = self.bin_dir / "llama-server.exe"
            mock_path.return_value = fake_exe

            # Missing file
            self.assertFalse(is_server_installed())

            # File too small (<4000 bytes)
            fake_exe.write_bytes(b"small")
            self.assertFalse(is_server_installed())

            # Valid executable (>4000 bytes)
            fake_exe.write_bytes(b"X" * 10000)
            self.assertTrue(is_server_installed())

    def test_download_server_mock(self):
        """Verify streaming download and zip extraction of executable and DLLs."""
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as z:
            z.writestr("llama-server.exe", b"MZ_FAKE_SERVER_BINARY" * 500)
            z.writestr("llama.dll", b"MZ_FAKE_DLL_BINARY" * 500)
            z.writestr("readme.txt", b"Should be ignored")
        zip_bytes = zip_buf.getvalue()

        class MockApiResponse:
            status = 200
            def read(self, *args):
                return json.dumps({
                    "assets": [{
                        "name": "llama-bin-win-cpu-x64.zip",
                        "browser_download_url": "https://mock.download/llama.zip"
                    }]
                }).encode("utf-8")
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass

        class MockDownloadResponse:
            headers = {"Content-Length": str(len(zip_bytes))}
            status = 200

            def __init__(self):
                self._stream = io.BytesIO(zip_bytes)

            def read(self, size=-1):
                return self._stream.read(size)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        def urlopen_side_effect(req, *args, **kwargs):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            if "api.github.com" in url:
                return MockApiResponse()
            return MockDownloadResponse()

        progress_calls = []

        def mock_cb(status_text, downloaded, total, pct):
            progress_calls.append((status_text, pct))

        with patch("services.llama_server_manager.get_bin_dir", return_value=self.bin_dir), \
             patch("services.llama_server_manager.get_server_exe_path", return_value=self.bin_dir / "llama-server.exe"), \
             patch("urllib.request.urlopen", side_effect=urlopen_side_effect):

            target = download_server(progress_callback=mock_cb)
            self.assertTrue(target.exists())
            self.assertTrue((self.bin_dir / "llama.dll").exists())
            self.assertFalse((self.bin_dir / "readme.txt").exists())
            self.assertTrue(len(progress_calls) > 0)

    def test_start_server_missing_model(self):
        """Verify start_server fails gracefully if model file does not exist."""
        with patch.object(LlamaServerManager, "get_effective_exe_path", return_value=self.bin_dir / "llama-server.exe"):
            (self.bin_dir / "llama-server.exe").write_bytes(b"X" * 10000)
            success, msg = LlamaServerManager.start_server(model_path="nonexistent_model.gguf")
            self.assertFalse(success)
            self.assertIn("not found", msg)

    def test_start_server_success_and_reuse(self):
        """Verify server starts, polls /health, and reuses instance on identical configuration."""
        fake_model = self.root / "model.gguf"
        fake_model.write_bytes(b"GGUF" * 1000)
        fake_exe = self.bin_dir / "llama-server.exe"
        fake_exe.write_bytes(b"X" * 10000)

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None

        class MockHealthResp:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        with patch.object(LlamaServerManager, "get_effective_exe_path", return_value=fake_exe), \
             patch("subprocess.Popen", return_value=mock_proc), \
             patch("urllib.request.urlopen", return_value=MockHealthResp()):

            # First start
            success, msg = LlamaServerManager.start_server(model_path=fake_model, port=9999)
            self.assertTrue(success)
            self.assertIn("ready on port 9999", msg)

            # Second start with identical parameters must reuse existing process
            success2, msg2 = LlamaServerManager.start_server(model_path=fake_model, port=9999)
            self.assertTrue(success2)
            self.assertIn("already running", msg2)

    def test_complete_mock(self):
        """Verify text completion parses OpenAI JSON response format."""
        fake_model = self.root / "model.gguf"
        fake_model.write_bytes(b"GGUF" * 1000)

        mock_response_data = json.dumps({
            "choices": [{"message": {"content": "Documents"}}]
        }).encode("utf-8")

        class MockResp:
            status = 200

            def read(self):
                return mock_response_data

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        with patch.object(LlamaServerManager, "start_server", return_value=(True, "Ready")), \
             patch("urllib.request.urlopen", return_value=MockResp()):

            res = LlamaServerManager.complete("Sort file", model_path=fake_model)
            self.assertEqual(res, "Documents")

    def test_analyze_image_mock(self):
        """Verify image analysis calls endpoint and returns generated description."""
        fake_model = self.root / "model.gguf"
        fake_model.write_bytes(b"GGUF" * 1000)
        fake_proj = self.root / "proj.gguf"
        fake_proj.write_bytes(b"PROJ" * 1000)
        fake_img = self.root / "test.jpg"
        fake_img.write_bytes(b"\xFF\xD8\xFF\xE0" + b"\x00" * 100)

        mock_response_data = json.dumps({
            "content": "A scenic landscape with trees"
        }).encode("utf-8")

        class MockResp:
            status = 200

            def read(self):
                return mock_response_data

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        with patch.object(LlamaServerManager, "start_server", return_value=(True, "Ready")), \
             patch("urllib.request.urlopen", return_value=MockResp()):

            res = LlamaServerManager.analyze_image(
                image_path=fake_img,
                prompt="Describe",
                model_path=fake_model,
                mmproj_path=fake_proj,
            )
            self.assertEqual(res, "A scenic landscape with trees")


if __name__ == "__main__":
    unittest.main()
