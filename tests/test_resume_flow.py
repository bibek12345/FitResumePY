import os
from pathlib import Path
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("fitresume")
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_dir}/test.db"
    os.environ["ARTIFACTS_ROOT"] = str(tmp_dir / "artifacts")

    import backend.config as config

    config.get_settings.cache_clear()  # type: ignore[attr-defined]

    import backend.main as main

    with TestClient(main.app) as test_client:
        yield test_client


def create_sample_docx(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w") as docx:
        docx.writestr(
            "[Content_Types].xml",
            """<?xml version='1.0' encoding='UTF-8'?>
<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'>
  <Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/>
  <Default Extension='xml' ContentType='application/xml'/>
  <Override PartName='/word/document.xml' ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'/>
</Types>
""",
        )
        docx.writestr(
            "_rels/.rels",
            """<?xml version='1.0' encoding='UTF-8'?>
<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>
  <Relationship Id='R1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument' Target='word/document.xml'/>
</Relationships>
""",
        )
        docx.writestr(
            "word/_rels/document.xml.rels",
            """<?xml version='1.0' encoding='UTF-8'?>
<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>
</Relationships>
""",
        )
        docx.writestr(
            "word/styles.xml",
            """<?xml version='1.0' encoding='UTF-8'?>
<w:styles xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>
  <w:style w:type='paragraph' w:default='1' w:styleId='Normal'>
    <w:name w:val='Normal'/>
  </w:style>
</w:styles>
""",
        )
        docx.writestr(
            "word/document.xml",
            """<?xml version='1.0' encoding='UTF-8'?>
<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>
  <w:body>
    <w:p><w:r><w:t>John Doe</w:t></w:r></w:p>
    <w:p><w:r><w:t>Experienced data analyst with Python skills.</w:t></w:r></w:p>
  </w:body>
</w:document>
""",
        )


def test_resume_tailoring_flow(client, tmp_path):
    resume_path = tmp_path / "sample.docx"
    create_sample_docx(resume_path)

    with resume_path.open("rb") as file_obj:
        response = client.post(
            "/api/resumes",
            files={
                "file": (
                    "sample.docx",
                    file_obj,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
    assert response.status_code == 200
    resume_data = response.json()

    job_payload = {
        "title": "Data Scientist",
        "company_name": "Acme Corp",
        "raw_text": "We are looking for data scientists with Python expertise.",
    }
    job_response = client.post("/api/job_postings", json=job_payload)
    assert job_response.status_code == 200
    job_data = job_response.json()

    tailor_response = client.post(
        "/api/tailor",
        json={
            "resume_id": resume_data["id"],
            "job_posting_id": job_data["id"],
        },
    )
    assert tailor_response.status_code == 200
    payload = tailor_response.json()
    assert payload["mock"] is True

    artifact_path = Path(payload["artifact_path"])
    assert artifact_path.exists()
    meta_path = artifact_path.parent / "meta.json"
    assert meta_path.exists()
