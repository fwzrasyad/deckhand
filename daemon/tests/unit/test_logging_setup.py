"""Tests for the application logging setup (FR-D-1101 to FR-D-1103)."""

from __future__ import annotations

import json
import logging
import logging.handlers
from collections.abc import Iterator
from pathlib import Path

import pytest

from deckhand.logging_setup import (
    BACKUP_COUNT,
    CONTEXT_FIELDS,
    LOG_FILENAME,
    MAX_LOG_BYTES,
    MAX_LOG_FILES,
    ContextFormatter,
    action_id,
    device_id,
    run_id,
    session_id,
    setup_logging,
)
from deckhand.security.redaction import REDACTION_MARKER, Redactor, SecretRegistry

SECRET = "fake-control-token-5511"


@pytest.fixture(autouse=True)
def _restore_logging() -> Iterator[None]:
    root = logging.getLogger()
    handlers = root.handlers[:]
    filters = root.filters[:]
    level = root.level
    try:
        yield
    finally:
        for handler in root.handlers:
            if handler not in handlers:
                handler.close()
        root.handlers[:] = handlers
        root.filters[:] = filters
        root.setLevel(level)
        for variable in (session_id, device_id, run_id, action_id):
            variable.set(None)


@pytest.fixture
def redactor() -> Redactor:
    return Redactor(SecretRegistry([SECRET]))


def _configure(
    log_dir: Path,
    redactor: Redactor,
    *,
    json_file: bool = True,
    level: str = "INFO",
) -> logging.Logger:
    return setup_logging(log_dir=log_dir, level=level, json_file=json_file, redactor=redactor)


def _root_handlers() -> list[logging.Handler]:
    return list(logging.getLogger().handlers)


def _file_handler() -> logging.handlers.RotatingFileHandler:
    candidates = [
        handler
        for handler in _root_handlers()
        if isinstance(handler, logging.handlers.RotatingFileHandler)
    ]
    assert len(candidates) == 1
    return candidates[0]


def _json_lines(path: Path) -> list[dict[str, object]]:
    _file_handler().flush()
    text = path.read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines()]


def test_configures_console_and_rotating_file(tmp_path: Path, redactor: Redactor) -> None:
    log_dir = tmp_path / "logs"

    _configure(log_dir, redactor, level="DEBUG")

    handlers = _root_handlers()
    assert len(handlers) == 2
    assert isinstance(handlers[0], logging.StreamHandler)
    assert isinstance(handlers[1], logging.handlers.RotatingFileHandler)
    assert (log_dir / LOG_FILENAME).exists()
    assert logging.getLogger().level == logging.DEBUG


def test_redaction_filter_is_installed_on_every_handler(tmp_path: Path, redactor: Redactor) -> None:
    _configure(tmp_path / "logs", redactor)

    handlers = _root_handlers()
    assert handlers
    assert all(redactor in handler.filters for handler in handlers)


def test_rotation_is_five_files_of_five_megabytes(tmp_path: Path, redactor: Redactor) -> None:
    log_dir = tmp_path / "logs"
    _configure(log_dir, redactor)

    file_handler = _file_handler()

    assert MAX_LOG_BYTES == 5 * 1024 * 1024
    assert MAX_LOG_FILES == 5
    assert file_handler.maxBytes == MAX_LOG_BYTES
    assert file_handler.backupCount == BACKUP_COUNT == 4
    assert Path(file_handler.baseFilename) == log_dir / LOG_FILENAME


def test_json_file_carries_contextvars_and_extras(tmp_path: Path, redactor: Redactor) -> None:
    log_dir = tmp_path / "logs"
    session_id.set("sess-1")
    device_id.set("dev-1")
    run_id.set("run-1")
    action_id.set("act-1")
    logger = _configure(log_dir, redactor)

    logger.info("started", extra={"probe": "one", "obj": object()})

    payload = _json_lines(log_dir / LOG_FILENAME)[0]
    assert payload["message"] == "started"
    assert payload["level"] == "INFO"
    assert payload["session_id"] == "sess-1"
    assert payload["device_id"] == "dev-1"
    assert payload["run_id"] == "run-1"
    assert payload["action_id"] == "act-1"
    extra = payload["extra"]
    assert isinstance(extra, dict)
    assert extra["probe"] == "one"
    assert isinstance(extra["obj"], str)


def test_json_file_omits_unset_context(tmp_path: Path, redactor: Redactor) -> None:
    log_dir = tmp_path / "logs"
    logger = _configure(log_dir, redactor)

    logger.info("plain")

    payload = _json_lines(log_dir / LOG_FILENAME)[0]
    assert [field for field in CONTEXT_FIELDS if field in payload] == []


def test_console_appends_set_context(
    tmp_path: Path, redactor: Redactor, capsys: pytest.CaptureFixture[str]
) -> None:
    session_id.set("sess-console")
    run_id.set("run-console")
    logger = _configure(tmp_path / "logs", redactor)

    logger.info("hello")

    err = capsys.readouterr().err
    assert "session_id=sess-console" in err
    assert "run_id=run-console" in err
    assert "hello" in err


def test_file_can_be_human_readable(tmp_path: Path, redactor: Redactor) -> None:
    log_dir = tmp_path / "logs"
    logger = _configure(log_dir, redactor, json_file=False)

    logger.info("plain text line")

    file_handler = _file_handler()
    file_handler.flush()
    content = (log_dir / LOG_FILENAME).read_text(encoding="utf-8")
    assert isinstance(file_handler.formatter, ContextFormatter)
    assert not content.startswith("{")
    assert "plain text line" in content


def test_stack_info_reaches_the_json_file(tmp_path: Path, redactor: Redactor) -> None:
    log_dir = tmp_path / "logs"
    logger = _configure(log_dir, redactor)

    logger.info("with stack", stack_info=True)

    payload = _json_lines(log_dir / LOG_FILENAME)[0]
    assert "Stack (most recent call last)" in str(payload["stack"])


def test_reconfiguration_replaces_handlers(tmp_path: Path, redactor: Redactor) -> None:
    _configure(tmp_path / "logs", redactor)
    _configure(tmp_path / "logs", redactor)

    assert len(_root_handlers()) == 2


def test_unknown_level_is_rejected(tmp_path: Path, redactor: Redactor) -> None:
    with pytest.raises(ValueError, match="unknown log level"):
        _configure(tmp_path / "logs", redactor, level="LOUD")


def test_registered_secret_never_reaches_console_or_file(
    tmp_path: Path,
    redactor: Redactor,
    capsys: pytest.CaptureFixture[str],
) -> None:
    log_dir = tmp_path / "logs"
    logger = _configure(log_dir, redactor)

    logger.info("controller token=%s", SECRET)
    try:
        raise ValueError(f"controller rejected {SECRET}")
    except ValueError:
        logger.exception("request failed")
    _file_handler().flush()

    console = capsys.readouterr().err
    content = (log_dir / LOG_FILENAME).read_text(encoding="utf-8")

    for output in (console, content):
        assert SECRET not in output
        assert REDACTION_MARKER in output

    for line in content.splitlines():
        payload = json.loads(line)
        assert SECRET not in str(payload["message"])
        assert SECRET not in str(payload.get("traceback", ""))
