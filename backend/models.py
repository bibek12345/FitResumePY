from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from .db import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    aliases = Column(Text)
    logo_url = Column(Text)

    job_postings = relationship("JobPosting", back_populates="company")


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    title = Column(String, nullable=False)
    location = Column(String)
    url = Column(Text)
    raw_text = Column(Text)
    external_id = Column(String)
    url_hash = Column(String, unique=True)
    collected_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="job_postings")
    resume_versions = relationship("ResumeVersion", back_populates="job_posting")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(Text, nullable=False)
    format = Column(String, nullable=False)
    text = Column(Text)
    text_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    versions = relationship("ResumeVersion", back_populates="resume")


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    base_resume_hash = Column(String)
    job_hash = Column(String)
    input_signature = Column(String)
    template_version = Column(String)
    model_name = Column(String)
    prompt_hash = Column(String)
    token_usage = Column(JSON)

    resume = relationship("Resume", back_populates="versions")
    job_posting = relationship("JobPosting", back_populates="resume_versions")


class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    triggered_by = Column(String)
    type = Column(String)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    status = Column(String)
    error = Column(Text)


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    cron_expr = Column(String, nullable=False)
    is_enabled = Column(Boolean, default=True)
    criteria_json = Column(JSON)
