#!/usr/bin/env python3
"""Validate Deckhand protocol fixtures against their JSON schemas.

Every ``*.json`` file in ``fixtures/valid`` must validate; every file in
``fixtures/invalid`` must be rejected. The schema is chosen from the file name:
the stem starts with the schema name (``envelope``, ``HELLO``, ``AUTH``,
``AUTH_OK``, ``AUTH_FAIL``, ``ERROR``), optionally followed by
``_<rule broken>``.

Message fixtures are checked twice: the whole document against
``envelope.schema.json``, and its ``payload`` against the message schema.
Envelope fixtures are checked against the envelope schema only.

The script also fails when a schema has no valid fixture, so schemas and
fixtures cannot drift apart silently (protocol/README.md rule 1).

Usage: python tools/scripts/validate_protocol.py [schemas_dir] [fixtures_dir]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft7Validator
except ModuleNotFoundError:  # pragma: no cover - environment problem, not a bug
    raise SystemExit(
        "validate_protocol.py needs jsonschema: run `uv sync` in daemon/ "
        "and use daemon/.venv/bin/python (or .venv\\Scripts\\python.exe)."
    ) from None

SCHEMA_NAMES: tuple[str, ...] = (
    "envelope",
    "HELLO",
    "AUTH",
    "AUTH_OK",
    "AUTH_FAIL",
    "ERROR",
)


def load_json(path: Path) -> Any:
    """Read a JSON document from disk."""
    return json.loads(path.read_text(encoding="utf-8"))


def schema_path(schemas_dir: Path, name: str) -> Path:
    """Return the schema file for a message name."""
    if name == "envelope":
        return schemas_dir / "envelope.schema.json"
    return schemas_dir / "messages" / f"{name}.schema.json"


def schema_name_for(stem: str) -> str | None:
    """Return the schema a fixture targets, or None when the name is unknown.

    Longest match wins, so ``AUTH_FAIL_code_not_in_enum`` selects ``AUTH_FAIL``
    rather than ``AUTH``.
    """
    for name in sorted(SCHEMA_NAMES, key=len, reverse=True):
        if stem == name or stem.startswith(f"{name}_"):
            return name
    return None


def errors_for(
    document: Any,
    name: str,
    validators: dict[str, Draft7Validator],
) -> list[str]:
    """Return every schema violation for a fixture document."""
    errors = [
        f"envelope: {error.message}"
        for error in validators["envelope"].iter_errors(document)
    ]
    if name != "envelope":
        payload = document.get("payload") if isinstance(document, dict) else None
        errors.extend(
            f"{name} payload: {error.message}"
            for error in validators[name].iter_errors(payload)
        )
    return errors


def main(argv: list[str]) -> int:
    """Run the fixture check and return a process exit code."""
    schemas_dir = Path(argv[1]) if len(argv) > 1 else Path("protocol/schemas")
    fixtures_dir = Path(argv[2]) if len(argv) > 2 else Path("protocol/fixtures")

    validators = {
        name: Draft7Validator(load_json(schema_path(schemas_dir, name)))
        for name in SCHEMA_NAMES
    }
    failures: list[str] = []
    covered: set[str] = set()
    passed = 0

    for path in sorted((fixtures_dir / "valid").glob("*.json")):
        name = schema_name_for(path.stem)
        if name is None:
            failures.append(f"{path.name}: no schema matches this file name")
            continue
        covered.add(name)
        errors = errors_for(load_json(path), name, validators)
        if errors:
            failures.append(f"{path.name}: expected valid, got {errors[0]}")
        else:
            passed += 1
            print(f"ok    valid/{path.name}  ({name})")

    for path in sorted((fixtures_dir / "invalid").glob("*.json")):
        name = schema_name_for(path.stem)
        if name is None:
            failures.append(f"{path.name}: no schema matches this file name")
            continue
        errors = errors_for(load_json(path), name, validators)
        if errors:
            passed += 1
            print(f"ok    invalid/{path.name}  [{errors[0]}]")
        else:
            failures.append(f"{path.name}: expected a violation, but it validated")

    for name in SCHEMA_NAMES:
        if name not in covered:
            failures.append(f"{name}: no valid fixture")

    for failure in failures:
        print(f"FAIL  {failure}", file=sys.stderr)
    print(f"==> {passed} fixture(s) behaved as expected, {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
