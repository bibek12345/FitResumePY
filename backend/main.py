from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import structlog
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from nicegui import app as nicegui_app

from . import crud, schemas
from .config import get_settings
from .db import Base, engine, session_scope
from .services import app_service
from .services.resume_extraction import ResumeExtractionError
from .services.scheduler_service import scheduler_service
from ui.pages import artifacts as artifacts_page  # noqa: F401
from ui.pages import dashboard  # noqa: F401
from ui.pages import job_board  # noqa: F401
from ui.pages import resume_manager  # noqa: F401
from ui.pages import runs as runs_page  # noqa: F401
from ui.pages import scheduler as scheduler_page  # noqa: F401


logging.basicConfig(level=logging.INFO)
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.EventRenamer("event"),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger(__name__)


Base.metadata.create_all(engine)

app: FastAPI = nicegui_app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    scheduler_service.start()
    scheduler_service.sync_schedules()
    logger.info("startup_complete")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    scheduler_service.shutdown()
    logger.info("shutdown_complete")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/resumes", response_model=schemas.Resume)
async def upload_resume(file: UploadFile = File(...)) -> schemas.Resume:
    content = await file.read()
    try:
        resume = app_service.save_resume_file(file.filename, content)
    except ResumeExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return schemas.Resume.from_orm(resume)


@app.get("/api/resumes", response_model=List[schemas.Resume])
async def list_resumes() -> List[schemas.Resume]:
    with session_scope() as session:
        resumes = crud.list_resumes(session)
        return [schemas.Resume.from_orm(resume) for resume in resumes]


@app.post("/api/job_postings", response_model=schemas.JobPosting)
async def create_job_posting(payload: schemas.JobPostingCreate) -> schemas.JobPosting:
    job = app_service.create_job_posting(payload)
    return schemas.JobPosting.from_orm(job)


@app.get("/api/job_postings", response_model=List[schemas.JobPosting])
async def list_job_postings() -> List[schemas.JobPosting]:
    with session_scope() as session:
        jobs = crud.list_job_postings(session)
        return [schemas.JobPosting.from_orm(job) for job in jobs]


@app.post("/api/job_postings/upload_csv", response_model=schemas.UploadJobCSVResponse)
async def upload_job_csv(file: UploadFile = File(...)) -> schemas.UploadJobCSVResponse:
    content = await file.read()
    ids = app_service.import_jobs_from_csv(content)
    return schemas.UploadJobCSVResponse(created_ids=ids)


@app.post("/api/tailor", response_model=schemas.TailorResponse)
async def tailor_resume(request: schemas.TailorRequest) -> schemas.TailorResponse:
    try:
        version, artifact_path, mock = app_service.tailor_resume(request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    response = schemas.TailorResponse(
        resume_version_id=version.id,
        artifact_path=str(artifact_path),
        mock=mock,
    )
    return response


@app.get("/api/runs", response_model=List[schemas.Run])
async def list_runs() -> List[schemas.Run]:
    with session_scope() as session:
        runs = crud.list_runs(session)
        return [schemas.Run.from_orm(run) for run in runs]


@app.post("/api/schedules", response_model=schemas.Schedule)
async def create_schedule(payload: schemas.ScheduleCreate) -> schemas.Schedule:
    schedule = app_service.create_schedule(payload)
    scheduler_service.sync_schedules()
    return schemas.Schedule.from_orm(schedule)


@app.get("/api/schedules", response_model=List[schemas.Schedule])
async def list_schedules() -> List[schemas.Schedule]:
    with session_scope() as session:
        schedules = crud.list_schedules(session)
        return [schemas.Schedule.from_orm(schedule) for schedule in schedules]


@app.post("/api/schedules/{schedule_id}/trigger")
async def trigger_schedule(schedule_id: int) -> dict[str, str]:
    scheduler_service.run_now(schedule_id)
    return {"status": "triggered"}


@app.get("/api/artifacts/download")
async def download_artifact(path: str):
    artifacts_root = get_settings().artifacts_root.resolve()
    target = Path(path).resolve()
    if not target.exists() or not str(target).startswith(str(artifacts_root)):
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(target)
