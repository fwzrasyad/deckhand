"""Unit tests for pairing cryptography (SRD 4.4, SEC-006, SEC-007)."""

from __future__ import annotations

import hashlib
from typing import cast

import pytest

from deckhand.security.crypto import (
    CROCKFORD_ALPHABET,
    SECRET_LENGTH,
    InvalidSecretError,
    Role,
    b64url_decode,
    b64url_encode,
    compute_proof,
    fingerprint,
    generate_pairing_secret,
    normalize_secret,
    transcript,
    verify_proof,
)

FP = "00" * 32
CLIENT_NONCE = "AAECAwQFBgcICQoLDA0ODw"
SERVER_NONCE = "EBESExQVFhcYGRobHB0eHw"
DEVICE_ID = "3f2b1c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"


def _zeros(count: int) -> bytes:
    return b"\x00" * count


def _ones(count: int) -> bytes:
    return b"\xff" * count


def _alter_last(value: str) -> str:
    return value[:-1] + ("0" if value[-1] != "0" else "1")


def _proof(role: Role = "client") -> str:
    return compute_proof("0000-0000-0000", role, FP, CLIENT_NONCE, SERVER_NONCE, DEVICE_ID)


def test_generated_secret_format_and_alphabet() -> None:
    for _ in range(50):
        secret = generate_pairing_secret()

        assert len(secret) == 14
        assert secret[4] == "-"
        assert secret[9] == "-"
        plain = secret.replace("-", "")
        assert len(plain) == SECRET_LENGTH
        assert set(plain) <= set(CROCKFORD_ALPHABET)


def test_generated_secrets_use_the_injected_random_source() -> None:
    assert generate_pairing_secret(_zeros) == "0000-0000-0000"
    assert generate_pairing_secret(_ones) == "ZZZZ-ZZZZ-ZZZZ"


def test_generated_secrets_differ() -> None:
    assert generate_pairing_secret() != generate_pairing_secret()


def test_random_source_with_wrong_length_is_rejected() -> None:
    with pytest.raises(ValueError, match="8 bytes"):
        generate_pairing_secret(lambda _count: b"\x00")


@pytest.mark.parametrize(
    ("typed", "expected"),
    [
        ("abcd-efgh-jkmn", "ABCDEFGHJKMN"),
        ("o1il 2o3l 4i5o", "011120314150"),
        ("  abcd efgh\tjkmn\n", "ABCDEFGHJKMN"),
        ("ABCD-EFGH-JKMN", "ABCDEFGHJKMN"),
        ("0123456789ab", "0123456789AB"),
        ("0000-0000-0000", "000000000000"),
    ],
)
def test_normalize_secret_accepts_typed_forms(typed: str, expected: str) -> None:
    assert normalize_secret(typed) == expected


def test_normalize_secret_is_idempotent_on_generated_secrets() -> None:
    secret = generate_pairing_secret()

    assert normalize_secret(secret) == normalize_secret(normalize_secret(secret))


@pytest.mark.parametrize(
    ("typed", "reason"),
    [
        ("ABCD-EFGH-JKM", "12 characters"),
        ("ABCD-EFGH-JKMNZ", "12 characters"),
        ("ABCD-EFGH-JKMU", "invalid characters"),
        ("ABCD-EFGH-JKM$", "invalid characters"),
    ],
)
def test_normalize_secret_rejects_invalid_forms(typed: str, reason: str) -> None:
    with pytest.raises(InvalidSecretError, match=reason):
        normalize_secret(typed)


def test_normalize_secret_error_does_not_echo_the_input() -> None:
    with pytest.raises(InvalidSecretError) as excinfo:
        normalize_secret("oops-typo")

    assert "oops-typo" not in str(excinfo.value)


