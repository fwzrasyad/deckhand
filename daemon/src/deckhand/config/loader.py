"""Reads and validates ``config.toml`` from the resolved config directory.

Layer 0 (foundations). Never touches ``actions.yaml``; that file belongs to
:mod:`deckhand.actions`.

A missing file is not an error: every key in ``config.toml`` is optional, so an
absent file means "all defaults" (SRD 8.2). Malformed TOML and validation
failures raise :class:`ConfigError`, whose message names the file and the
offending keys.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import ValidationError

from deckhand.config import paths
from deckhand.config.defaults import ENCODING
from deckhand.config.settings import Settings
from deckhand.core.errors import ConfigurationError

__all__ = ["ConfigError", "load_config"]


class ConfigError(ConfigurationError):
    """``config.toml`` could not be read, parsed, or validated."""

    def __init__(self, message: str, *, path: Path | None = None) -> None:
        super().__init__(message, details={"path": str(path)} if path is not None else None)
        self.path = path


def _format_validation_error(error: ValidationError) -> str:
    """Flatten a pydantic error into ``dotted.key: message`` fragments."""
    problems: list[str] = []
    for item in error.errors():
        location = ".".join(str(part) for part in item["loc"]) or "<root>"
        problems.append(f"{location}: {item['msg']}")
    return "; ".join(problems)


def load_config(path: str | Path | None = None) -> Settings:
    """Load and validate ``config.toml``.

    ``path`` defaults to :func:`deckhand.config.paths.config_file`. A missing
    file returns the default :class:`Settings`; any other problem raises
    :class:`ConfigError`.
    """
    target = Path(path) if path is not None else paths.config_file()

    try:
        raw = target.read_bytes()
    except FileNotFoundError:
        return Settings()
    except OSError as exc:
        raise ConfigError(f"cannot read config file {target}: {exc}", path=target) from exc

    try:
        document = tomllib.loads(raw.decode(ENCODING))
    except UnicodeDecodeError as exc:
        raise ConfigError(
            f"config file {target} is not valid {ENCODING}: {exc}", path=target
        ) from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML in {target}: {exc}", path=target) from exc

    try:
        return Settings.model_validate(document)
    except ValidationError as exc:
        message = _format_validation_error(exc)
        raise ConfigError(f"invalid configuration in {target}: {message}", path=target) from exc
