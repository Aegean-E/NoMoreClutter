"""
Unit tests for Document Content Peeker (PRINCIPLE-007, PRINCIPLE-009, PRINCIPLE-011)
Tests plain text, docx, pdf stream extraction, truncation, and RLM dense payload integration.
"""

import io
import os
import tempfile
import unittest
import zipfile
from services.document_peeker import DocumentPeeker
from services.rlm_organizer import RLMOrganizer
from services.providers.base import BaseAIProvider
from models import FileChange


class DummyProvider(BaseAIProvider):
    def __init__(self):
        super().__init__(base_url="http://dummy", api_key="dummy")
        self.last_prompt = ""

    def test_connection(self, model=None):
        return True, "Connected"

    def complete(self, prompt, model, temperature=0.2, max_tokens=1500):
        self.last_prompt = prompt
        return '[{"id": 0, "folder": "Invoices", "name": "acme_invoice.txt"}]'

    def analyze_image(self, image_path, prompt, model, max_tokens=100):
        return "{}"


class TestDocumentPeeker(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_plain_text_peeking(self):
        file_path = os.path.join(self.root, "sample.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("Line 1: Q3 Financial Summary\nLine 2: Revenue increased by 20%\nLine 3: Confidential")

        peek = DocumentPeeker.peek(file_path, max_chars=40)
        self.assertTrue(peek.startswith("Line 1: Q3 Financial Summary Line 2:"))
        self.assertTrue(peek.endswith("..."))
        self.assertLessEqual(len(peek), 45)
        # Ensure newlines were sanitized into spaces
        self.assertNotIn("\n", peek)

    def test_code_file_peeking(self):
        file_path = os.path.join(self.root, "script.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("import os\n\ndef organize_files():\n    pass")

        peek = DocumentPeeker.peek(file_path, max_chars=100)
        self.assertIn("import os def organize_files()", peek)

    def test_docx_peeking(self):
        file_path = os.path.join(self.root, "document.docx")
        # Build synthetic docx zip archive with word/document.xml
        xml_content = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body><w:p><w:r><w:t>Project Apollo Launch Architecture</w:t></w:r></w:p></w:body>'
            '</w:document>'
        )
        with zipfile.ZipFile(file_path, "w") as z:
            z.writestr("word/document.xml", xml_content)

        peek = DocumentPeeker.peek(file_path, max_chars=100)
        self.assertEqual(peek, "Project Apollo Launch Architecture")

    def test_pdf_peeking_uncompressed(self):
        file_path = os.path.join(self.root, "invoice.pdf")
        pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
            b"BT\n"
            b"(Acme Corporation Official Receipt #9421) Tj\n"
            b"ET\n"
            b"%%EOF\n"
        )
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        peek = DocumentPeeker.peek(file_path, max_chars=100)
        self.assertIn("Acme Corporation Official Receipt #9421", peek)

    def test_nonexistent_or_empty_file(self):
        self.assertEqual(DocumentPeeker.peek(""), "")
        self.assertEqual(DocumentPeeker.peek(os.path.join(self.root, "does_not_exist.txt")), "")

        empty_file = os.path.join(self.root, "empty.txt")
        with open(empty_file, "w", encoding="utf-8") as f:
            pass
        self.assertEqual(DocumentPeeker.peek(empty_file), "")

    def test_rlm_organizer_content_peeking_integration(self):
        """Verify that RLMOrganizer includes 'peek' key in candidate items when enabled."""
        file_path = os.path.join(self.root, "meeting_notes.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Engineering Sprint Planning\nTopic: Microservices Migration")

        provider = DummyProvider()
        organizer = RLMOrganizer(provider=provider)

        organizer.organize(
            files=[file_path],
            model="test-model",
            output_folder=self.root,
            content_peeking=True
        )

        self.assertIn('"peek"', provider.last_prompt)
        self.assertIn("Engineering Sprint Planning", provider.last_prompt)


if __name__ == "__main__":
    unittest.main()
