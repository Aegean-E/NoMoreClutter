"""
Document Content Peeker (PRINCIPLE-007: Performance, PRINCIPLE-009: Token Frugality)
Extracts brief, token-budgeted text snippets from documents (TXT, MD, PDF, DOCX, CSV, Code)
to empower semantic AI categorization without dumping entire files into prompts.
Zero external dependencies (uses standard library zipfile, zlib, re, os).
"""

import os
import re
import zipfile
import zlib
from typing import Optional, Set

# File extensions recognized as text or code documents
TEXT_EXTENSIONS: Set[str] = {
    ".txt", ".md", ".rtf", ".csv", ".tsv", ".json", ".yaml", ".yml",
    ".xml", ".html", ".htm", ".log", ".ini", ".conf", ".cfg",
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
    ".cs", ".php", ".rb", ".go", ".rs", ".sql", ".sh", ".bat", ".ps1"
}


class DocumentPeeker:
    """Safely extracts compact text snippets from documents for intelligent categorization."""

    @classmethod
    def peek(cls, file_path: str, max_chars: int = 200) -> str:
        """
        Extract a brief, clean snippet (first max_chars) from a document.
        
        Args:
            file_path: Absolute path to the file.
            max_chars: Maximum characters to extract (default 200).
            
        Returns:
            str: Clean, single-line text snippet, or empty string if unreadable.
        """
        if not file_path or not os.path.exists(file_path):
            return ""

        try:
            # Don't inspect empty or excessively tiny files
            size = os.path.getsize(file_path)
            if size == 0:
                return ""

            ext = os.path.splitext(file_path)[1].lower()

            if ext in TEXT_EXTENSIONS:
                raw_text = cls._extract_plain_text(file_path, max_bytes=2048)
            elif ext == ".docx":
                raw_text = cls._extract_docx(file_path)
            elif ext == ".pdf":
                raw_text = cls._extract_pdf(file_path)
            else:
                return ""

            return cls._clean_and_truncate(raw_text, max_chars=max_chars)

        except Exception:
            # Fail silently and gracefully to ensure organization pipeline is never interrupted
            return ""

    @staticmethod
    def _extract_plain_text(file_path: str, max_bytes: int = 2048) -> str:
        """Read beginning of text file with utf-8 and latin-1 fallback."""
        try:
            with open(file_path, "rb") as f:
                data = f.read(max_bytes)
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                return data.decode("latin-1", errors="ignore")
        except Exception:
            return ""

    @staticmethod
    def _extract_docx(file_path: str) -> str:
        """Extract text from docx zip archive word/document.xml without external libraries."""
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                if "word/document.xml" in z.namelist():
                    xml_content = z.read("word/document.xml").decode("utf-8", errors="ignore")
                    # Extract text inside <w:t> tags
                    paragraphs = re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml_content)
                    return " ".join(paragraphs)
            return ""
        except Exception:
            return ""

    @staticmethod
    def _extract_pdf(file_path: str, max_scan_bytes: int = 65536) -> str:
        """
        Extract text from PDF streams using standard library decompresion.
        Inspects stream blocks and FlateDecode filters.
        """
        try:
            with open(file_path, "rb") as f:
                content = f.read(max_scan_bytes)

            extracted_fragments = []

            # 1. Look for uncompressed text blocks: BT ... ET
            bt_matches = re.findall(rb"BT\s*(.*?)\s*ET", content, re.DOTALL)
            for block in bt_matches:
                text_matches = re.findall(rb"\((.*?)\)", block)
                for tm in text_matches:
                    try:
                        decoded = tm.decode("utf-8", errors="ignore")
                        if len(decoded.strip()) > 2:
                            extracted_fragments.append(decoded)
                    except Exception:  # hygiene: allow malformed raw PDF fragment decode is skipped
                        pass
                if len(" ".join(extracted_fragments)) >= 300:
                    break

            # 2. If no plain text found, attempt decompressing FlateDecode streams
            if not extracted_fragments:
                stream_pattern = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.DOTALL)
                for stream_match in stream_pattern.finditer(content):
                    stream_data = stream_match.group(1)
                    try:
                        # Attempt zlib decompression
                        decompressed = zlib.decompress(stream_data)
                        text_matches = re.findall(rb"\((.*?)\)", decompressed)
                        for tm in text_matches:
                            decoded = tm.decode("utf-8", errors="ignore")
                            if len(decoded.strip()) > 2:
                                extracted_fragments.append(decoded)
                        if len(" ".join(extracted_fragments)) >= 300:
                            break
                    except Exception:  # hygiene: allow non-zlib streams in PDF are skipped
                        continue

            return " ".join(extracted_fragments)

        except Exception:
            return ""

    @staticmethod
    def _clean_and_truncate(text: str, max_chars: int = 200) -> str:
        """Sanitize text to a single-line snippet and truncate to max_chars."""
        if not text:
            return ""
        # Remove control characters
        text = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", text)
        # Collapse multiple whitespace characters into single space
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > max_chars:
            return text[:max_chars].rstrip() + "..."
        return text
