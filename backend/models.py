from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Company:
    id: int
    name: str
    aliases: Optional[str] = None
    logo_url: Optional[str] = None


@dataclass
class JobPosting:
    id: int
    title: str
    company_id: Optional[int]
    location: Optional[str]
    url: Optional[str]
    raw_text: Optional[str]
    external_id: Optional[str]
    url_hash: str
    collected_at: datetime
    company: Optional[Company] = None


@dataclass
class Resume:
    id: int
    file_path: str
    format: str
    text: Optional[str]
    text_hash: Optional[str]
    created_at: datetime


@dataclass
class ResumeVersion:
    id: int
    resume_id: int
    job_posting_id: int
    file_path: str
    created_at: datetime
    base_resume_hash: Optional[str] = None
    job_hash: Optional[str] = None
    input_signature: Optional[str] = None
    template_version: Optional[str] = None
    model_name: Optional[str] = None
    prompt_hash: Optional[str] = None
    token_usage: Optional[dict] = field(default=None)


@dataclass
class Run:
    id: int
    triggered_by: Optional[str]
    type: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    status: Optional[str]
    error: Optional[str]


@dataclass
class Schedule:
    id: int
    cron_expr: str
    is_enabled: bool
    criteria_json: Optional[dict]
