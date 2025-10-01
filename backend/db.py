from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Iterator

from .config import get_settings


_INIT_LOCK = Lock()
_INITIALIZED = False
_DATABASE_LOCATION: str | Path = ":memory:"


def _ensure_initialized() -> None:
    global _INITIALIZED, _DATABASE_LOCATION
    if _INITIALIZED:
        return
    with _INIT_LOCK:
        if _INITIALIZED:
            return
        settings = get_settings()
        url = settings.database_url
        target: str | Path
        if url == "sqlite:///:memory:":
            target = ":memory:"
        elif url.startswith("sqlite:///"):
            path_str = url[len("sqlite:///") :]
            target = Path(path_str).expanduser().resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
        else:
            raise RuntimeError(
                "Only sqlite:/// URLs are supported in the test environment."
            )

        if target != ":memory:":
            connection = sqlite3.connect(target)
        else:
            connection = sqlite3.connect(target)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            init_sql = Path("db/init.sql").read_text(encoding="utf-8")
            connection.executescript(init_sql)
            connection.commit()
        finally:
            connection.close()

        _DATABASE_LOCATION = target
        _INITIALIZED = True


@contextmanager
def session_scope() -> Iterator[sqlite3.Connection]:
    _ensure_initialized()
    connection = sqlite3.connect(_DATABASE_LOCATION)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
