"""Utilities for working with DOCX documents without external dependencies.

The original implementation relied on the ``python-docx`` and ``docxtpl``
packages.  Those libraries are not available inside the execution sandbox used
for the automated tests, so we provide a very small subset of the
functionality we need by manipulating the Office Open XML files directly.  A
DOCX file is just a ZIP archive with a handful of XML files inside.  We only
need two capabilities:

* Extract plain text from an uploaded resume for indexing in the database.
* Render a simple resume document with headings and paragraph text for the
  tailored artifact output.

The helpers below keep the XML markup intentionally small.  The generated
documents are compatible with common word processors because they follow the
same minimal structure used in the unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZipInfo


_WORD_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_NS = {"w": _WORD_NAMESPACE}


def extract_docx_text(path: Path) -> str:
    """Return the newline separated text content of a DOCX document."""

    with ZipFile(path) as archive:
        xml = archive.read("word/document.xml")

    root = ET.fromstring(xml)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", _NS):
        texts = [node.text or "" for node in paragraph.findall(".//w:t", _NS)]
        if texts:
            paragraphs.append("".join(texts))
    return "\n".join(part.strip() for part in paragraphs if part.strip())


def create_placeholder_template(path: Path) -> None:
    """Create a very small DOCX template with placeholder tokens."""

    if path.exists():
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    paragraphs = [
        "Summary",
        "{{ summary }}",
        "Skills",
        "{{ skills }}",
        "Experience",
        "{{ experience }}",
        "Education",
        "{{ education }}",
        "Certifications",
        "{{ certifications }}",
    ]
    _write_docx(path, paragraphs)


@dataclass
class RenderContext:
    """Structured resume data used to build the artifact output."""

    summary: str
    skills: Iterable[str]
    experience: Iterable[str]
    education: Iterable[str]
    certifications: Iterable[str]

    def iter_paragraphs(self) -> Iterable[str]:
        yield "Summary"
        yield from _split_lines(self.summary)
        yield "Skills"
        yield from (f"- {skill}" for skill in self.skills)
        yield "Experience"
        for block in self.experience:
            yield from _split_lines(block)
        yield "Education"
        yield from _split_lines("\n".join(self.education))
        yield "Certifications"
        yield from _split_lines("\n".join(self.certifications))


def render_resume_docx(path: Path, context: RenderContext) -> None:
    """Render the resume artifact as a DOCX file using the provided context."""

    paragraphs = [para for para in context.iter_paragraphs() if para]
    _write_docx(path, paragraphs)


def _split_lines(text: str) -> Iterable[str]:
    for line in (text or "").splitlines():
        cleaned = line.strip()
        if cleaned:
            yield cleaned


def _write_docx(path: Path, paragraphs: Iterable[str]) -> None:
    """Write a minimal DOCX file with the supplied paragraphs."""

    paragraphs = list(paragraphs)
    document_xml = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        f"<w:document xmlns:w='{_WORD_NAMESPACE}'>",
        "  <w:body>",
    ]
    for paragraph in paragraphs:
        document_xml.append(_paragraph_xml(paragraph))
    document_xml.append("  </w:body>")
    document_xml.append("</w:document>")
    document_bytes = "\n".join(document_xml).encode("utf-8")

    with ZipFile(path, "w") as archive:
        archive.writestr(
            ZipInfo("[Content_Types].xml"),
            """<?xml version='1.0' encoding='UTF-8'?>
<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'>
  <Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/>
  <Default Extension='xml' ContentType='application/xml'/>
  <Override PartName='/word/document.xml' ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'/>
</Types>
""",
        )
        archive.writestr(
            ZipInfo("_rels/.rels"),
            """<?xml version='1.0' encoding='UTF-8'?>
<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>
  <Relationship Id='R1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument' Target='word/document.xml'/>
</Relationships>
""",
        )
        archive.writestr(
            ZipInfo("word/_rels/document.xml.rels"),
            """<?xml version='1.0' encoding='UTF-8'?>
<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>
</Relationships>
""",
        )
        archive.writestr(
            ZipInfo("word/styles.xml"),
            """<?xml version='1.0' encoding='UTF-8'?>
<w:styles xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>
  <w:style w:type='paragraph' w:default='1' w:styleId='Normal'>
    <w:name w:val='Normal'/>
  </w:style>
</w:styles>
""",
        )
        archive.writestr(ZipInfo("word/document.xml"), document_bytes)


def _paragraph_xml(text: str) -> str:
    if not text:
        return "  <w:p/>"
    text = escape(text)
    return f"  <w:p><w:r><w:t xml:space='preserve'>{text}</w:t></w:r></w:p>"

