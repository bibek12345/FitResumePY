from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from docx import Document
from docxtpl import DocxTemplate

from ..config import get_settings
from .rewrite_service import RewriteResult


class ArtifactService:
    TEMPLATE_VERSION = "1.0"

    def __init__(self, artifacts_root: Path | None = None, template_path: Path | None = None) -> None:
        settings = get_settings()
        self.artifacts_root = artifacts_root or settings.artifacts_root
        self.template_path = template_path or Path("templates/resume_template.docx").resolve()
        self._ensure_template_exists()

    def create_artifact(
        self,
        *,
        company_name: str,
        job_key: str,
        rewrite_result: RewriteResult,
    ) -> Path:
        folder = self._resolve_folder(company_name, job_key)
        folder.mkdir(parents=True, exist_ok=True)
        filename = f"resume_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.docx"
        artifact_path = folder / filename

        template = DocxTemplate(str(self.template_path))
        context = self._build_context(rewrite_result)
        template.render(context)
        template.save(str(artifact_path))

        meta_path = folder / "meta.json"
        meta_payload = {
            "company": company_name,
            "job_key": job_key,
            "artifact": artifact_path.name,
            "created_at": datetime.utcnow().isoformat(),
            "template_version": self.TEMPLATE_VERSION,
            "model_name": rewrite_result.model_name,
            "prompt_hash": rewrite_result.prompt_hash,
            "plan": rewrite_result.plan,
            "mock_output": rewrite_result.mock,
        }
        if rewrite_result.token_usage:
            meta_payload["token_usage"] = rewrite_result.token_usage
        meta_path.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")
        return artifact_path

    def _resolve_folder(self, company_name: str, job_key: str) -> Path:
        folder_name = f"{self._sanitize(company_name)}__{self._sanitize(job_key)}"
        return self.artifacts_root / folder_name

    def _sanitize(self, value: str) -> str:
        return re.sub(r"[^A-Za-z0-9_-]", "_", value.strip() or "job")[:60]

    def _build_context(self, rewrite_result: RewriteResult) -> Dict[str, Any]:
        plan = rewrite_result.plan
        skills = plan.get("skills", [])
        experience_lines = []
        for exp in plan.get("experience", []):
            bullets = exp.get("bullets", [])
            bullet_lines = "\n".join(f"- {bullet}" for bullet in bullets)
            line = f"{exp.get('employer', '')} — {exp.get('role', '')} ({exp.get('start', '')} - {exp.get('end', '')})"
            if bullet_lines:
                line += f"\n{bullet_lines}"
            experience_lines.append(line.strip())
        context = {
            "summary": plan.get("summary", ""),
            "skills": "\n".join(f"- {skill}" for skill in skills) if skills else "",
            "experience": "\n\n".join(experience_lines),
            "education": "\n".join(plan.get("education", [])),
            "certifications": "\n".join(plan.get("certifications", [])),
        }
        return context

    def _ensure_template_exists(self) -> None:
        if self.template_path.exists():
            return

        self.template_path.parent.mkdir(parents=True, exist_ok=True)

        document = Document()
        document.add_heading("Summary", level=1)
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
