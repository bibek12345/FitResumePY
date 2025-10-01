from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Tuple

from docx import Document
from pypdf import PdfReader


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
        document = Document(file_path)
        text = "\n".join(paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text)
    except Exception as exc:  # pragma: no cover - python-docx errors
        raise ResumeExtractionError(f"Unable to parse DOCX: {exc}") from exc
    return text, _hash_text(text)


def _extract_pdf(file_path: Path) -> Tuple[str, str]:
    try:
        reader = PdfReader(str(file_path))
        lines = []
        for page in reader.pages:
            lines.append(page.extract_text() or "")
        text = "\n".join(lines)
    except Exception as exc:  # pragma: no cover - pdf parser errors
        raise ResumeExtractionError(f"Unable to parse PDF: {exc}") from exc
    return text, _hash_text(text)
