from __future__ import annotations

from nicegui import ui

from ..backend_bridge import (
    create_job_posting,
    import_jobs_from_csv,
    list_job_postings,
    list_resumes,
    tailor_resume,
)
from .shared import page_container, top_navigation


@ui.page("/jobs")
def job_board_page() -> None:
    top_navigation("/jobs")
    with page_container():
        ui.label("Job Board").classes("text-3xl font-semibold")
        ui.label("Manage job intel, review descriptions, and tailor on demand.").classes("text-gray-500")
        with ui.card().classes("w-full bg-gray-50 border-dashed border"):
            ui.label("DiffPreview").classes("text-lg font-semibold")
            ui.label("Coming soon: visual diff approval workflows.").classes("text-gray-500")

        status = ui.label().classes("text-green-600")

        resume_options = {
            f"#{resume.id} · {resume.format.upper()} · {resume.created_at:%Y-%m-%d}": resume.id
            for resume in list_resumes()
        }
        selected_resume = ui.select(
            resume_options,
            label="Select resume to tailor",
        ).classes("w-full")
        if resume_options:
            selected_resume.set_value(next(iter(resume_options.values())))
        else:
            selected_resume.set_value(None)
            status.set_text("Upload a resume before tailoring")
            status.classes("text-orange-600")

        with ui.expansion("Add Job Posting", icon="work").classes("w-full"):
            with ui.form() as job_form:
                company_input = ui.input("Company")
                title_input = ui.input("Job Title").props("required")
                location_input = ui.input("Location")
                url_input = ui.input("Job URL")
                raw_text_input = ui.textarea("Description").props("rows=6")
                ui.button("Create Job", on_click=lambda: submit_job()).props("color=primary")

            def submit_job() -> None:
                if not title_input.value:
                    status.set_text("Job title is required")
                    status.classes("text-red-600")
                    return
                payload = {
                    "title": title_input.value,
                    "company_name": company_input.value or None,
                    "location": location_input.value or None,
                    "url": url_input.value or None,
                    "raw_text": raw_text_input.value or None,
                }
                job = create_job_posting(payload)
                status.set_text(f"Created job #{job.id} for {job.title}")
                status.classes("text-green-600")
                company_input.set_value("")
                title_input.set_value("")
                location_input.set_value("")
                url_input.set_value("")
                raw_text_input.set_value("")
                render_job_cards()

        ui.upload(
            label="Import CSV (title,company,location,url,description)",
            auto_upload=True,
            on_upload=lambda e: import_csv(e),
        ).props("accept=.csv").classes("w-full")

        def import_csv(event) -> None:
            if hasattr(event.content, "seek"):
                event.content.seek(0)
            created = import_jobs_from_csv(event.content)
            status.set_text(f"Imported {len(created)} jobs from CSV")
            status.classes("text-green-600")
            render_job_cards()

        jobs_container = ui.column().classes("w-full gap-4")

        def render_job_cards() -> None:
            jobs_container.clear()
            jobs = list_job_postings()
            if not jobs:
                ui.label("No job postings yet. Add one above or import via CSV.").classes("text-gray-500")
                return
            for job in jobs:
                with jobs_container:
                    with ui.card().classes("w-full"):
                        ui.label(job.title).classes("text-xl font-semibold")
                        subtitle = " · ".join(
                            filter(
                                None,
                                [
                                    job.company.name if job.company else None,
                                    job.location,
                                ],
                            )
                        )
                        if subtitle:
                            ui.label(subtitle).classes("text-gray-500")
                        ui.label((job.raw_text or "")[0:400] + ("..." if job.raw_text and len(job.raw_text) > 400 else ""))
                        with ui.row().classes("justify-between items-center w-full mt-2"):
                            if job.url:
                                ui.link("Job Listing", job.url, new_tab=True)
                            ui.button(
                                "Tailor Resume",
                                on_click=lambda j=job: run_tailoring(j.id, j.title, j.company.name if j.company else "Company"),
                            ).props("color=primary")

        def run_tailoring(job_id: int, title: str, company: str) -> None:
            if not selected_resume.value:
                status.set_text("Select a resume before tailoring")
                status.classes("text-red-600")
                return
            try:
                version, artifact_path, mock = tailor_resume(selected_resume.value, job_id)
                label = "MOCK" if mock else "AI"
                status.set_text(
                    f"[{label}] Generated resume version #{version.id} for {company} — {title}. Saved to {artifact_path}."
                )
                status.classes("text-green-600")
            except Exception as exc:  # pragma: no cover - UI feedback
                status.set_text(f"Tailoring failed: {exc}")
                status.classes("text-red-600")

        render_job_cards()
