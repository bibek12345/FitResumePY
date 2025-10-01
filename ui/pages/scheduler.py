from __future__ import annotations

from nicegui import ui

from ..backend_bridge import (
    create_schedule,
    list_schedules,
    sync_scheduler,
    trigger_schedule,
)
from .shared import page_container, top_navigation


@ui.page("/scheduler")
def scheduler_page() -> None:
    top_navigation("/scheduler")
    with page_container():
        ui.label("Scheduler").classes("text-3xl font-semibold")
        ui.label("Automate resume tailoring with recurring jobs.").classes("text-gray-500")

        status = ui.label().classes("text-green-600")

        def refresh() -> None:
            sync_scheduler()
            schedules = list_schedules()
            rows = [
                {
                    "id": schedule.id,
                    "cron": schedule.cron_expr,
                    "enabled": "Yes" if schedule.is_enabled else "No",
                    "criteria": schedule.criteria_json or {},
                }
                for schedule in schedules
            ]
            table.rows = rows

        with ui.row().classes("gap-3"):
            ui.button("Daily 8am", on_click=lambda: create_cron("0 8 * * *"))
            ui.button("Weekly Monday", on_click=lambda: create_cron("0 9 * * MON"))
            ui.button("Sync", on_click=refresh)

        cron_input = ui.input("Cron Expression", placeholder="e.g. 0 9 * * MON")
        enable_toggle = ui.switch("Enabled", value=True)
        ui.button("Create Schedule", on_click=lambda: submit_schedule()).props("color=primary")

        def create_cron(cron: str) -> None:
            cron_input.set_value(cron)

        def submit_schedule() -> None:
            cron = cron_input.value
            if not cron:
                status.set_text("Cron expression required")
                status.classes("text-red-600")
                return
            schedule = create_schedule({"cron_expr": cron, "is_enabled": enable_toggle.value, "criteria_json": None})
            status.set_text(f"Created schedule #{schedule.id} ({schedule.cron_expr})")
            status.classes("text-green-600")
            cron_input.set_value("")
            enable_toggle.set_value(True)
            refresh()

        table = ui.table(
            columns=[
                {"name": "id", "label": "ID", "field": "id"},
                {"name": "cron", "label": "Cron", "field": "cron"},
                {"name": "enabled", "label": "Enabled", "field": "enabled"},
                {"name": "criteria", "label": "Criteria", "field": "criteria"},
            ],
            rows=[],
            row_key="id",
        ).classes("w-full")

        @table.on("rowClick")
        def _(event) -> None:
            row = event.args.get("row")
            if not row:
                return
            try:
                trigger_schedule(row["id"])
                status.set_text(f"Triggered schedule #{row['id']} immediately")
                status.classes("text-green-600")
            except Exception as exc:  # pragma: no cover - UI feedback
                status.set_text(f"Trigger failed: {exc}")
                status.classes("text-red-600")

        refresh()
