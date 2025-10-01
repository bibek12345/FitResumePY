from __future__ import annotations

import csv
import io
from pathlib import Path
from .. import crud
from ..db import session_scope
from ..schemas import JobPostingCreate, ScheduleCreate, TailorRequest
from .artifact_service import ArtifactService
from .resume_extraction import extract_text
from .rewrite_service import get_rewrite_service

UPLOAD_ROOT = Path("uploads/resumes")
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)


def save_resume_file(filename: str, content: bytes):
    upload_path = UPLOAD_ROOT / filename
    counter = 1
    while upload_path.exists():
        upload_path = UPLOAD_ROOT / f"{upload_path.stem}_{counter}{upload_path.suffix}"
        counter += 1
    upload_path.write_bytes(content)
    text, text_hash = extract_text(upload_path)
    with session_scope() as connection:
        resume = crud.create_resume(
            connection,
            file_path=str(upload_path),
            file_format=upload_path.suffix.lstrip("."),
            text=text,
            text_hash=text_hash,
        )
        return resume


def create_job_posting(payload: JobPostingCreate):
    with session_scope() as connection:
        company = None
        if payload.company_name:
            company = crud.get_or_create_company(connection, payload.company_name)
        job = crud.create_job_posting(
            connection,
            title=payload.title,
            company=company,
            location=payload.location,
            url=payload.url,
            raw_text=payload.raw_text,
            external_id=payload.external_id,
        )
        return job


def tailor_resume(request: TailorRequest):
    with session_scope() as connection:
        resume = crud.get_resume(connection, request.resume_id)
        job = crud.get_job_posting(connection, request.job_posting_id)
        if not resume or not job:
            raise ValueError("Resume or job posting not found")
        service = get_rewrite_service()
        rewrite_result = service.rewrite(resume.text or "", job.raw_text or job.title)
        artifact_service = ArtifactService()
        artifact_path = artifact_service.create_artifact(
            company_name=job.company.name if job.company else "Unknown",
            job_key=f"{job.id}_{job.title}",
            rewrite_result=rewrite_result,
        )
        version = crud.create_resume_version(
            connection,
            resume=resume,
            job_posting=job,
            file_path=str(artifact_path),
            template_version=artifact_service.TEMPLATE_VERSION,
            model_name=rewrite_result.model_name,
            prompt_hash=rewrite_result.prompt_hash,
            token_usage=rewrite_result.token_usage,
        )
        return version, artifact_path, rewrite_result.mock


def import_jobs_from_csv(content: bytes | str) -> list[int]:
    if isinstance(content, bytes):
        text = content.decode("utf-8")
    else:
        text = content
    reader = csv.DictReader(io.StringIO(text))
    created_ids: list[int] = []
    with session_scope() as connection:
        for row in reader:
            title = row.get("title")
            if not title:
                continue
            company = None
            company_name = row.get("company")
            if company_name:
                company = crud.get_or_create_company(connection, company_name)
            job = crud.create_job_posting(
                connection,
                title=title,
                company=company,
                location=row.get("location"),
                url=row.get("url"),
                raw_text=row.get("description") or row.get("raw_text"),
                external_id=row.get("external_id"),
            )
            created_ids.append(job.id)
    return created_ids


def create_schedule(payload: ScheduleCreate):
    with session_scope() as connection:
        schedule = crud.create_schedule(
            connection,
            cron_expr=payload.cron_expr,
            is_enabled=payload.is_enabled,
            criteria_json=payload.criteria_json,
        )
        return schedule
