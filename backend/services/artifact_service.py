"""Services for generating resume artifacts from templates."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from docxtpl import DocxTemplate
from docx import Document


class ArtifactService:
    """Service responsible for rendering DOCX resume artifacts."""

    def __init__(self, template_path: str | Path | None = None) -> None:
        self.template_path = Path(template_path or "templates/resume_template.docx")
        self._ensure_template_exists()

    def _ensure_template_exists(self) -> None:
        """Create the DOCX template if it is missing from disk.

        The project historically stored a binary template in version control.
        This helper recreates the template at runtime when it is not present so
        artifact generation can continue without shipping binary assets.
        """

        if self.template_path.exists():
            return

        self.template_path.parent.mkdir(parents=True, exist_ok=True)

        document = Document()
        document.add_heading("Professional Summary", level=1)
        document.add_paragraph("{{ summary }}")

        document.add_heading("Skills", level=1)
        document.add_paragraph("{{ skills }}")

        document.add_heading("Experience", level=1)
        document.add_paragraph("{{ experience }}")

        document.add_heading("Education", level=1)
        document.add_paragraph("{{ education }}")

        document.add_heading("Certifications", level=1)
        document.add_paragraph("{{ certifications }}")

        document.save(self.template_path)

    def render_artifact(
        self, context: Mapping[str, Any], destination: str | Path
    ) -> Path:
        """Render the resume artifact into ``destination`` using the template.

        Parameters
        ----------
        context:
            A mapping with the keys expected by the template (``summary``,
            ``skills``, ``experience``, ``education``, ``certifications``).
        destination:
            Where the rendered document should be written.
        """

        template = DocxTemplate(str(self.template_path))
        template.render(dict(context))

        destination_path = Path(destination)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        template.save(str(destination_path))
        return destination_path
