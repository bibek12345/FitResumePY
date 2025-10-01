from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Tuple

from ..utils.docx_utils import extract_docx_text


class ResumeExtractionError(RuntimeError):
    pass


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()


def extract_text(file_path: Path) -> Tuple[str, str]:
    suffix = file_path.suffix.lower()
    if suffix == ".docx":
        return _extract_docx(file_path)
    if suffix == ".pdf":
        return _extract_pdf(file_path)
    raise ResumeExtractionError(f"Unsupported resume format: {suffix}")


def _extract_docx(file_path: Path) -> Tuple[str, str]:
    try:
        text = extract_docx_text(file_path)
    except Exception as exc:  # pragma: no cover - docx parsing edge cases
        raise ResumeExtractionError(f"Unable to parse DOCX: {exc}") from exc
    return text, _hash_text(text)


def _extract_pdf(file_path: Path) -> Tuple[str, str]:
    raise ResumeExtractionError(
        "PDF extraction requires the optional 'pypdf' dependency which is not available in this environment."
    )
