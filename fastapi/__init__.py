from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, Optional


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: Any = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def File(default: Any) -> Any:  # pragma: no cover - marker used for compatibility
    return default


class UploadFile:
    def __init__(self, filename: str, content: bytes, content_type: str | None = None) -> None:
        self.filename = filename
        self._content = content
        self.content_type = content_type

    async def read(self) -> bytes:
        return self._content


class FastAPI:
    def __init__(self) -> None:
        self._routes: Dict[str, Dict[str, Callable]] = {"GET": {}, "POST": {}}
        self._event_handlers: Dict[str, list[Callable]] = {"startup": [], "shutdown": []}

    def add_middleware(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - noop
        return None

    def on_event(self, event: str) -> Callable[[Callable], Callable]:
        def decorator(func: Callable) -> Callable:
            self._event_handlers.setdefault(event, []).append(func)
            return func

        return decorator

    def get(self, path: str, response_model: Optional[Any] = None) -> Callable[[Callable], Callable]:
        return self._register("GET", path)

    def post(self, path: str, response_model: Optional[Any] = None) -> Callable[[Callable], Callable]:
        return self._register("POST", path)

    def _register(self, method: str, path: str) -> Callable[[Callable], Callable]:
        def decorator(func: Callable) -> Callable:
            self._routes[method][path] = func
            return func

        return decorator

    def get_route(self, method: str, path: str) -> Callable:
        return self._routes[method][path]

    async def run_event(self, name: str) -> None:
        handlers = self._event_handlers.get(name, [])
        for handler in handlers:
            result = handler()
            if inspect.isawaitable(result):
                await result


# Convenience re-export for compatibility with ``from fastapi import status`` style imports.
status = type("status", (), {"HTTP_200_OK": 200})

