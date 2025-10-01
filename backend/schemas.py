from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class CompanyBase(BaseModel):
    name: str
    aliases: Optional[str] = None
    logo_url: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class Company(CompanyBase):
    id: int

    class Config:
        orm_mode = True


class JobPostingBase(BaseModel):
    title: str
    location: Optional[str] = None
    url: Optional[str] = None
    raw_text: Optional[str] = None
    external_id: Optional[str] = None


class JobPostingCreate(JobPostingBase):
    company_name: Optional[str] = None


class JobPosting(JobPostingBase):
    id: int
    company: Optional[Company]
    collected_at: Optional[datetime]

    class Config:
        orm_mode = True


class ResumeBase(BaseModel):
    file_path: str
    format: str
    text: Optional[str]
    text_hash: Optional[str]


class ResumeCreate(BaseModel):
    file_path: str
    format: str
    text: Optional[str]
    text_hash: Optional[str]


class Resume(ResumeBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class ResumeVersion(BaseModel):
    id: int
    resume_id: int
    job_posting_id: int
    file_path: str
    created_at: datetime

    class Config:
        orm_mode = True


class Run(BaseModel):
    id: int
    triggered_by: Optional[str]
    type: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    status: Optional[str]
    error: Optional[str]

    class Config:
        orm_mode = True


class ScheduleCreate(BaseModel):
    cron_expr: str
    is_enabled: bool = True
    criteria_json: Optional[dict] = None


class Schedule(BaseModel):
    id: int
    cron_expr: str
    is_enabled: bool
    criteria_json: Optional[dict]

    class Config:
        orm_mode = True


class TailorRequest(BaseModel):
    resume_id: int
    job_posting_id: int


class TailorResponse(BaseModel):
    resume_version_id: int
    artifact_path: str
    mock: bool = False


class SchedulerTriggerRequest(BaseModel):
    schedule_id: int


class UploadJobCSVResponse(BaseModel):
    created_ids: List[int]
