from __future__ import annotations

import json
from typing import List

from backend import crud
from backend.db import session_scope
from backend.schemas import JobPostingCreate, ScheduleCreate, TailorRequest
from backend.services.app_service import create_job_posting as service_create_job_posting
from backend.services.app_service import (
    create_schedule as service_create_schedule,
    import_jobs_from_csv as service_import_jobs_from_csv,
    save_resume_file,
    tailor_resume as service_tailor_resume,
)
from backend.services.artifact_service import ArtifactService
from backend.services.scheduler_service import scheduler_service


def get_counts() -> dict[str, int]:
    with session_scope() as session:
        resumes = len(crud.list_resumes(session))
        jobs = len(crud.list_job_postings(session))
        schedules = len(crud.list_schedules(session))
    artifacts = sum(1 for _ in ArtifactService().artifacts_root.glob("*/*.docx"))
    return {
        "Resumes": resumes,
        "Job Postings": jobs,
        "Artifacts": artifacts,
        "Schedules": schedules,
    }


def get_recent_runs(limit: int = 5) -> List[str]:
    with session_scope() as session:
        runs = crud.list_runs(session)
        return [
            f"{run.started_at:%Y-%m-%d %H:%M} — {run.type or 'manual'} ({run.status or 'pending'})"
            for run in runs[:limit]
        ]


def list_resumes():
    with session_scope() as session:
        return crud.list_resumes(session)


def list_job_postings():
    with session_scope() as session:
        return crud.list_job_postings(session)


def list_runs():
    with session_scope() as session:
        return crud.list_runs(session)


def list_schedules():
    with session_scope() as session:
        return crud.list_schedules(session)


def upload_resume(filename: str, content: bytes):
    return save_resume_file(filename, content)


def tailor_resume(resume_id: int, job_id: int):
    request = TailorRequest(resume_id=resume_id, job_posting_id=job_id)
    return service_tailor_resume(request)


def create_job_posting(payload: JobPostingCreate | dict):
    if not isinstance(payload, JobPostingCreate):
        payload = JobPostingCreate(**payload)
    return service_create_job_posting(payload)


def create_schedule(payload: ScheduleCreate | dict):
    if not isinstance(payload, ScheduleCreate):
        payload = ScheduleCreate(**payload)
    schedule = service_create_schedule(payload)
    scheduler_service.sync_schedules()
    return schedule


def import_jobs_from_csv(file) -> List[int]:
    if hasattr(file, "read"):
        raw = file.read()
    else:
        raw = file
    return service_import_jobs_from_csv(raw)


def list_artifacts() -> List[dict]:
    root = ArtifactService().artifacts_root
    artifacts = []
    for directory in sorted(root.glob("*")):
        if directory.is_dir():
            for docx_path in directory.glob("*.docx"):
                meta = directory / "meta.json"
                meta_data = {}
                if meta.exists():
                    try:
                        meta_data = json.loads(meta.read_text(encoding="utf-8"))
                    except Exception:
                        meta_data = {}
                artifacts.append(
                    {
                        "folder": directory.name,
                        "file": docx_path.name,
                        "path": str(docx_path),
                        "meta": meta_data,
                    }
                )
    return artifacts


def trigger_schedule(schedule_id: int) -> None:
    scheduler_service.run_now(schedule_id)


def sync_scheduler() -> None:
    scheduler_service.sync_schedules()
