from __future__ import annotations

import json
from urllib.parse import quote

from nicegui import ui

from ..backend_bridge import list_artifacts
from .shared import page_container, top_navigation


@ui.page("/artifacts")
def artifacts_page() -> None:
    top_navigation("/artifacts")
    with page_container():
        ui.label("Artifacts").classes("text-3xl font-semibold")
        ui.label("Browse generated resumes and download tailored documents.").classes("text-gray-500")

        search = ui.input("Search", placeholder="Company, job, or filename").classes("w-full")
        container = ui.column().classes("w-full gap-4")

        def render() -> None:
            artifacts = list_artifacts()
            query = (search.value or "").lower()
            container.clear()
            matches = []
            for artifact in artifacts:
                text_blob = json.dumps(artifact.get("meta", {})).lower()
                if query and query not in artifact["folder"].lower() and query not in artifact["file"].lower() and query not in text_blob:
                    continue
                matches.append(artifact)
            if not matches:
                with container:
                    ui.label("No artifacts match your search yet.").classes("text-gray-500")
                return
            for artifact in matches:
                download_url = f"/api/artifacts/download?path={quote(artifact['path'])}"
                meta = artifact.get("meta", {})
                with container:
                    with ui.card().classes("w-full"):
                        ui.label(artifact["file"]).classes("text-xl font-semibold")
                        ui.label(artifact["folder"]).classes("text-gray-500")
                        if isinstance(meta, dict) and meta:
                            ui.label(json.dumps(meta, indent=2)).classes("font-mono text-sm bg-gray-100 p-2 rounded")
                        ui.button("Download", on_click=lambda url=download_url: ui.open(url)).props("color=primary")

        @search.on("input")
        def _(_: str) -> None:
            render()

        render()