def test_fingerprint_is_lowercase_sha256() -> None:
    assert fingerprint(b"") == ("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    assert fingerprint(b"certificate") == hashlib.sha256(b"certificate").hexdigest()
    assert fingerprint(b"certificate") == fingerprint(b"certificate").lower()


def test_transcript_is_the_exact_srd_string() -> None:
    assert transcript("client", "abc", "cn", "sn", "did") == (
        "deckhand-pair-v1|client|abc|cn|sn|did"
    )
    assert transcript("server", "abc", "cn", "sn", "did") == (
        "deckhand-pair-v1|server|abc|cn|sn|did"
    )


def test_transcript_rejects_unknown_roles() -> None:
    with pytest.raises(ValueError, match="role"):
        transcript(cast(Role, "phone"), "abc", "cn", "sn", "did")


def test_b64url_encode_never_emits_padding() -> None:
    encoded = b64url_encode(hashlib.sha256(b"proof").digest())

    assert "=" not in encoded
    assert len(encoded) == 43


def test_b64url_decode_round_trips_unpadded_input() -> None:
    payload = b"\x00\xff\x10payload"

    assert b64url_decode(b64url_encode(payload)) == payload
    assert b64url_decode("") == b""


@pytest.mark.parametrize("padded", ["AA==", "AAA=", "AAAA====", "="])
def test_b64url_decode_rejects_padding(padded: str) -> None:
    with pytest.raises(ValueError, match="padded"):
        b64url_decode(padded)


@pytest.mark.parametrize("invalid", ["AA*", "AA AA", "AA+/", "é"])
def test_b64url_decode_rejects_non_alphabet_characters(invalid: str) -> None:
    with pytest.raises(ValueError, match="alphabet"):
        b64url_decode(invalid)


def test_b64url_decode_rejects_impossible_length() -> None:
    with pytest.raises(ValueError, match="impossible length"):
        b64url_decode("A")


def test_compute_proof_normalizes_its_secret() -> None:
    typed = compute_proof("o1il 2o3l 4i5o", "client", FP, CLIENT_NONCE, SERVER_NONCE, DEVICE_ID)

    assert typed == compute_proof(
        "0111-2031-4150", "client", FP, CLIENT_NONCE, SERVER_NONCE, DEVICE_ID
    )
    assert len(typed) == 43
    assert "=" not in typed


def test_verify_proof_accepts_the_matching_proof() -> None:
    assert verify_proof(
        "0000-0000-0000", "client", FP, CLIENT_NONCE, SERVER_NONCE, DEVICE_ID, _proof()
    )
    assert verify_proof(
        "0000-0000-0000", "server", FP, CLIENT_NONCE, SERVER_NONCE, DEVICE_ID, _proof("server")
    )


def test_verify_proof_rejects_a_wrong_secret() -> None:
    assert not verify_proof(
        "1111-1111-1111", "client", FP, CLIENT_NONCE, SERVER_NONCE, DEVICE_ID, _proof()
    )


def test_verify_proof_rejects_a_wrong_fingerprint_mitm() -> None:
    assert not verify_proof(
        "0000-0000-0000",
        "client",
        _alter_last(FP),
        CLIENT_NONCE,
        SERVER_NONCE,
        DEVICE_ID,
        _proof(),
    )


def test_verify_proof_rejects_a_swapped_role() -> None:
    assert not verify_proof(
        "0000-0000-0000", "server", FP, CLIENT_NONCE, SERVER_NONCE, DEVICE_ID, _proof()
    )


def test_verify_proof_rejects_an_altered_nonce() -> None:
    assert not verify_proof(
        "0000-0000-0000",
        "client",
        FP,
        _alter_last(CLIENT_NONCE),
        SERVER_NONCE,
        DEVICE_ID,
        _proof(),
    )
    assert not verify_proof(
        "0000-0000-0000",
        "client",
        FP,
        CLIENT_NONCE,
        _alter_last(SERVER_NONCE),
        DEVICE_ID,
        _proof(),
    )


def test_verify_proof_rejects_an_altered_device_id() -> None:
    assert not verify_proof(
        "0000-0000-0000",
        "client",
        FP,
        CLIENT_NONCE,
        SERVER_NONCE,
        _alter_last(DEVICE_ID),
        _proof(),
    )


@pytest.mark.parametrize(
    "bad_proof",
    [
        _proof() + "=",
        "=" + _proof(),
        "not base64!",
        "",
        "AAAA",
        _proof()[:-1],
        "A" * 43,
    ],
)
def test_verify_proof_rejects_malformed_or_wrong_proofs(bad_proof: str) -> None:
    assert not verify_proof(
        "0000-0000-0000", "client", FP, CLIENT_NONCE, SERVER_NONCE, DEVICE_ID, bad_proof
    )
