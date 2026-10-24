"""Application logging: console plus rotating file, with redaction wired in.

Human-readable records go to stderr. The file receives one JSON object per line
unless ``json_file`` is false, in which case it receives the same human-readable
format (SRD 8.2 ``[logging] json_file``). The file rotates at 5 MB and keeps five
files in total (FR-D-1101).

Every record gains ``session_id``, ``device_id``, ``run_id``, and ``action_id``
from :mod:`contextvars` when those are set (FR-D-1102). The injected redaction
filter is installed on every handler (FR-D-1103).

This module imports only the standard library and has no import-time side
effects. Callers own the wiring: pass ``deckhand.config.paths.log_dir()``, the
validated level, the ``json_file`` flag, and a
:class:`deckhand.security.redaction.Redactor`.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

__all__ = [
    "CONTEXT_FIELDS",
    "LOG_FILENAME",
    "MAX_LOG_BYTES",
    "MAX_LOG_FILES",
    "ContextFilter",
    "ContextFormatter",
    "JsonFormatter",
    "action_id",
    "device_id",
    "run_id",
    "session_id",
    "setup_logging",
]

LOG_FILENAME = "deckhand.log"
MAX_LOG_BYTES = 5 * 1024 * 1024
MAX_LOG_FILES = 5
BACKUP_COUNT = MAX_LOG_FILES - 1
"""Rotations kept next to the live file, so five files exist in total."""

CONSOLE_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"

session_id: ContextVar[str | None] = ContextVar("deckhand_session_id", default=None)
device_id: ContextVar[str | None] = ContextVar("deckhand_device_id", default=None)
run_id: ContextVar[str | None] = ContextVar("deckhand_run_id", default=None)
action_id: ContextVar[str | None] = ContextVar("deckhand_action_id", default=None)

CONTEXT_FIELDS: Final[tuple[str, ...]] = ("session_id", "device_id", "run_id", "action_id")

_CONTEXT_VARS: Final[tuple[tuple[str, ContextVar[str | None]], ...]] = (
    ("session_id", session_id),
    ("device_id", device_id),
    ("run_id", run_id),
    ("action_id", action_id),
)

_CONTEXT_NAMES: Final[frozenset[str]] = frozenset(CONTEXT_FIELDS)

_RESERVED_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)


class ContextFilter(logging.Filter):
    """Copy the set context variables onto the record (FR-D-1102)."""

    def filter(self, record: logging.LogRecord) -> bool:
        for name, variable in _CONTEXT_VARS:
            value = variable.get()
            if value is not None:
                record.__dict__[name] = value
        return True


class ContextFormatter(logging.Formatter):
    """Human-readable formatter that appends the ids that are actually set."""

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        pairs = [
            f"{name}={value}" for name, _ in _CONTEXT_VARS if (value := getattr(record, name, None))
        ]
        return f"{base} [{' '.join(pairs)}]" if pairs else base


class JsonFormatter(logging.Formatter):
    """One JSON object per line, with context ids and extra fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for name, _ in _CONTEXT_VARS:
            value = getattr(record, name, None)
            if value:
                payload[name] = value

        extras = {
            key: value
            for key, value in vars(record).items()
            if key not in _RESERVED_FIELDS and key not in _CONTEXT_NAMES
        }
        if extras:
            payload["extra"] = extras

        if record.exc_text:
            payload["traceback"] = record.exc_text
        if record.stack_info:
            payload["stack"] = record.stack_info

        return json.dumps(payload, ensure_ascii=False, default=str)


def _resolve_level(level: str) -> int:
    """Map a level name to its numeric value, rejecting unknown names."""
    key = level.strip().upper()
    levels = logging.getLevelNamesMapping()
    if key not in levels:
        raise ValueError(f"unknown log level: {level!r}")
    return levels[key]


def setup_logging(
    *,
    log_dir: Path,
    level: str,
    json_file: bool,
    redactor: logging.Filter,
) -> logging.Logger:
    """Configure the root logger and return it.

    Any handler already attached to the root logger is replaced, so calling this
    again reconfigures rather than duplicating output. ``redactor`` is installed
    on every handler this function creates (FR-D-1103); the caller is responsible
    for registering secret values on it.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
        existing.close()
    root.setLevel(_resolve_level(level))

    context_filter = ContextFilter()

    console = logging.StreamHandler()
    console.setFormatter(ContextFormatter(CONSOLE_FORMAT))

    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / LOG_FILENAME,
        maxBytes=MAX_LOG_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(JsonFormatter() if json_file else ContextFormatter(CONSOLE_FORMAT))

    for handler in (console, file_handler):
        handler.addFilter(context_filter)
        handler.addFilter(redactor)
        root.addHandler(handler)

    return root
