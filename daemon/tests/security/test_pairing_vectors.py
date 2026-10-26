"""Every shared pairing vector must pass on the daemon side.

The vectors are an independent contract (see
``protocol/test_vectors/README.md``); this suite only consumes them.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from deckhand.security.crypto import (
    CROCKFORD_ALPHABET,
    SECRET_LENGTH,
    Role,
    b64url_decode,
    compute_proof,
    fingerprint,
    normalize_secret,
    transcript,
    verify_proof,
)

_VECTORS_PATH = Path(__file__).resolve().parents[3] / "protocol" / "test_vectors" / "pairing.json"


def _load_cases() -> list[dict[str, Any]]:
    document: Any = json.loads(_VECTORS_PATH.read_text(encoding="utf-8"))
    assert document["version"] == 1
    cases: list[dict[str, Any]] = document["cases"]
    return cases


CASES = _load_cases()
CASE_IDS = [str(case["name"]) for case in CASES]


def _alter_last(value: str) -> str:
    return value[:-1] + ("0" if value[-1] != "0" else "1")


def _verify(
    case: dict[str, Any],
    role: Role,
    *,
    secret: str | None = None,
    fp: str | None = None,
    client_nonce: str | None = None,
    server_nonce: str | None = None,
    device_id: str | None = None,
    proof: str | None = None,
) -> bool:
    return verify_proof(
        case["secret_input"] if secret is None else secret,
        role,
        case["fingerprint"] if fp is None else fp,
        case["client_nonce"] if client_nonce is None else client_nonce,
        case["server_nonce"] if server_nonce is None else server_nonce,
        case["device_id"] if device_id is None else device_id,
        case[f"{role}_proof"] if proof is None else proof,
    )


def test_vector_file_has_several_cases() -> None:
    assert len(CASES) >= 5
    assert len(CASE_IDS) == len(set(CASE_IDS))


def test_vectors_cover_the_required_edge_cases() -> None:
    assert any(
        " " in case["secret_input"] and any(char in case["secret_input"].upper() for char in "ILO")
        for case in CASES
    )
    assert any(case["cert_der_hex"] != case["cert_der_hex"].lower() for case in CASES)
    assert any(case["secret_input"] != case["normalized_secret"] for case in CASES)


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
def test_vector_normalizes_secret(case: dict[str, Any]) -> None:
    normalized = normalize_secret(case["secret_input"])

    assert normalized == case["normalized_secret"]
    assert len(normalized) == SECRET_LENGTH
    assert set(normalized) <= set(CROCKFORD_ALPHABET)


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
def test_vector_fingerprint_is_lowercase_hex(case: dict[str, Any]) -> None:
    computed = fingerprint(bytes.fromhex(case["cert_der_hex"]))

    assert computed == case["fingerprint"]
    assert re.fullmatch(r"[0-9a-f]{64}", computed)
    assert computed == computed.lower()


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
@pytest.mark.parametrize("role", ["client", "server"])
def test_vector_transcript_matches(case: dict[str, Any], role: Role) -> None:
    computed = transcript(
        role,
        case["fingerprint"],
        case["client_nonce"],
        case["server_nonce"],
        case["device_id"],
    )

    assert computed == case[f"{role}_transcript"]
    assert computed.startswith(f"deckhand-pair-v1|{role}|")


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
@pytest.mark.parametrize("role", ["client", "server"])
def test_vector_proof_matches_and_verifies(case: dict[str, Any], role: Role) -> None:
    computed = compute_proof(
        case["secret_input"],
        role,
        case["fingerprint"],
        case["client_nonce"],
        case["server_nonce"],
        case["device_id"],
    )

    assert computed == case[f"{role}_proof"]
    assert len(computed) == 43
    assert "=" not in computed
    assert len(b64url_decode(computed)) == 32
    assert _verify(case, role)


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
@pytest.mark.parametrize("role", ["client", "server"])
def test_vector_proof_rejects_a_wrong_secret(case: dict[str, Any], role: Role) -> None:
    assert not _verify(case, role, secret=_alter_last(case["normalized_secret"]))


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
@pytest.mark.parametrize("role", ["client", "server"])
def test_vector_proof_rejects_a_wrong_fingerprint_mitm(case: dict[str, Any], role: Role) -> None:
    assert not _verify(case, role, fp=_alter_last(case["fingerprint"]))


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
@pytest.mark.parametrize("role", ["client", "server"])
def test_vector_proof_rejects_a_swapped_role(case: dict[str, Any], role: Role) -> None:
    swapped: Role = "server" if role == "client" else "client"

    assert not _verify(case, swapped, proof=case[f"{role}_proof"])


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
@pytest.mark.parametrize("role", ["client", "server"])
def test_vector_proof_rejects_altered_nonces(case: dict[str, Any], role: Role) -> None:
    assert not _verify(case, role, client_nonce=_alter_last(case["client_nonce"]))
    assert not _verify(case, role, server_nonce=_alter_last(case["server_nonce"]))


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
@pytest.mark.parametrize("role", ["client", "server"])
def test_vector_proof_rejects_an_altered_device_id(case: dict[str, Any], role: Role) -> None:
    assert not _verify(case, role, device_id=_alter_last(case["device_id"]))


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
@pytest.mark.parametrize("role", ["client", "server"])
def test_vector_proof_rejects_padded_base64url(case: dict[str, Any], role: Role) -> None:
    assert not _verify(case, role, proof=case[f"{role}_proof"] + "=")
