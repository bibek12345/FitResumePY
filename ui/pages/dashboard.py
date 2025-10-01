from __future__ import annotations

from nicegui import ui

from ..backend_bridge import get_counts, get_recent_runs
from .shared import page_container, top_navigation


@ui.page("/")
def dashboard_page() -> None:
    top_navigation("/")
    with page_container():
        ui.label("Welcome to FitResume").classes("text-3xl font-bold")
        ui.label("Operational command center for tailored resumes.").classes("text-gray-500")

        counts = get_counts()
        with ui.row().classes("gap-6 flex-wrap"):
            for label, value in counts.items():
                with ui.card().classes("min-w-[200px] bg-blue-50 border border-blue-100"):
                    ui.label(label).classes("text-sm uppercase text-blue-600")
                    ui.label(str(value)).classes("text-3xl font-semibold")

        with ui.row().classes("gap-4"):
            ui.button("Upload Resume", on_click=lambda: ui.open("/resumes"))
            ui.button("Add Job Posting", on_click=lambda: ui.open("/jobs"))
            ui.button("Review Artifacts", on_click=lambda: ui.open("/artifacts"))

        with ui.expansion("Latest Activity", icon="timeline").classes("w-full"):
            with ui.column().classes("space-y-2"):
                for item in get_recent_runs():
                    ui.label(item)
