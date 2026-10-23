"""The protocol schemas are well-formed JSON Schema and match SRD 7.2.

This is the daemon's side of the contract check. Fixture validation across both
codebases is added in Phase 1 (PROTO-006, PROTO-007).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator


def _schema_paths(repo_root: Path) -> list[Path]:
    schemas_dir = repo_root / "protocol" / "schemas"
    return sorted(schemas_dir.rglob("*.schema.json"))


def test_schema_directory_is_not_empty(repo_root: Path) -> None:
    assert _schema_paths(repo_root), "no protocol schemas found"


@pytest.mark.parametrize(
    "schema_path",
    _schema_paths(Path(__file__).resolve().parents[3]),
    ids=lambda path: path.name,
)
def test_schema_is_valid_json_schema(schema_path: Path) -> None:
    schema: Any = json.loads(schema_path.read_text(encoding="utf-8"))

    Draft7Validator.check_schema(schema)


def test_envelope_requires_the_documented_fields(repo_root: Path) -> None:
    envelope: dict[str, Any] = json.loads(
        (repo_root / "protocol" / "schemas" / "envelope.schema.json").read_text(encoding="utf-8")
    )

    assert set(envelope["required"]) == {"v", "type", "id", "ts", "payload"}
    assert envelope["properties"]["type"]["pattern"] == "^[A-Z][A-Z0-9_]*$"
    assert envelope["properties"]["id"]["maxLength"] == 64
