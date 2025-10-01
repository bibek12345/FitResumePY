from __future__ import annotations

from pathlib import Path

from nicegui import ui

from ..backend_bridge import list_resumes, upload_resume
from .shared import page_container, top_navigation


@ui.page("/resumes")
def resume_manager_page() -> None:
    top_navigation("/resumes")
    with page_container():
        ui.label("Resume Manager").classes("text-3xl font-semibold")
        ui.label("Upload base resumes and review parsed text.").classes("text-gray-500")

        status = ui.label().classes("text-green-600")

        def refresh_table() -> None:
            data = [
                {
                    "id": resume.id,
                    "file": Path(resume.file_path).name,
                    "format": resume.format.upper(),
                    "created_at": resume.created_at.strftime("%Y-%m-%d %H:%M"),
                    "text": resume.text or "",
                }
                for resume in list_resumes()
            ]
            table.rows = data

        async def handle_upload(event) -> None:
            content = event.content.read()
            try:
                resume = upload_resume(event.name, content)
                status.set_text(f"Uploaded {event.name} as resume #{resume.id}")
                status.classes("text-green-600")
                refresh_table()
            except Exception as exc:  # pragma: no cover - UI feedback
                status.set_text(f"Upload failed: {exc}")
                status.classes("text-red-600")

        ui.upload(
            label="Drop DOCX or PDF",
            auto_upload=True,
            on_upload=handle_upload,
        ).props("accept=.docx,.pdf").classes("w-full")

        table = ui.table(
            columns=[
                {"name": "id", "label": "ID", "field": "id", "sortable": True},
                {"name": "file", "label": "File", "field": "file"},
                {"name": "format", "label": "Format", "field": "format"},
                {"name": "created_at", "label": "Uploaded", "field": "created_at"},
            ],
            rows=[],
            row_key="id",
        ).classes("w-full")

        preview = ui.expansion("Resume Preview").classes("w-full")
        preview_text = ui.markdown("Select a resume to preview parsed text.")

        @table.on("rowClick")
        def _(event) -> None:
            row = event.args.get("row")
            if not row:
                return
            preview.set_value(f"Resume #{row['id']} — {row['file']}")
            preview_text.set_content(f"```\n{row.get('text', '')[:4000]}\n```")

        refresh_table()
