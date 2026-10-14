"""
UI Modules for NoMoreClutter (PRINCIPLE-003: Modularity)
"""

from .tree_preview import TreePreviewDialog
from .duplicate_finder import DuplicateFinderDialog
from .junk_cleaner import JunkCleanerDialog
from .file_viewer import FileViewerDialog

__all__ = ["TreePreviewDialog", "DuplicateFinderDialog", "JunkCleanerDialog", "FileViewerDialog"]
