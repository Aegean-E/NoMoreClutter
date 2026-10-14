"""
Unit tests for BenchmarkService & Camera Photo Anti-Hallucination Guard (PRINCIPLE-007, PRINCIPLE-011).
Tests latency measurement, optimal batch calculation, vision detection, and camera date grouping.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock
from services.benchmark_service import BenchmarkService, BenchmarkResult
from services.rlm_organizer import RLMOrganizer
from services.providers.base import BaseAIProvider
from models import FileChange


class MockBenchProvider(BaseAIProvider):
    def __init__(self, delay_sec=0.05, return_json=None):
        super().__init__(base_url="http://mock", api_key="test")
        self.delay_sec = delay_sec
        self.return_json = return_json or '[{"id": 0, "folder": "Invoices", "name": "q3_invoice.pdf"}, {"id": 1, "folder": "Code", "name": "clean_dataset.py"}, {"id": 2, "folder": "Photos/2017", "name": "20170926_112101.jpg"}]'

    def test_connection(self, model=None):
        return True, "Connected"

    def complete(self, prompt, model, temperature=0.2, max_tokens=1500):
        import time
        if self.delay_sec > 0:
            time.sleep(self.delay_sec)
        return self.return_json

    def analyze_image(self, image_path, prompt, model, max_tokens=100):
        return "{}"


class MockAnimalsHallucinatingProvider(BaseAIProvider):
    """Simulates the bug where model assigns 'Animals' to all camera timestamps."""
    def __init__(self):
        super().__init__(base_url="http://mock", api_key="test")

    def test_connection(self, model=None):
        return True, "Connected"

    def complete(self, prompt, model, temperature=0.2, max_tokens=1500):
        return '[{"id": 0, "folder": "Animals", "name": "animal_1.jpg"}, {"id": 1, "folder": "Animals", "name": "animal_2.jpg"}]'

    def analyze_image(self, image_path, prompt, model, max_tokens=100):
        return "{}"


class TestBenchmarkService(unittest.TestCase):
    def test_fast_cloud_benchmark(self):
        """Fast latency (<800ms) should recommend batch size 15 and limit 100."""
        provider = MockBenchProvider(delay_sec=0.01)
        progress_msgs = []

        def prog(msg, val):
            progress_msgs.append((msg, val))

        result = BenchmarkService.run_benchmark(
            provider=provider,
            model="llama-3.3-70b-versatile",
            provider_name="Groq (Free & Fastest - Zero Install)",
            progress_callback=prog,
        )

        self.assertIsInstance(result, BenchmarkResult)
        self.assertTrue(result.is_json_compliant)
        self.assertEqual(result.recommended_batch_size, 15)
        self.assertEqual(result.recommended_limit, 100)
        self.assertIn("Ultra-Fast", result.hardware_tier)
        self.assertGreater(len(progress_msgs), 2)

    def test_vision_model_detection(self):
        """Models with vision in their name should be flagged as vision-capable."""
        provider = MockBenchProvider(delay_sec=0.01)
        result = BenchmarkService.run_benchmark(
            provider=provider,
            model="llama-3.2-11b-vision-preview",
            provider_name="Groq",
        )
        self.assertTrue(result.is_vision_supported)
        self.assertTrue(any("Vision Supported" in rec for rec in result.recommendations))

    def test_camera_photo_anti_hallucination_guard(self):
        """
        Verify that when a model erroneously assigns 'Animals' to camera timestamps,
        the anti-hallucination guard corrects the folder to 'Photos/{Year}' and preserves the filename.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            file_1 = os.path.join(tmpdir, "20170926_112101.jpg")
            file_2 = os.path.join(tmpdir, "20180416_103236.jpg")
            with open(file_1, "w") as f:
                f.write("fake photo 1")
            with open(file_2, "w") as f:
                f.write("fake photo 2")

            provider = MockAnimalsHallucinatingProvider()
            organizer = RLMOrganizer(provider=provider)

            changes = organizer.organize(
                files=[file_1, file_2],
                model="test-model",
                output_folder=tmpdir,
                analyze_images=False,
            )

            self.assertEqual(len(changes), 2)

            # Neither file should be put in 'Animals/'!
            for change in changes:
                dest_folder = os.path.basename(os.path.dirname(change.new_path))
                parent_folder = os.path.basename(os.path.dirname(os.path.dirname(change.new_path)))
                self.assertNotEqual(dest_folder.lower(), "animals")
                self.assertNotEqual(parent_folder.lower(), "animals")

            # Check that file 1 was routed to Photos/2017 and file 2 to Photos/2018
            self.assertIn("2017", changes[0].new_path)
            self.assertIn("2018", changes[1].new_path)
            # Original timestamp filename preserved
            self.assertTrue(changes[0].new_path.endswith("20170926_112101.jpg"))
            self.assertTrue(changes[1].new_path.endswith("20180416_103236.jpg"))


if __name__ == "__main__":
    unittest.main()
