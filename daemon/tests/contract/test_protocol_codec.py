"""The daemon codec honours the shared protocol fixtures (PROTO-006/007).

Valid fixtures must decode, re-encode, and still validate against their JSON
Schema. Invalid fixtures must be rejected with a protocol error rather than a
Python exception.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

from deckhand.protocol.codec import MESSAGE_MODELS, decode, encode
from deckhand.protocol.errors import ErrorCode, ProtocolError
from deckhand.protocol.messages.shared import SHARED_MODELS

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCHEMAS_DIR = _REPO_ROOT / "protocol" / "schemas"
_VALID_DIR = _REPO_ROOT / "protocol" / "fixtures" / "valid"
_INVALID_DIR = _REPO_ROOT / "protocol" / "fixtures" / "invalid"


def _schema_paths(schemas_dir: Path) -> list[Path]:
    return sorted(schemas_dir.rglob("*.schema.json"))


def _schema_name_for(stem: str, names: tuple[str, ...]) -> str:
    for name in sorted(names, key=len, reverse=True):
        if stem == name or stem.startswith(f"{name}_"):
            return name
    raise AssertionError(f"no schema matches fixture {stem}")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _validators(
    schemas_dir: Path,
) -> tuple[tuple[str, ...], dict[str, Draft7Validator]]:
    paths = _schema_paths(schemas_dir)
    names = tuple(
        sorted(
            path.name.removesuffix(".schema.json")
            for path in paths
            if path.name != "envelope.schema.json"
        )
    )
    schemas = {"envelope": _load(schemas_dir / "envelope.schema.json")}
    for name in names:
        match = next(path for path in paths if path.name == f"{name}.schema.json")
        schemas[name] = _load(match)
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema, default_specification=DRAFT7))
        for schema in schemas.values()
        if "$id" in schema
    )
    return ("envelope", *names), {
        name: Draft7Validator(schema, registry=registry) for name, schema in schemas.items()
    }


def _errors(document: Any, name: str, validators: dict[str, Draft7Validator]) -> list[str]:
    errors = [
        f"envelope: {error.message}" for error in validators["envelope"].iter_errors(document)
    ]
    if name != "envelope":
        payload = document.get("payload") if isinstance(document, dict) else None
        errors.extend(
            f"{name} payload: {error.message}" for error in validators[name].iter_errors(payload)
        )
    return errors


@pytest.fixture(scope="module")
def protocol_schemas() -> tuple[tuple[str, ...], dict[str, Draft7Validator]]:
    return _validators(_SCHEMAS_DIR)


def _check_valid_fixture(
    path: Path,
    schemas: tuple[tuple[str, ...], dict[str, Draft7Validator]],
) -> None:
    names, validators = schemas
    document = _load(path)
    name = _schema_name_for(path.stem, names)
    assert _errors(document, name, validators) == []

    if name == "envelope" or name in MESSAGE_MODELS:
        decoded = decode(path.read_text(encoding="utf-8"))
        if name != "envelope":
            assert decoded.type == name
            assert name == decoded.payload.__class__.TYPE
        encoded = encode(decoded)
        assert _errors(json.loads(encoded), name, validators) == []
        return

    # Shared-shape fixtures carry the shape as the envelope payload; there is
    # no standalone protocol message for them, so decode the shape directly.
    payload = SHARED_MODELS[name].model_validate(document["payload"])
    dumped = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
    assert list(validators[name].iter_errors(dumped)) == []


@pytest.mark.parametrize("fixture", sorted(path.name for path in _VALID_DIR.glob("*.json")))
def test_valid_fixtures_round_trip(
    fixture: str, protocol_schemas: tuple[tuple[str, ...], dict[str, Draft7Validator]]
) -> None:
    _check_valid_fixture(_VALID_DIR / fixture, protocol_schemas)


@pytest.mark.parametrize("fixture", sorted(path.name for path in _INVALID_DIR.glob("*.json")))
def test_invalid_fixtures_are_rejected_with_protocol_error(fixture: str) -> None:
    try:
        decode((_INVALID_DIR / fixture).read_text(encoding="utf-8"))
    except ProtocolError as error:
        assert error.code is ErrorCode.PROTO_MALFORMED
    else:  # pragma: no cover - a rejection failure is the assertion itself
        pytest.fail(f"{fixture} was accepted by the codec")


def test_registry_covers_every_message_schema(
    protocol_schemas: tuple[tuple[str, ...], dict[str, Draft7Validator]],
) -> None:
    names, _ = protocol_schemas
    shared_or_envelope = set(SHARED_MODELS) | {"envelope"}
    message_schemas = set(names) - shared_or_envelope
    assert set(MESSAGE_MODELS) == message_schemas
