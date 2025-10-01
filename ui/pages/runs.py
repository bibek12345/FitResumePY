from __future__ import annotations

from nicegui import ui

from ..backend_bridge import list_runs
from .shared import page_container, top_navigation


@ui.page("/runs")
def runs_page() -> None:
    top_navigation("/runs")
    with page_container():
        ui.label("Automation Runs").classes("text-3xl font-semibold")
        ui.label("Monitor tailoring jobs, scheduler activity, and manual executions.").classes("text-gray-500")

        runs = list_runs()
        if not runs:
            ui.label("No runs recorded yet. Trigger tailoring or enable schedules to populate this view.").classes(
                "text-gray-500"
            )
            return

        with ui.timeline().classes("w-full"):
            for run in runs:
                with ui.timeline_item(icon="play_arrow"):
                    with ui.card().classes("w-full"):
                        ui.label(f"Run #{run.id} — {run.type or 'manual'}").classes("text-xl font-semibold")
                        ui.label(f"Started: {run.started_at:%Y-%m-%d %H:%M:%S}")
                        if run.finished_at:
                            ui.label(f"Finished: {run.finished_at:%Y-%m-%d %H:%M:%S}")
                        ui.label(f"Status: {run.status or 'pending'}").classes(
                            "text-green-600" if (run.status or "").lower() == "success" else "text-gray-600"
                        )
                        if run.error:
                            ui.label(f"Error: {run.error}").classes("text-red-600")
