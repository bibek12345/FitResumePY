from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models


def get_or_create_company(session: Session, name: str) -> models.Company:
    stmt = select(models.Company).where(models.Company.name == name)
    company = session.execute(stmt).scalar_one_or_none()
    if company:
        return company
    company = models.Company(name=name)
    session.add(company)
    session.flush()
    return company


def create_job_posting(
    session: Session,
    *,
    title: str,
    company: Optional[models.Company],
    location: Optional[str],
    url: Optional[str],
    raw_text: Optional[str],
    external_id: Optional[str],
) -> models.JobPosting:
    job = models.JobPosting(
        title=title,
        company=company,
        location=location,
        url=url,
        raw_text=raw_text,
        external_id=external_id,
        url_hash=sha256((url or raw_text or title).encode("utf-8", "ignore")).hexdigest(),
    )
    session.add(job)
    session.flush()
    return job


def list_job_postings(session: Session) -> List[models.JobPosting]:
    return list(session.scalars(select(models.JobPosting).order_by(models.JobPosting.id.desc())))


def create_resume(
    session: Session,
    *,
    file_path: str,
    file_format: str,
    text: Optional[str],
    text_hash: Optional[str],
) -> models.Resume:
    resume = models.Resume(
        file_path=file_path,
        format=file_format,
        text=text,
        text_hash=text_hash,
    )
    session.add(resume)
    session.flush()
    return resume


def list_resumes(session: Session) -> List[models.Resume]:
    return list(session.scalars(select(models.Resume).order_by(models.Resume.created_at.desc())))


def get_resume(session: Session, resume_id: int) -> Optional[models.Resume]:
    return session.get(models.Resume, resume_id)


def get_job_posting(session: Session, job_id: int) -> Optional[models.JobPosting]:
    return session.get(models.JobPosting, job_id)


def create_resume_version(
    session: Session,
    *,
    resume: models.Resume,
    job_posting: models.JobPosting,
    file_path: str,
    template_version: str,
    model_name: str,
    prompt_hash: str,
    token_usage: Optional[dict],
) -> models.ResumeVersion:
    version = models.ResumeVersion(
        resume=resume,
        job_posting=job_posting,
        file_path=file_path,
        base_resume_hash=resume.text_hash,
        job_hash=sha256((job_posting.raw_text or job_posting.title).encode("utf-8", "ignore")).hexdigest(),
        input_signature=sha256(f"{resume.id}:{job_posting.id}".encode()).hexdigest(),
        template_version=template_version,
        model_name=model_name,
        prompt_hash=prompt_hash,
        token_usage=token_usage,
    )
    session.add(version)
    session.flush()
    return version


def create_run(
    session: Session,
    *,
    triggered_by: str,
    run_type: str,
) -> models.Run:
    run = models.Run(triggered_by=triggered_by, type=run_type, status="running", started_at=datetime.utcnow())
    session.add(run)
    session.flush()
    return run


def finish_run(
    session: Session, run: models.Run, *, status: str, error: Optional[str] = None
) -> models.Run:
    run.status = status
    run.error = error
    run.finished_at = datetime.utcnow()
    session.add(run)
    session.flush()
    return run


def create_schedule(
    session: Session,
    *,
    cron_expr: str,
    is_enabled: bool,
    criteria_json: Optional[dict],
) -> models.Schedule:
    schedule = models.Schedule(
        cron_expr=cron_expr, is_enabled=is_enabled, criteria_json=criteria_json
    )
    session.add(schedule)
    session.flush()
    return schedule


def list_schedules(session: Session) -> List[models.Schedule]:
    return list(session.scalars(select(models.Schedule)))


def get_schedule(session: Session, schedule_id: int) -> Optional[models.Schedule]:
    return session.get(models.Schedule, schedule_id)


def record_token_usage(total_tokens: int, prompt_tokens: int, completion_tokens: int) -> dict:
    return {
        "total_tokens": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }


def list_runs(session: Session) -> List[models.Run]:
    return list(
        session.scalars(select(models.Run).order_by(models.Run.started_at.desc()))
    )
