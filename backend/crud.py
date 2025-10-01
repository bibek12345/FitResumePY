from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256
from typing import Optional

from . import models


def _parse_datetime(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value)
    if "T" not in text and " " in text:
        text = text.replace(" ", "T")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _row_to_company(row) -> models.Company:
    return models.Company(
        id=row["id"],
        name=row["name"],
        aliases=row["aliases"],
        logo_url=row["logo_url"],
    )


def _row_to_job(row) -> models.JobPosting:
    company = None
    if row["company_id"] is not None:
        company = models.Company(
            id=row["company_id"],
            name=row["company_name"],
            aliases=row["company_aliases"],
            logo_url=row["company_logo_url"],
        )
    return models.JobPosting(
        id=row["id"],
        title=row["title"],
        company_id=row["company_id"],
        location=row["location"],
        url=row["url"],
        raw_text=row["raw_text"],
        external_id=row["external_id"],
        url_hash=row["url_hash"],
        collected_at=_parse_datetime(row["collected_at"]),
        company=company,
    )


def _row_to_resume(row) -> models.Resume:
    return models.Resume(
        id=row["id"],
        file_path=row["file_path"],
        format=row["format"],
        text=row["text"],
        text_hash=row["text_hash"],
        created_at=_parse_datetime(row["created_at"]),
    )


def _row_to_resume_version(row) -> models.ResumeVersion:
    token_usage = row["token_usage"]
    if token_usage:
        try:
            token_usage = json.loads(token_usage)
        except json.JSONDecodeError:
            token_usage = None
    return models.ResumeVersion(
        id=row["id"],
        resume_id=row["resume_id"],
        job_posting_id=row["job_posting_id"],
        file_path=row["file_path"],
        created_at=_parse_datetime(row["created_at"]),
        base_resume_hash=row["base_resume_hash"],
        job_hash=row["job_hash"],
        input_signature=row["input_signature"],
        template_version=row["template_version"],
        model_name=row["model_name"],
        prompt_hash=row["prompt_hash"],
        token_usage=token_usage,
    )


def _row_to_run(row) -> models.Run:
    return models.Run(
        id=row["id"],
        triggered_by=row["triggered_by"],
        type=row["type"],
        started_at=_parse_datetime(row["started_at"]),
        finished_at=_parse_datetime(row["finished_at"]),
        status=row["status"],
        error=row["error"],
    )


def _row_to_schedule(row) -> models.Schedule:
    criteria = row["criteria_json"]
    if criteria:
        try:
            criteria = json.loads(criteria)
        except json.JSONDecodeError:
            criteria = None
    return models.Schedule(
        id=row["id"],
        cron_expr=row["cron_expr"],
        is_enabled=bool(row["is_enabled"]),
        criteria_json=criteria,
    )


def get_or_create_company(connection, name: str) -> models.Company:
    row = connection.execute(
        "SELECT * FROM companies WHERE name = ?", (name,)
    ).fetchone()
    if row:
        return _row_to_company(row)
    cursor = connection.execute(
        "INSERT INTO companies (name) VALUES (?)",
        (name,),
    )
    company_id = cursor.lastrowid
    row = connection.execute(
        "SELECT * FROM companies WHERE id = ?", (company_id,)
    ).fetchone()
    return _row_to_company(row)


