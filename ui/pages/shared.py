from __future__ import annotations

from nicegui import ui

NAV_ITEMS = [
    ("Dashboard", "/"),
    ("Resumes", "/resumes"),
    ("Job Board", "/jobs"),
    ("Runs", "/runs"),
    ("Scheduler", "/scheduler"),
    ("Artifacts", "/artifacts"),
]


def top_navigation(active: str) -> None:
    with ui.header().classes("bg-blue-600 text-white"):
        ui.label("FitResume").classes("text-2xl font-semibold")
        with ui.row().classes("ml-auto items-center gap-4"):
            for label, path in NAV_ITEMS:
                button = ui.button(label, on_click=lambda p=path: ui.open(p)).props("flat color=white")
                if path == active:
                    button.classes("bg-white text-blue-600 rounded-lg")


def page_container() -> ui.element:
    return ui.column().classes("w-full max-w-6xl mx-auto p-6 space-y-4")
