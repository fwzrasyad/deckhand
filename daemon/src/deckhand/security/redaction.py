"""Log filter that strips tokens, pairing secrets, and secret params (SEC-016).

Layer 2 (domain service). Imports only the standard library.

Two independent mechanisms protect a record:

* a registry of *known* secret values -- device tokens, pairing secrets, the
  control token, and values of parameters marked ``secret`` -- replaced wherever
  they appear;
* patterns for the usual textual encodings of a secret (``key=value``,
  ``key: value``, JSON, and ``Bearer`` credentials), which catch values that were
  never registered.

The filter works on the *formatted* message: ``msg`` and ``args`` are replaced by
one scrubbed string, and extra fields, ``exc_text``, ``stack_info``, and
``exc_info`` are scrubbed as well. ``exc_info`` is dropped after its traceback has
been rendered and scrubbed because a traceback object cannot be sanitised in
place; the sanitised text is left in ``exc_text`` for formatters.

The registry is injected, never global. A :class:`Redactor` returns ``True`` from
:meth:`Redactor.filter` even when it fails: a failed redaction replaces the record
with :data:`SAFE_PLACEHOLDER` rather than letting the original text through.
"""

from __future__ import annotations

import logging
import re
import threading
from collections.abc import Iterable, Mapping

__all__ = [
    "REDACTION_MARKER",
    "SAFE_PLACEHOLDER",
    "Redactor",
    "SecretRegistry",
]

REDACTION_MARKER = "[REDACTED]"
"""Replacement for every redacted value."""

SAFE_PLACEHOLDER = "[log record withheld: redaction failed]"
"""Message used when the filter itself errors."""

_MAX_EXTRA_DEPTH = 4

_SKIP_FIELDS = frozenset({"msg", "args", "exc_info", "exc_text", "stack_info", "message"})

_KEEP_ON_FAILURE = frozenset(
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

_KEY_VALUE_PATTERN = re.compile(
    r"""
    (?P<prefix>
        ["']?
        \b(?:token|secret|password|passwd|authorization|api[_-]?key|key)\b
        ["']?
        \s*[=:]\s*
    )
    (?P<value>
        "(?:[^"\\]|\\.)*"
        | '(?:[^'\\]|\\.)*'
        | (?:Bearer\s+(?:\[REDACTED\]|[A-Za-z0-9\-._~+/]+=*))
        | [^\s,;&\[\]{}"'\\]+
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

_BEARER_PATTERN = re.compile(r"\bBearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)


def _replace_key_value(match: re.Match[str]) -> str:
    """Replace the value of a ``key=value`` / ``key: value`` match, keeping quotes."""
    value = match.group("value")
    if REDACTION_MARKER in value:
        return match.group(0)
    quote = value[0] if value[:1] in {'"', "'"} else ""
    return f"{match.group('prefix')}{quote}{REDACTION_MARKER}{quote}"


class SecretRegistry:
    """Thread-safe set of secret values that must never appear in a log.

    Values are matched exactly and case-sensitively. Empty strings are ignored so
    that a caller cannot accidentally redact every character in the log.
    """

    def __init__(self, initial: Iterable[str] = ()) -> None:
        self._lock = threading.Lock()
        self._values: set[str] = {value for value in initial if value}

    def register(self, value: str) -> None:
        """Add ``value``; registering the same value twice is a no-op."""
        if not value:
            return
        with self._lock:
            self._values.add(value)

    def unregister(self, value: str) -> None:
        """Stop redacting ``value``, if it was registered."""
        with self._lock:
            self._values.discard(value)

    def clear(self) -> None:
        """Forget every registered value."""
        with self._lock:
            self._values.clear()

    def snapshot(self) -> tuple[str, ...]:
        """Return the values longest first, so overlapping secrets match whole."""
        with self._lock:
            return tuple(sorted(self._values, key=len, reverse=True))

    def __len__(self) -> int:
        with self._lock:
            return len(self._values)


class Redactor(logging.Filter):
    """``logging.Filter`` that scrubs a record before it reaches a handler."""

    def __init__(self, registry: SecretRegistry | None = None) -> None:
        super().__init__()
        self._registry = registry if registry is not None else SecretRegistry()

    @property
    def registry(self) -> SecretRegistry:
        """The registry this filter reads from; callers register secrets here."""
        return self._registry

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            self._scrub(record)
        except Exception:  # a logging filter must never raise
            self._fail_safe(record)
        return True

    def _scrub(self, record: logging.LogRecord) -> None:
        message = self._scrub_text(record.getMessage())
        record.msg = message
        record.args = ()
        self._scrub_extras(record)
        if record.exc_text:
            record.exc_text = self._scrub_text(record.exc_text)
        if record.exc_info is not None:
            traceback_text = logging.Formatter().formatException(record.exc_info)
            record.exc_text = self._scrub_text(traceback_text)
            record.exc_info = None
        if record.stack_info:
            record.stack_info = self._scrub_text(record.stack_info)

    def _scrub_extras(self, record: logging.LogRecord) -> None:
        for key, value in list(vars(record).items()):
            if key in _SKIP_FIELDS:
                continue
            record.__dict__[key] = self._scrub_value(value)

    def _scrub_value(self, value: object, depth: int = _MAX_EXTRA_DEPTH) -> object:
        if isinstance(value, str):
            return self._scrub_text(value)
        if depth <= 0:
            return value
        if isinstance(value, Mapping):
            return {key: self._scrub_value(item, depth - 1) for key, item in value.items()}
        if isinstance(value, list):
            return [self._scrub_value(item, depth - 1) for item in value]
        if isinstance(value, tuple):
            return tuple(self._scrub_value(item, depth - 1) for item in value)
        return value

    def _scrub_text(self, text: str) -> str:
        for secret in self._registry.snapshot():
            text = text.replace(secret, REDACTION_MARKER)
        text = _BEARER_PATTERN.sub(f"Bearer {REDACTION_MARKER}", text)
        return _KEY_VALUE_PATTERN.sub(_replace_key_value, text)

    def _fail_safe(self, record: logging.LogRecord) -> None:
        for key in list(vars(record)):
            if key not in _KEEP_ON_FAILURE:
                record.__dict__.pop(key, None)
        record.msg = SAFE_PLACEHOLDER
        record.args = ()
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
