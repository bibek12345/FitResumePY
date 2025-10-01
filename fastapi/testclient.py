from __future__ import annotations

import asyncio
import inspect
from typing import Any, Callable, Dict, get_type_hints

from . import FastAPI, HTTPException, UploadFile


class Response:
    def __init__(self, status_code: int, data: Any = None) -> None:
        self.status_code = status_code
        self._data = data

    def json(self) -> Any:
        return self._data


class TestClient:
    def __init__(self, app: FastAPI) -> None:
        self.app = app

    def __enter__(self) -> "TestClient":
        asyncio.run(self.app.run_event("startup"))
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        asyncio.run(self.app.run_event("shutdown"))

    def get(self, path: str, **kwargs: Any) -> Response:
        return self._request("GET", path, None, None)

    def post(self, path: str, *, json: Any = None, files: Dict[str, Any] | None = None) -> Response:
        return self._request("POST", path, json, files)

    def _request(
        self,
        method: str,
        path: str,
        json_payload: Any,
        files: Dict[str, Any] | None,
    ) -> Response:
        try:
            handler = self.app.get_route(method, path)
        except KeyError:
            return Response(404, {"detail": "Not Found"})

        try:
            result = self._call_handler(handler, json_payload, files)
        except HTTPException as exc:
            return Response(exc.status_code, exc.detail)
        return Response(200, _prepare_response(result))

    def _call_handler(
        self,
        handler: Callable,
        json_payload: Any,
        files: Dict[str, Any] | None,
    ) -> Any:
        kwargs: Dict[str, Any] = {}
        files_data: Dict[str, UploadFile] = {}
        if files:
            for key, file_tuple in files.items():
                filename, file_obj, content_type = file_tuple
                content = file_obj.read()
                if hasattr(file_obj, "seek"):
                    file_obj.seek(0)
                files_data[key] = UploadFile(
                    filename=filename,
                    content=content,
                    content_type=content_type,
                )

        signature = inspect.signature(handler)
        try:
            type_hints = get_type_hints(handler)
        except Exception:  # pragma: no cover - best effort resolution
            type_hints = {}
        for name, parameter in signature.parameters.items():
            annotation = type_hints.get(name, parameter.annotation)
            if name in files_data:
                kwargs[name] = files_data[name]
            elif json_payload is not None:
                value = json_payload
                if (
                    annotation is not inspect._empty
                    and isinstance(annotation, type)
                    and hasattr(annotation, "from_dict")
                    and callable(annotation.from_dict)
                ):
                    value = annotation.from_dict(json_payload)
                kwargs[name] = value
        result = handler(**kwargs)
        if inspect.isawaitable(result):
            return asyncio.run(result)
        return result


def _prepare_response(data: Any) -> Any:
    if data is None:
        return None
    if hasattr(data, "to_dict") and callable(data.to_dict):
        return data.to_dict()
    if isinstance(data, list):
        return [_prepare_response(item) for item in data]
    if isinstance(data, dict):
        return {key: _prepare_response(value) for key, value in data.items()}
    return data
