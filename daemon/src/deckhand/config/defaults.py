"""Default values and example snippets shared by the loader and the CLI.

Layer 0 (foundations). The defaults themselves live on the pydantic models in
:mod:`deckhand.config.settings`; this module only holds names and small literals
that more than one module needs.
"""

from __future__ import annotations

CONFIG_FILENAME = "config.toml"
"""User-edited configuration, inside the config directory (SRD 8.1)."""

ACTIONS_FILENAME = "actions.yaml"
"""Action definitions, inside the config directory (SRD 8.1, 8.3)."""

ENCODING = "utf-8"
"""Encoding for every text file the config package reads."""

HOME_ENV_VAR = "DECKHAND_HOME"
"""Environment variable that overrides every resolved directory (SRD 8.1)."""

OVERRIDE_CONFIG_DIR = "config"
OVERRIDE_STATE_DIR = "state"
OVERRIDE_LOG_DIR = "logs"
"""Subdirectories of ``DECKHAND_HOME`` used when the override is set."""
