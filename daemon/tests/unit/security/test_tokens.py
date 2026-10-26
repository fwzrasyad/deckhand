"""Unit tests for device token generation, hashing and verification (SEC-008)."""

from __future__ import annotations

import hashlib
import logging

import pytest

from deckhand.security.tokens import (
    TOKEN_BYTES,
    TOKEN_HEX_LENGTH,
    generate_token,
    hash_token,
    verify_token,
)


def _zeros(count: int) -> bytes:
    return b"\x00" * count


def _alter_last(value: str) -> str:
    return value[:-1] + ("0" if value[-1] != "0" else "1")


def test_generated_token_is_64_lowercase_hex() -> None:
    token = generate_token()

    assert len(token) == TOKEN_HEX_LENGTH
    assert set(token) <= set("0123456789abcdef")
    assert token == token.lower()


def test_generated_tokens_differ() -> None:
    assert len({generate_token() for _ in range(32)}) == 32


def test_generated_token_uses_the_injected_random_source() -> None:
    assert generate_token(_zeros) == "00" * TOKEN_BYTES
    assert generate_token(lambda count: b"\xab" * count) == "ab" * TOKEN_BYTES


def test_random_source_with_wrong_length_is_rejected() -> None:
    with pytest.raises(ValueError, match="32 bytes"):
        generate_token(lambda _count: b"\x00")


def test_hash_token_is_the_sha256_hex_of_the_token() -> None:
    token = generate_token()

    digest = hash_token(token)

    assert len(digest) == TOKEN_HEX_LENGTH
    assert digest == hashlib.sha256(token.encode("utf-8")).hexdigest()
    assert digest != token


def test_verify_token_accepts_the_matching_token() -> None:
    token = generate_token()

    assert verify_token(token, hash_token(token))


def test_verify_token_rejects_a_one_character_change() -> None:
    token = generate_token()
    stored = hash_token(token)

    assert not verify_token(_alter_last(token), stored)


def test_verify_token_rejects_a_different_token() -> None:
    stored = hash_token(generate_token())

    assert not verify_token(generate_token(), stored)


def test_verify_token_rejects_a_wrong_or_malformed_stored_hash() -> None:
    token = generate_token()

    assert not verify_token(token, hash_token(generate_token()))
    assert not verify_token(token, "")
    assert not verify_token(token, "not-a-hash")
    assert not verify_token(token, "é" * TOKEN_HEX_LENGTH)


def test_token_operations_do_not_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    token = generate_token()
    stored = hash_token(token)

    assert verify_token(token, stored)

    assert caplog.records == []


def test_token_errors_never_include_token_material() -> None:
    with pytest.raises(ValueError) as excinfo:
        generate_token(lambda _count: b"\x00")

    assert "00" * TOKEN_BYTES not in str(excinfo.value)
