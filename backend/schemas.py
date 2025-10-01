from __future__ import annotations

from dataclasses import dataclass, asdict, fields
from datetime import datetime
from typing import Any, List, Optional, Type, TypeVar, get_args, get_origin


T = TypeVar("T", bound="SchemaBase")


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, SchemaBase):
        return value.to_dict()
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    return value


class SchemaBase:
    @classmethod
    def from_dict(cls: Type[T], data: dict) -> T:
        return cls(**data)

    def to_dict(self) -> dict:
        return {
            key: _serialize(value)
            for key, value in asdict(self).items()
            if value is not None
        }

    @classmethod
    def from_orm(cls: Type[T], obj: Any) -> T:
        payload = {}
        for field in fields(cls):
            value = getattr(obj, field.name, None)
            payload[field.name] = _convert(value, field.type)
        return cls(**payload)  # type: ignore[arg-type]


def _convert(value: Any, annotation: Any) -> Any:
    if value is None:
        return None
    origin = get_origin(annotation)
    if origin in (list, List):
        inner = get_args(annotation)[0]
        return [_convert(item, inner) for item in value]
    if isinstance(value, datetime):
        return value
    if hasattr(annotation, "__mro__") and issubclass(annotation, SchemaBase):
        return annotation.from_orm(value)
    return value


@dataclass
class Company(SchemaBase):
    id: int
    name: str
    aliases: Optional[str] = None
    logo_url: Optional[str] = None


@dataclass
class JobPosting(SchemaBase):
    id: int
    title: str
    location: Optional[str] = None
    url: Optional[str] = None
    raw_text: Optional[str] = None
    external_id: Optional[str] = None
    company: Optional[Company] = None
    collected_at: Optional[datetime] = None


@dataclass
class JobPostingCreate(SchemaBase):
    title: str
    location: Optional[str] = None
    url: Optional[str] = None
    raw_text: Optional[str] = None
    external_id: Optional[str] = None
    company_name: Optional[str] = None


@dataclass
class Resume(SchemaBase):
    id: int
    file_path: str
    format: str
    text: Optional[str]
    text_hash: Optional[str]
    created_at: datetime


@dataclass
class ResumeCreate(SchemaBase):
    file_path: str
    format: str
    text: Optional[str]
    text_hash: Optional[str]


@dataclass
class ResumeVersion(SchemaBase):
    id: int
    resume_id: int
    job_posting_id: int
    file_path: str
    created_at: datetime


@dataclass
class Run(SchemaBase):
    id: int
    triggered_by: Optional[str]
    type: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    status: Optional[str]
    error: Optional[str]


@dataclass
class Schedule(SchemaBase):
    id: int
    cron_expr: str
    is_enabled: bool
    criteria_json: Optional[dict]


@dataclass
class ScheduleCreate(SchemaBase):
    cron_expr: str
    is_enabled: bool = True
    criteria_json: Optional[dict] = None


@dataclass
class TailorRequest(SchemaBase):
    resume_id: int
    job_posting_id: int


@dataclass
class TailorResponse(SchemaBase):
    resume_version_id: int
    artifact_path: str
    mock: bool = False


@dataclass
class SchedulerTriggerRequest(SchemaBase):
    schedule_id: int


@dataclass
class UploadJobCSVResponse(SchemaBase):
    created_ids: List[int]
