from __future__ import annotations

from typing import Any, Callable

from fastapi import FastAPI


app = FastAPI()


class _DummyElement:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def __call__(self, *args: Any, **kwargs: Any) -> "_DummyElement":
        return self

    def __enter__(self) -> "_DummyElement":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def classes(self, *args: Any, **kwargs: Any) -> "_DummyElement":
        return self

    def props(self, *args: Any, **kwargs: Any) -> "_DummyElement":
        return self

    def style(self, *args: Any, **kwargs: Any) -> "_DummyElement":
        return self


class _DummyUI:
    def page(self, path: str) -> Callable[[Callable], Callable]:
        def decorator(func: Callable) -> Callable:
            return func

        return decorator

    def open(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - UI stub
        return None

    def notify(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - UI stub
        return None

    def __getattr__(self, name: str) -> Callable:
        def method(*args: Any, **kwargs: Any) -> _DummyElement:
            return _DummyElement()

        return method


ui = _DummyUI()
