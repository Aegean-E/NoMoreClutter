"""
Unit tests for Principles and Knowledge Base Synchronization (PRINCIPLE-011).
Tests principle parsing, guideline content generation, and AST symbol extraction.
"""

import ast
import tempfile
import unittest
from pathlib import Path
from scripts.sync_principles import parse_principles, generate_gemini_content
from scripts.update_knowledge_base import extract_python_symbols


class TestSyncAndKnowledge(unittest.TestCase):
    def test_parse_principles(self):
        """Principle parser should parse principles conforming to PRINCIPLE-XXX schema."""
        sample_markdown = """
### PRINCIPLE-001: RLM Compatibility
- **Concept**: The system must be built for Recursive Language Model processing.
- **Rules**:
  1. Hierarchical decomposition.

### PRINCIPLE-002: Automatic Git Workflow
- **Concept**: Maintain active git trail.
- **Rules**:
  1. Commit automatically.
"""
        with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(sample_markdown)
            f.flush()
            temp_path = Path(f.name)

        try:
            principles = parse_principles(temp_path)
            self.assertEqual(len(principles), 2)
            self.assertEqual(principles[0]["id"], "PRINCIPLE-001")
            self.assertEqual(principles[0]["title"], "RLM Compatibility")
            self.assertEqual(principles[1]["id"], "PRINCIPLE-002")
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_generate_gemini_content(self):
        """Generated guideline content should include all parsed principles."""
        principles = [
            {"id": "PRINCIPLE-001", "title": "Test Principle", "concept": "Test concept"}
        ]
        content = generate_gemini_content(principles)
        self.assertIn("PRINCIPLE-001: Test Principle", content)
        self.assertIn("Test concept", content)

    def test_extract_python_symbols(self):
        """AST extractor should identify classes, methods, functions, and docstrings."""
        sample_code = '''"""Sample module docstring."""

class SampleClass:
    """Class docstring."""
    def sample_method(self, arg1, arg2):
        """Method docstring."""
        pass

def standalone_func(x):
    """Function docstring."""
    return x * 2
'''
        with tempfile.NamedTemporaryFile("w+", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(sample_code)
            f.flush()
            temp_path = Path(f.name)

        try:
            symbols = extract_python_symbols(temp_path)
            self.assertEqual(symbols["docstring"], "Sample module docstring.")
            self.assertEqual(len(symbols["classes"]), 1)
            self.assertEqual(symbols["classes"][0]["name"], "SampleClass")
            self.assertEqual(symbols["classes"][0]["methods"][0]["name"], "sample_method")
            self.assertEqual(symbols["classes"][0]["methods"][0]["args"], ["arg1", "arg2"])
            self.assertEqual(len(symbols["functions"]), 1)
            self.assertEqual(symbols["functions"][0]["name"], "standalone_func")
            self.assertEqual(symbols["functions"][0]["args"], ["x"])
        finally:
            if temp_path.exists():
                temp_path.unlink()


if __name__ == "__main__":
    unittest.main()
