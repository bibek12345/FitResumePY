from __future__ import annotations

import structlog
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .. import crud
from ..db import session_scope
from .artifact_service import ArtifactService
from .rewrite_service import get_rewrite_service

logger = structlog.get_logger(__name__)


class SchedulerService:
    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler()
        self.rewrite_service = get_rewrite_service()
        self.artifact_service = ArtifactService()
        self.started = False

    def start(self) -> None:
        if not self.started:
            self.scheduler.start()
            self.started = True
            logger.info("scheduler_started")

    def shutdown(self) -> None:
        if self.started:
            self.scheduler.shutdown(wait=False)
            self.started = False
            logger.info("scheduler_stopped")

    def sync_schedules(self) -> None:
        with session_scope() as session:
            schedules = crud.list_schedules(session)
            for schedule in schedules:
                self._register_schedule(schedule.id, schedule.cron_expr, schedule.is_enabled)

    def run_now(self, schedule_id: int) -> None:
        self._run_schedule(schedule_id)

    def _register_schedule(self, schedule_id: int, cron_expr: str, enabled: bool) -> None:
        job_id = f"schedule-{schedule_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        if not enabled:
            logger.info("schedule_disabled", schedule_id=schedule_id)
            return
        trigger = CronTrigger.from_crontab(cron_expr)
        self.scheduler.add_job(self._run_schedule, trigger=trigger, id=job_id, args=[schedule_id])
        logger.info("schedule_registered", schedule_id=schedule_id, cron=cron_expr)

    def _run_schedule(self, schedule_id: int) -> None:
        logger.info("schedule_trigger", schedule_id=schedule_id)
        with session_scope() as session:
            schedule = crud.get_schedule(session, schedule_id)
            if not schedule:
                logger.warning("schedule_missing", schedule_id=schedule_id)
                return
            run = crud.create_run(session, triggered_by="scheduler", run_type="scheduled")
            try:
                resume = next(iter(crud.list_resumes(session)), None)
                job = next(iter(crud.list_job_postings(session)), None)
                if not resume or not job:
                    crud.finish_run(session, run, status="skipped", error="No resumes or job postings available")
                    logger.info("schedule_skipped", schedule_id=schedule_id)
                    return
                rewrite_result = self.rewrite_service.rewrite(resume.text or "", job.raw_text or job.title)
                artifact_path = self.artifact_service.create_artifact(
                    company_name=job.company.name if job.company else "Unknown",
                    job_key=f"{job.id}_{job.title}",
                    rewrite_result=rewrite_result,
                )
                crud.create_resume_version(
                    session,
                    resume=resume,
                    job_posting=job,
                    file_path=str(artifact_path),
                    template_version=self.artifact_service.TEMPLATE_VERSION,
                    model_name=rewrite_result.model_name,
                    prompt_hash=rewrite_result.prompt_hash,
                    token_usage=rewrite_result.token_usage,
                )
                crud.finish_run(session, run, status="success")
                logger.info("schedule_completed", schedule_id=schedule_id, artifact=str(artifact_path))
            except Exception as exc:  # pragma: no cover - scheduler runtime
                crud.finish_run(session, run, status="failed", error=str(exc))
                logger.error("schedule_error", schedule_id=schedule_id, error=str(exc))


scheduler_service = SchedulerService()
