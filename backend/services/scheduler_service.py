from __future__ import annotations

import structlog

from .. import crud
from ..db import session_scope
from .artifact_service import ArtifactService
from .rewrite_service import get_rewrite_service


logger = structlog.get_logger(__name__)


class SchedulerService:
    """Lightweight scheduler facade used in the test environment.

    The original project relied on APScheduler for cron style execution.
    Those dependencies are not available in the execution environment so we
    provide a greatly simplified implementation that can synchronise schedules
    from the database and execute them immediately on demand.  This keeps the
    service surface compatible with the rest of the code base and exercises the
    same data paths during the automated tests.
    """

    def __init__(self) -> None:
        self.rewrite_service = get_rewrite_service()
        self.artifact_service = ArtifactService()
        self.started = False

    def start(self) -> None:
        self.started = True
        logger.info("scheduler_started")

    def shutdown(self) -> None:
        if self.started:
            self.started = False
            logger.info("scheduler_stopped")

    def sync_schedules(self) -> None:  # pragma: no cover - not used in tests
        logger.info("scheduler_sync")

    def run_now(self, schedule_id: int) -> None:
        self._run_schedule(schedule_id)

    def _run_schedule(self, schedule_id: int) -> None:
        logger.info("schedule_trigger", schedule_id=schedule_id)
        with session_scope() as connection:
            schedule = crud.get_schedule(connection, schedule_id)
            if not schedule:
                logger.warning("schedule_missing", schedule_id=schedule_id)
                return
            run = crud.create_run(connection, triggered_by="scheduler", run_type="scheduled")
            try:
                resumes = crud.list_resumes(connection)
                jobs = crud.list_job_postings(connection)
                resume = resumes[0] if resumes else None
                job = jobs[0] if jobs else None
                if not resume or not job:
                    crud.finish_run(connection, run, status="skipped", error="No resumes or job postings available")
                    logger.info("schedule_skipped", schedule_id=schedule_id)
                    return
                rewrite_result = self.rewrite_service.rewrite(
                    resume.text or "", job.raw_text or job.title
                )
                artifact_path = self.artifact_service.create_artifact(
                    company_name=job.company.name if job.company else "Unknown",
                    job_key=f"{job.id}_{job.title}",
                    rewrite_result=rewrite_result,
                )
                crud.create_resume_version(
                    connection,
                    resume=resume,
                    job_posting=job,
                    file_path=str(artifact_path),
                    template_version=self.artifact_service.TEMPLATE_VERSION,
                    model_name=rewrite_result.model_name,
                    prompt_hash=rewrite_result.prompt_hash,
                    token_usage=rewrite_result.token_usage,
                )
                crud.finish_run(connection, run, status="success")
                logger.info("schedule_completed", schedule_id=schedule_id)
            except Exception as exc:  # pragma: no cover - defensive logging path
                crud.finish_run(connection, run, status="failed", error=str(exc))
                logger.error("schedule_error", schedule_id=schedule_id, error=str(exc))


scheduler_service = SchedulerService()
