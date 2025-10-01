from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.artifact_service import ArtifactService

DocxTemplate = pytest.importorskip("docxtpl").DocxTemplate


def test_template_created_when_missing(tmp_path):
    template_path = tmp_path / "templates" / "resume_template.docx"

    service = ArtifactService(template_path=template_path)

    assert template_path.exists(), "Template should be created automatically"

    doc = DocxTemplate(template_path)
    # Rendering should succeed with the expected placeholders present.
    context = {
        "summary": "Experienced professional",
        "skills": "Python, Data Analysis",
        "experience": "Company XYZ",
        "education": "BS in Computer Science",
        "certifications": "AWS Certified",
    }
    doc.render(context)

    output_path = tmp_path / "artifacts" / "resume.docx"
    rendered_path = service.render_artifact(context, output_path)

    assert rendered_path == output_path
    assert rendered_path.exists(), "Rendered artifact should be written to disk"
