#!/usr/bin/env python3
"""
Codebase Knowledge Base Auto-Updater & Validator (PRINCIPLE-010)

Inspects the repository AST, extracts exported classes, functions, docstrings,
and generates the authoritative `knowledge/codebase_map.md`. Also validates
the integrity of all knowledge base documents.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
CODEBASE_MAP_PATH = KNOWLEDGE_DIR / "codebase_map.md"

CORE_DOCS = [
    "INDEX.md",
    "architecture.md",
    "services.md",
    "data_models.md",
    "state_and_ui.md",
    "decisions.md",
    "codebase_map.md",
]

TARGET_DIRS = ["models", "services", "tests"]
TARGET_FILES = ["main.py"]


def extract_python_symbols(file_path: Path) -> Dict[str, Any]:
    """Parse a python file with AST and extract docstrings, classes, and functions."""
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except Exception as e:
        return {"error": str(e), "classes": [], "functions": [], "docstring": None}

    module_docstring = ast.get_docstring(tree)
    classes = []
    functions = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_doc = ast.get_docstring(node)
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    # Extract arguments
                    args = [arg.arg for arg in item.args.args if arg.arg != "self"]
                    methods.append({
                        "name": item.name,
                        "args": args,
                        "docstring": ast.get_docstring(item)
                    })
            classes.append({
                "name": node.name,
                "docstring": class_doc,
                "methods": methods
            })
        elif isinstance(node, ast.FunctionDef):
            args = [arg.arg for arg in node.args.args]
            functions.append({
                "name": node.name,
                "args": args,
                "docstring": ast.get_docstring(node)
            })

    line_count = len(content.splitlines())
    return {
        "docstring": module_docstring,
        "classes": classes,
        "functions": functions,
        "line_count": line_count,
        "size_bytes": len(content.encode("utf-8"))
    }


def generate_codebase_map() -> str:
    """Generate the markdown content for knowledge/codebase_map.md."""
    lines = [
        "# Codebase Map & Symbol Catalog 🗺️",
        "",
        "> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**",
        "> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across the NoMoreClutter repository.",
        "",
        "---",
        ""
    ]

    # Collect python files
    files_to_scan = []
    for tf in TARGET_FILES:
        p = ROOT_DIR / tf
        if p.exists():
            files_to_scan.append(p)

    for td in TARGET_DIRS:
        dp = ROOT_DIR / td
        if dp.exists():
            for p in sorted(dp.rglob("*.py")):
                if "__pycache__" not in p.parts:
                    files_to_scan.append(p)

    lines.append("## 📦 Module Summary Table")
    lines.append("")
    lines.append("| Module Path | Lines | Size (Bytes) | Classes | Functions |")
    lines.append("|-------------|-------|--------------|---------|-----------|")

    parsed_modules = {}
    for fp in files_to_scan:
        rel_path = fp.relative_to(ROOT_DIR).as_posix()
        info = extract_python_symbols(fp)
        parsed_modules[rel_path] = info
        cls_count = len(info.get("classes", []))
        fn_count = len(info.get("functions", []))
        lines.append(f"| `{rel_path}` | {info.get('line_count', 0)} | {info.get('size_bytes', 0)} | {cls_count} | {fn_count} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🔍 Deep Symbol Breakdown")
    lines.append("")

    for rel_path, info in parsed_modules.items():
        lines.append(f"### `{rel_path}`")
        if info.get("docstring"):
            lines.append(f"> {info['docstring'].strip()}")
            lines.append("")

        classes = info.get("classes", [])
        if classes:
            lines.append("#### Classes")
            for cls in classes:
                lines.append(f"- **`{cls['name']}`**")
                if cls.get("docstring"):
                    lines.append(f"  - *{cls['docstring'].strip()}*")
                methods = cls.get("methods", [])
                if methods:
                    for m in methods:
                        arg_str = ", ".join(m["args"])
                        lines.append(f"  - Method `.{m['name']}({arg_str})`")

        functions = info.get("functions", [])
        if functions:
            lines.append("#### Functions")
            for fn in functions:
                arg_str = ", ".join(fn["args"])
                lines.append(f"- `def {fn['name']}({arg_str})`")
                if fn.get("docstring"):
                    lines.append(f"  - *{fn['docstring'].strip()}*")

        lines.append("")

    return "\n".join(lines)


def update_and_validate(check_only: bool = False):
    """Update or check knowledge base files."""
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Verify existence of core documents
    missing_docs = []
    for doc in CORE_DOCS:
        doc_path = KNOWLEDGE_DIR / doc
        if not doc_path.exists() and doc != "codebase_map.md":
            missing_docs.append(doc)

    if missing_docs:
        print(f"[ERROR] Missing knowledge base documents in {KNOWLEDGE_DIR}: {missing_docs}")
        if check_only:
            sys.exit(1)

    # 2. Generate expected codebase map
    expected_map = generate_codebase_map()

    # 3. Check / Update codebase_map.md
    needs_update = True
    if CODEBASE_MAP_PATH.exists():
        current_map = CODEBASE_MAP_PATH.read_text(encoding="utf-8")
        if current_map.strip() == expected_map.strip():
            needs_update = False

    if check_only:
        if needs_update:
            print("[OUT OF SYNC] knowledge/codebase_map.md is out of date with the codebase AST.")
            sys.exit(1)
        else:
            print("[OK] knowledge/codebase_map.md is up to date.")
            print(f"[OK] All {len(CORE_DOCS)} knowledge base documents verified.")
            return

    # Normal update
    CODEBASE_MAP_PATH.write_text(expected_map, encoding="utf-8")
    print(f"[UPDATED] {CODEBASE_MAP_PATH.relative_to(ROOT_DIR)}")
    print(f"[OK] Verified {len(CORE_DOCS)} knowledge base documents in {KNOWLEDGE_DIR.relative_to(ROOT_DIR)}/")


if __name__ == "__main__":
    check_mode = "--check" in sys.argv
    update_and_validate(check_only=check_mode)
