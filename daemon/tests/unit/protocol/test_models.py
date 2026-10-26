"""Shared models mirror the frozen schemas, especially ActionMeta and Capabilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from deckhand.protocol.codec import encode
from deckhand.protocol.envelope import Envelope
from deckhand.protocol.messages.shared import (
    ActionMeta,
    Capabilities,
    CapabilitiesFeatures,
    CapabilitiesTelemetry,
    ParamSpec,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SCHEMAS = _REPO_ROOT / "protocol" / "schemas" / "shared"

_FORBIDDEN = {"argv", "cwd", "env", "shell"}

_EXPECTED_CAPABILITIES = {
    "root": {"os", "telemetry", "features"},
    "telemetry": {"cpu_temp", "gpu", "gpu_vendors", "battery", "disk", "net"},
    "features": {"pty", "signals", "probes", "notifier"},
}


def _schema(name: str) -> dict[str, Any]:
    document: dict[str, Any] = json.loads(
        (_SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8")
    )
    return document


def test_capabilities_field_names_are_frozen() -> None:
    assert set(Capabilities.model_fields) == _EXPECTED_CAPABILITIES["root"]
    assert set(CapabilitiesTelemetry.model_fields) == _EXPECTED_CAPABILITIES["telemetry"]
    assert set(CapabilitiesFeatures.model_fields) == _EXPECTED_CAPABILITIES["features"]


def test_capabilities_match_the_schema_exactly() -> None:
    schema = _schema("Capabilities")
    assert set(schema["properties"]) == _EXPECTED_CAPABILITIES["root"]
    assert (
        set(schema["properties"]["telemetry"]["properties"]) == _EXPECTED_CAPABILITIES["telemetry"]
    )
    assert set(schema["properties"]["features"]["properties"]) == _EXPECTED_CAPABILITIES["features"]
    assert set(schema["required"]) == {"os", "telemetry", "features"}
    assert set(schema["properties"]["telemetry"]["required"]) == _EXPECTED_CAPABILITIES["telemetry"]
    assert set(schema["properties"]["features"]["required"]) == _EXPECTED_CAPABILITIES["features"]


def test_action_meta_has_no_run_block() -> None:
    assert not (_FORBIDDEN & set(ActionMeta.model_fields))
    schema = _schema("ActionMeta")
    assert not (_FORBIDDEN & set(schema["properties"]))


def test_action_meta_ignores_and_never_re_emits_run_block(repo_root: Path) -> None:
    fixture = json.loads(
        (
            repo_root
            / "protocol"
            / "fixtures"
            / "valid"
            / "ActionMeta_argv_unknown_field_is_ignored.json"
        ).read_text(encoding="utf-8")
    )
    meta = ActionMeta.model_validate(fixture["payload"])

    encoded = encode(
        Envelope[Any](
            v=1,
            type="SNAPSHOT",
            id="s-shared-0002",
            ts=0,
            payload=meta,
        )
    )

    for field in _FORBIDDEN:
        assert field not in json.loads(encoded)["payload"]
        assert f'"{field}"' not in encoded


def test_param_spec_ignores_unknown_fields() -> None:
    param = ParamSpec.model_validate(
        {
            "name": "branch",
            "label": "Branch",
            "type": "string",
            "required": True,
            "argv": ["ignored"],
        }
    )

    assert param.name == "branch"
    assert "argv" not in param.model_dump()


def test_param_spec_rejects_an_unknown_type() -> None:
    with pytest.raises(ValueError):
        ParamSpec.model_validate({"name": "n", "label": "N", "type": "yaml", "required": True})
