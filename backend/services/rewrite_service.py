from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

import structlog

from ..config import get_settings

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT = "You are a professional resume editor. Do not invent employers, roles, skills, or dates. Keep ATS-friendly formatting."
PLAN_PROMPT = (
    "Given the job posting and resume text, produce a JSON plan with keys summary, skills, experience, "
    "education, certifications. Experience is an array of objects with employer, role, start, end, bullets.""
)
RENDER_PROMPT = (
    "Using the provided plan JSON, render a tailored resume in plain text with sections: Summary, Skills, Experience, "
    "Education, Certifications."
)


@dataclass
class RewriteResult:
    plan: dict
    rendered_text: str
    model_name: str
    prompt_hash: str
    token_usage: dict | None = None
    mock: bool = False


class RewriteService(Protocol):
    def rewrite(self, resume_text: str, job_text: str) -> RewriteResult:
        ...


class MockRewriteService:
    model_name = "mock"

    def rewrite(self, resume_text: str, job_text: str) -> RewriteResult:  # noqa: D401
        logger.info("mock_rewrite", resume_length=len(resume_text), job_length=len(job_text))
        plan = {
            "summary": "[MOCK OUTPUT] Tailored summary based on provided resume and job description.",
            "skills": ["[MOCK OUTPUT] Skill A", "Skill B"],
            "experience": [
                {
                    "employer": "Current Employer",
                    "role": "Relevant Role",
                    "start": "2020",
                    "end": "Present",
                    "bullets": [
                        "Aligned achievements with job posting keywords.",
                        "Demonstrated leadership and impact in relevant projects.",
                    ],
                }
            ],
            "education": ["Degree, University"],
            "certifications": ["Certification"]
        }
        rendered = _render_from_plan(plan)
        prompt_hash = sha256((resume_text + job_text).encode()).hexdigest()
        return RewriteResult(plan=plan, rendered_text=rendered, model_name=self.model_name, prompt_hash=prompt_hash, mock=True)


class OpenAIRewriteService:
    def __init__(self, api_key: str) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model_name = "gpt-4o-mini"

    def rewrite(self, resume_text: str, job_text: str) -> RewriteResult:
        prompt_hash = sha256((resume_text + job_text).encode()).hexdigest()
        plan_response = self.client.responses.create(
            model=self.model_name,
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": f"{PLAN_PROMPT}\nJob Posting:\n{job_text}\nResume:\n{resume_text}",
                },
            ],
            response_format={"type": "json_object"},
        )
        plan_text = plan_response.output[0].content[0].text
        plan = json.loads(plan_text)

        render_response = self.client.responses.create(
            model=self.model_name,
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": f"{RENDER_PROMPT}\nPlan JSON:\n{json.dumps(plan)}",
                },
            ],
        )
        rendered_text = render_response.output[0].content[0].text
        token_usage = getattr(render_response, "usage", None)
        token_data = None
        if token_usage:
            token_data = {
                "total_tokens": token_usage.total_tokens,
                "prompt_tokens": token_usage.prompt_tokens,
                "completion_tokens": token_usage.completion_tokens,
            }
        return RewriteResult(
            plan=plan,
            rendered_text=rendered_text,
            model_name=self.model_name,
            prompt_hash=prompt_hash,
            token_usage=token_data,
        )


def get_rewrite_service() -> RewriteService:
    settings = get_settings()
    if settings.openai_api_key:
        try:
            return OpenAIRewriteService(settings.openai_api_key)
        except Exception as exc:  # pragma: no cover - openai configuration errors
            logging.getLogger(__name__).warning("Failed to init OpenAI service, using mock", exc_info=exc)
    return MockRewriteService()


def _render_from_plan(plan: dict) -> str:
    sections = [
        "Summary\n" + plan.get("summary", ""),
        "Skills\n" + ", ".join(plan.get("skills", [])),
    ]
    experiences = []
    for exp in plan.get("experience", []):
        bullets = "\n  - ".join(exp.get("bullets", []))
        exp_block = f"{exp.get('employer', '')} — {exp.get('role', '')} ({exp.get('start', '')} - {exp.get('end', '')})"
        if bullets:
            exp_block += f"\n  - {bullets}"
        experiences.append(exp_block)
    sections.append("Experience\n" + "\n".join(experiences))
    sections.append("Education\n" + "\n".join(plan.get("education", [])))
    sections.append("Certifications\n" + "\n".join(plan.get("certifications", [])))
    return "\n\n".join(section.strip() for section in sections if section)