def create_job_posting(
    connection,
    *,
    title: str,
    company: Optional[models.Company],
    location: Optional[str],
    url: Optional[str],
    raw_text: Optional[str],
    external_id: Optional[str],
) -> models.JobPosting:
    company_id = company.id if company else None
    material = url or raw_text or title
    url_hash = sha256(material.encode("utf-8", "ignore")).hexdigest()
    cursor = connection.execute(
        """
        INSERT INTO job_postings (company_id, title, location, url, raw_text, external_id, url_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (company_id, title, location, url, raw_text, external_id, url_hash),
    )
    job_id = cursor.lastrowid
    return get_job_posting(connection, job_id)


def list_job_postings(connection) -> list[models.JobPosting]:
    rows = connection.execute(
        """
        SELECT jp.*, c.name AS company_name, c.aliases AS company_aliases, c.logo_url AS company_logo_url
        FROM job_postings AS jp
        LEFT JOIN companies AS c ON jp.company_id = c.id
        ORDER BY jp.id DESC
        """
    ).fetchall()
    return [_row_to_job(row) for row in rows]


def create_resume(
    connection,
    *,
    file_path: str,
    file_format: str,
    text: Optional[str],
    text_hash: Optional[str],
) -> models.Resume:
    cursor = connection.execute(
        """
        INSERT INTO resumes (file_path, format, text, text_hash)
        VALUES (?, ?, ?, ?)
        """,
        (file_path, file_format, text, text_hash),
    )
    resume_id = cursor.lastrowid
    return get_resume(connection, resume_id)


def list_resumes(connection) -> list[models.Resume]:
    rows = connection.execute(
        "SELECT * FROM resumes ORDER BY created_at DESC, id DESC"
    ).fetchall()
    return [_row_to_resume(row) for row in rows]


def get_resume(connection, resume_id: int) -> Optional[models.Resume]:
    row = connection.execute(
        "SELECT * FROM resumes WHERE id = ?", (resume_id,)
    ).fetchone()
    if row:
        return _row_to_resume(row)
    return None


def get_job_posting(connection, job_id: int) -> Optional[models.JobPosting]:
    row = connection.execute(
        """
        SELECT jp.*, c.name AS company_name, c.aliases AS company_aliases, c.logo_url AS company_logo_url
        FROM job_postings AS jp
        LEFT JOIN companies AS c ON jp.company_id = c.id
        WHERE jp.id = ?
        """,
        (job_id,),
    ).fetchone()
    if row:
        return _row_to_job(row)
    return None


def create_resume_version(
    connection,
    *,
    resume: models.Resume,
    job_posting: models.JobPosting,
    file_path: str,
    template_version: str,
    model_name: str,
    prompt_hash: str,
    token_usage: Optional[dict],
) -> models.ResumeVersion:
    job_material = job_posting.raw_text or job_posting.title
    cursor = connection.execute(
        """
        INSERT INTO resume_versions (
            resume_id, job_posting_id, file_path,
            base_resume_hash, job_hash, input_signature,
            template_version, model_name, prompt_hash, token_usage
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            resume.id,
            job_posting.id,
            file_path,
            resume.text_hash,
            sha256(job_material.encode("utf-8", "ignore")).hexdigest(),
            sha256(f"{resume.id}:{job_posting.id}".encode()).hexdigest(),
            template_version,
            model_name,
            prompt_hash,
            json.dumps(token_usage) if token_usage else None,
        ),
    )
    version_id = cursor.lastrowid
    row = connection.execute(
        "SELECT * FROM resume_versions WHERE id = ?",
        (version_id,),
    ).fetchone()
    return _row_to_resume_version(row)


def create_run(
    connection,
    *,
    triggered_by: str,
    run_type: str,
) -> models.Run:
    cursor = connection.execute(
        "INSERT INTO runs (triggered_by, type, status) VALUES (?, ?, ?)",
        (triggered_by, run_type, "running"),
    )
    run_id = cursor.lastrowid
    row = connection.execute(
        "SELECT * FROM runs WHERE id = ?", (run_id,)
    ).fetchone()
    return _row_to_run(row)


def finish_run(
    connection,
    run: models.Run,
    *,
    status: str,
    error: Optional[str] = None,
) -> models.Run:
    connection.execute(
        "UPDATE runs SET status = ?, error = ?, finished_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, error, run.id),
    )
    row = connection.execute(
        "SELECT * FROM runs WHERE id = ?", (run.id,)
    ).fetchone()
    return _row_to_run(row)


def create_schedule(
    connection,
    *,
    cron_expr: str,
    is_enabled: bool,
    criteria_json: Optional[dict],
) -> models.Schedule:
    cursor = connection.execute(
        "INSERT INTO schedules (cron_expr, is_enabled, criteria_json) VALUES (?, ?, ?)",
        (cron_expr, 1 if is_enabled else 0, json.dumps(criteria_json) if criteria_json else None),
    )
    schedule_id = cursor.lastrowid
    row = connection.execute(
        "SELECT * FROM schedules WHERE id = ?", (schedule_id,)
    ).fetchone()
    return _row_to_schedule(row)


def list_schedules(connection) -> list[models.Schedule]:
    rows = connection.execute("SELECT * FROM schedules ORDER BY id").fetchall()
    return [_row_to_schedule(row) for row in rows]


def get_schedule(connection, schedule_id: int) -> Optional[models.Schedule]:
    row = connection.execute(
        "SELECT * FROM schedules WHERE id = ?", (schedule_id,)
    ).fetchone()
    if row:
        return _row_to_schedule(row)
    return None


def record_token_usage(total_tokens: int, prompt_tokens: int, completion_tokens: int) -> dict:
    return {
        "total_tokens": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }


def list_runs(connection) -> list[models.Run]:
    rows = connection.execute(
        "SELECT * FROM runs ORDER BY started_at DESC, id DESC"
    ).fetchall()
    return [_row_to_run(row) for row in rows]
