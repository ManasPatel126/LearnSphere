"""
Handles multipart file uploads for Phase 1.
Saves files to UPLOAD_DIR, validates type and size,
returns an UploadedFile schema object.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from models.schemas import UploadedFile

_ALLOWED_EXTENSIONS = {"pdf", "txt", "md", "rst"}
_MAX_SIZE_BYTES     = 10 * 1024 * 1024   # 10 MB
_UPLOAD_DIR         = Path(os.getenv("UPLOAD_DIR", "/tmp/phase1_uploads"))


def _ensure_upload_dir() -> None:
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in _ALLOWED_EXTENSIONS


def save_upload(file: FileStorage) -> UploadedFile:
    """
    Validate and persist an uploaded file.
    Returns an UploadedFile metadata object (no text extraction here).

    Raises:
        ValueError  — bad type or oversized
    """
    _ensure_upload_dir()

    original_name = file.filename or "unnamed"
    if not _allowed(original_name):
        raise ValueError(
            f"File type not allowed. Accepted: {', '.join(_ALLOWED_EXTENSIONS)}"
        )

    # Read into memory to check size before writing
    data = file.read()
    if len(data) > _MAX_SIZE_BYTES:
        raise ValueError(
            f"File too large ({len(data) // 1024} KB). Max is "
            f"{_MAX_SIZE_BYTES // 1024 // 1024} MB."
        )

    safe_name    = secure_filename(original_name)
    unique_name  = f"{uuid.uuid4().hex}_{safe_name}"
    dest         = _UPLOAD_DIR / unique_name

    dest.write_bytes(data)

    return UploadedFile(
        filename=original_name,
        storage_path=str(dest),
        size_bytes=len(data),
    )
