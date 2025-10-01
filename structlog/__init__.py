from __future__ import annotations

import json
import logging
from typing import Any


class _Logger:
    def __init__(self, name: str | None = None) -> None:
        self._logger = logging.getLogger(name or "structlog")

    def info(self, event: str, **kwargs: Any) -> None:
        self._logger.info("%s %s", event, kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._logger.warning("%s %s", event, kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._logger.error("%s %s", event, kwargs)


def configure(*args: Any, **kwargs: Any) -> None:  # pragma: no cover - no-op configuration
    logging.basicConfig(level=logging.INFO)


def get_logger(name: str | None = None) -> _Logger:
    return _Logger(name)


class processors:  # pragma: no cover - simple stubs
    class TimeStamper:
        def __init__(self, fmt: str | None = None) -> None:
            self.fmt = fmt

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            return kwargs

    @staticmethod
    def add_log_level(*args: Any, **kwargs: Any) -> Any:
        return kwargs

    @staticmethod
    def EventRenamer(new_name: str) -> Any:
        def _rename(logger, method_name, event_dict):
            return event_dict

        return _rename

    @staticmethod
    def format_exc_info(*args: Any, **kwargs: Any) -> Any:
        return kwargs

    @staticmethod
    def JSONRenderer() -> Any:
        def renderer(logger, method_name, event_dict):
            return json.dumps(event_dict)

        return renderer


class stdlib:  # pragma: no cover - compatibility shim
    class LoggerFactory:
        def __call__(self, *args: Any, **kwargs: Any) -> logging.Logger:
            return logging.getLogger()

    class BoundLogger(_Logger):
        pass
