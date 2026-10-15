"""
Unit tests for RLM Organizer (PRINCIPLE-001, PRINCIPLE-007, PRINCIPLE-009)
"""

import unittest
from services.rlm_organizer import RLMOrganizer
from services.providers.base import BaseAIProvider
from models import FileChange


class MockProvider(BaseAIProvider):
    def __init__(self, mock_response: str = ""):
        super().__init__(base_url="http://mock", api_key="mock")
        self.mock_response = mock_response

    def test_connection(self, model=None):
        return True, "Mock connected"

    def complete(self, prompt, model, temperature=0.2, max_tokens=1500):
        return self.mock_response

    def analyze_image(self, image_path, prompt, model, max_tokens=150):
        return '{"folder": "Screenshots", "name": "app_preview"}'


class TestRLMOrganizer(unittest.TestCase):
    def test_json_extraction_raw(self):
        text = '[{"id": 0, "folder": "Work", "name": "report.pdf"}]'
        parsed = RLMOrganizer._extract_json(text)
        self.assertIsInstance(parsed, list)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["folder"], "Work")

    def test_json_extraction_markdown_fenced(self):
        text = 'Here is the result:\n```json\n[{"id": 0, "folder": "Nature", "name": "sunset.jpg"}]\n```'
        parsed = RLMOrganizer._extract_json(text)
        self.assertIsInstance(parsed, list)
        self.assertEqual(parsed[0]["name"], "sunset.jpg")

    def test_heuristic_categorization(self):
        self.assertEqual(RLMOrganizer.get_heuristic_category("document.pdf"), "Documents")
        self.assertEqual(RLMOrganizer.get_heuristic_category("song.mp3"), "Audio")
        self.assertEqual(RLMOrganizer.get_heuristic_category("archive.zip"), "Archives")
        self.assertEqual(RLMOrganizer.get_heuristic_category("photo.png"), "Images")
        self.assertEqual(RLMOrganizer.get_heuristic_category("code.py"), "Code")
        self.assertEqual(RLMOrganizer.get_heuristic_category("unknown.xyz123"), "Other")

    def test_numbered_rename(self):
        changes = [
            FileChange(original="/source/a.jpg", action="move", new_path="/dest/Photos/a.jpg"),
            FileChange(original="/source/b.jpg", action="move", new_path="/dest/Photos/b.jpg"),
            FileChange(original="/source/c.png", action="move", new_path="/dest/Photos/c.png"),
        ]
        renamed = RLMOrganizer._apply_numbered_rename(changes)
        import os
        self.assertEqual(os.path.normpath(renamed[0].new_path), os.path.normpath("/dest/Photos/1.jpg"))
        self.assertEqual(os.path.normpath(renamed[1].new_path), os.path.normpath("/dest/Photos/2.jpg"))
        self.assertEqual(os.path.normpath(renamed[2].new_path), os.path.normpath("/dest/Photos/1.png"))

    def test_organize_mock(self):
        mock_resp = '[{"id": 0, "folder": "Finance", "name": "q3_tax.pdf"}]'
        organizer = RLMOrganizer(provider=MockProvider(mock_resp))
        files = ["/data/source/receipt.pdf"]
        results = organizer.organize(
            files=files,
            model="test-model",
            output_folder="/data/dest",
            existing_folders=["Finance", "Personal"],
            create_new_folders=True,
            ai_rename=True,
        )
        self.assertEqual(len(results), 1)
        self.assertIn("Finance", results[0].new_path)
        self.assertIn("q3_tax.pdf", results[0].new_path)

    def test_organize_non_vision_provider_routes_to_regular_rlm(self):
        class NonVisionProvider(MockProvider):
            @property
            def has_vision(self):
                return False

        # Even if LLM returns 'Animals', camera timestamp anti-hallucination guard routes to Photos/2017
        mock_resp = '[{"id": 0, "folder": "Animals", "name": "animal.jpg"}]'
        organizer = RLMOrganizer(provider=NonVisionProvider(mock_resp))
        files = ["/data/source/20170926_112101.jpg"]

        results = organizer.organize(
            files=files,
            model="test-model",
            output_folder="/data/dest",
            analyze_images=True,  # User requested vision, but provider is text-only
            ai_rename=True,
        )
        self.assertEqual(len(results), 1)
        import os
        normalized = os.path.normpath(results[0].new_path)
        self.assertIn(os.path.normpath("Photos/2017"), normalized)
        self.assertIn("20170926_112101.jpg", normalized)

    def test_organize_vision_not_implemented_graceful_fallback(self):
        class NotImplementedVisionProvider(MockProvider):
            def analyze_image(self, image_path, prompt, model, max_tokens=150):
                raise NotImplementedError("Text-only model")

        mock_resp = '[{"id": 0, "folder": "Artwork", "name": "admin_icon.svg"}]'
        organizer = RLMOrganizer(provider=NotImplementedVisionProvider(mock_resp))
        files = ["/data/source/admin_icon.svg"]

        results = organizer.organize(
            files=files,
            model="test-model",
            output_folder="/data/dest",
            analyze_images=True,
            ai_rename=True,
        )
        self.assertEqual(len(results), 1)
        self.assertIn("Artwork", results[0].new_path)

    def test_organize_vision_runtime_error_aborts_immediately_and_routes_to_text_rlm(self):
        call_count = {"count": 0}

        class RuntimeErrorVisionProvider(MockProvider):
            def analyze_image(self, image_path, prompt, model, max_tokens=150):
                call_count["count"] += 1
                raise RuntimeError("llama-cpp-python with multimodal support is required for local vision analysis.")

        # Text RLM mock response
        mock_resp = (
            '[{"id": 0, "folder": "General", "name": "20170926_112101.jpg"}, '
            '{"id": 1, "folder": "General", "name": "20180401_191543.jpg"}, '
            '{"id": 2, "folder": "Icons", "name": "admin_icon.svg"}]'
        )
        organizer = RLMOrganizer(provider=RuntimeErrorVisionProvider(mock_resp))
        files = [
            "/data/source/20170926_112101.jpg",
            "/data/source/20180401_191543.jpg",
            "/data/source/admin_icon.svg",
        ]

        results = organizer.organize(
            files=files,
            model="test-model",
            output_folder="/data/dest",
            analyze_images=True,
            ai_rename=True,
        )
        # Vision must abort on initial failure and not spam 3 failed calls
        self.assertEqual(call_count["count"], 1)
        self.assertEqual(len(results), 3)

        import os
        paths = [os.path.normpath(r.new_path) for r in results]
        # Photos are cleanly categorized into date albums, not dumped into Images/
        self.assertTrue(any(os.path.normpath("Photos/2017") in p for p in paths))
        self.assertTrue(any(os.path.normpath("Photos/2018") in p for p in paths))
        self.assertTrue(any("Icons" in p for p in paths))
        self.assertFalse(any(os.path.normpath("/Images/") in p for p in paths))

    def test_smart_image_folder_extraction(self):
        self.assertEqual(RLMOrganizer._get_smart_image_folder("20170926_112101.jpg"), "Photos/2017")
        self.assertEqual(RLMOrganizer._get_smart_image_folder("20220813_205117_01.jpg"), "Photos/2022")
        self.assertEqual(RLMOrganizer._get_smart_image_folder("IMG_20191225_001.png"), "Photos/2019")
        self.assertEqual(RLMOrganizer._get_smart_image_folder("photo_2020-05-01.webp"), "Photos/2020")
        self.assertEqual(RLMOrganizer._get_smart_image_folder("random_graphic.png"), "Photos")

    def test_heuristic_fallback_batch_image_albums(self):
        organizer = RLMOrganizer(provider=MockProvider())
        files = ["/source/20170926_112101.jpg", "/source/20180401_191543.jpg", "/source/notes.txt"]
        changes = organizer._heuristic_fallback_batch(files, "/dest", [])
        import os
        self.assertEqual(len(changes), 3)
        self.assertEqual(os.path.normpath(changes[0].new_path), os.path.normpath("/dest/Photos/2017/20170926_112101.jpg"))
        self.assertEqual(os.path.normpath(changes[1].new_path), os.path.normpath("/dest/Photos/2018/20180401_191543.jpg"))
        self.assertEqual(os.path.normpath(changes[2].new_path), os.path.normpath("/dest/Documents/notes.txt"))


    def test_sanitize_non_string_types(self):
        self.assertEqual(RLMOrganizer._sanitize_folder_name(2017), "2017")
        self.assertEqual(RLMOrganizer._sanitize_folder_name(None), "General")
        self.assertEqual(RLMOrganizer._sanitize_filename(142809, "/path/img.jpg"), "142809.jpg")
        self.assertEqual(RLMOrganizer._sanitize_filename(None, "/path/img.jpg"), "img.jpg")

    def test_process_images_with_integer_json_fields(self):
        class IntVisionProvider(BaseAIProvider):
            def __init__(self):
                super().__init__(base_url="http://mock", api_key="mock")
            def test_connection(self, model=None):
                return True, "Mock"
            def complete(self, prompt, model, **kwargs):
                return ""
            def analyze_image(self, image_path, prompt, model, **kwargs):
                return '{"folder": 2017, "name": 142809}'

        organizer = RLMOrganizer(provider=IntVisionProvider())
        results = organizer._process_images_hierarchical(
            files=["/source/20171026_142809.jpg"],
            model="mock",
            output_folder="/dest",
            existing_folders=[],
            create_new_folders=True,
            ai_rename=True,
        )
        import os
        self.assertEqual(len(results), 1)
        self.assertEqual(os.path.normpath(results[0].new_path), os.path.normpath("/dest/2017/142809.jpg"))


if __name__ == "__main__":
    unittest.main()
