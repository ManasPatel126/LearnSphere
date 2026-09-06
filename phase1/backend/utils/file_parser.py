"""
File parser for Phase 1.
Supports: PDF (via pdfplumber), plain text, markdown.
Returns raw extracted text that is fed into the Gemini prompt.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

# pdfplumber is much more reliable than PyPDF2 for real-world PDFs
try:
    import pdfplumber
    _PDFPLUMBER_OK = True
except ImportError:
    _PDFPLUMBER_OK = False

_MAX_CHARS = 20_000   # clip text sent to Gemini to avoid token overflow


def extract_text(filepath: str | Path) -> tuple[str, int]:
    """
    Extract text from a file.

    Returns:
        (extracted_text, page_count)
        page_count is 0 for non-PDF files.

    Raises:
        ValueError  — unsupported file type
        IOError     — file not readable
    """
    path = Path(filepath)
    if not path.exists():
        raise IOError(f"File not found: {filepath}")

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(path)
    elif suffix in {".txt", ".md", ".rst"}:
        return _extract_text_file(path)
    else:
        raise ValueError(
            f"Unsupported file type: {suffix}. "
            f"Accepted: .pdf, .txt, .md, .rst"
        )


def _extract_pdf(path: Path) -> tuple[str, int]:
    if not _PDFPLUMBER_OK:
        raise ImportError(
            "pdfplumber is not installed. Run: pip install pdfplumber"
        )

    pages_text = []
    page_count = 0

    with pdfplumber.open(path) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

    full_text = "\n\n".join(pages_text)
    return full_text[:_MAX_CHARS], page_count


def _extract_text_file(path: Path) -> tuple[str, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:_MAX_CHARS], 0


def safe_extract(filepath: str | Path) -> Optional[str]:
    """
    Non-raising wrapper — returns None on any error.
    Use this in RQ tasks where you don't want file errors to kill the whole job.
    """
    try:
        text, _ = extract_text(filepath)
        return text
    except Exception as exc:
        print(f"[file_parser] WARNING: could not extract {filepath}: {exc}")
        return None
