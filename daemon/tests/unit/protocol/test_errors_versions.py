"""Error registry, safe messages, and version negotiation (SRD 7.3/7.7)."""

from __future__ import annotations

from typing import Any, cast

import pytest

from deckhand.core.errors import DeckhandError
from deckhand.protocol.errors import (
    CLOSE_CODES,
    ERROR_CODES,
    CloseCode,
    ErrorCode,
    ProtocolError,
    sanitize_error_message,
)
from deckhand.protocol.versions import (
    CURRENT_VERSION,
    SUPPORTED_VERSIONS,
    is_supported,
    negotiate_version,
)

_EXPECTED_CODES = {
    "PROTO_MALFORMED",
    "PROTO_UNKNOWN_TYPE",
    "PROTO_VERSION_UNSUPPORTED",
    "AUTH_REQUIRED",
    "AUTH_INVALID_TOKEN",
    "AUTH_REVOKED",
    "AUTH_LOCKED_OUT",
    "PAIR_WINDOW_CLOSED",
    "PAIR_BAD_PROOF",
    "PAIR_LOCKED_OUT",
    "RATE_LIMITED",
    "ACTION_NOT_FOUND",
    "PARAM_INVALID",
    "ACTION_BUSY",
    "RUN_LIMIT_REACHED",
    "RUN_NOT_FOUND",
    "RUN_NOT_ACTIVE",
    "RUN_NOT_INTERACTIVE",
    "SIGNAL_UNSUPPORTED",
    "LAYOUT_CONFLICT",
    "LAYOUT_INVALID",
    "ALERT_RULES_INVALID",
    "UNSUPPORTED_ON_HOST",
    "SHUTTING_DOWN",
    "INTERNAL_ERROR",
}

_EXPECTED_CLOSE_CODES = {
    1000,
    1001,
    1003,
    1009,
    1011,
    4400,
    4401,
    4408,
    4429,
    4503,
}


def _assert_safe(message: str) -> None:
    assert "/" not in message
    assert "\\" not in message
    assert "traceback" not in message.lower()
    assert "argv" not in message.lower()


def test_error_code_registry_matches_srd_7_7() -> None:
    assert {str(code) for code in ErrorCode} == _EXPECTED_CODES
    assert {code.value for code in ERROR_CODES} == _EXPECTED_CODES


def test_close_code_registry_matches_srd_7_7() -> None:
    assert {int(code) for code in CLOSE_CODES} == _EXPECTED_CLOSE_CODES
    assert CloseCode.PROTOCOL_ERROR.value == 4400
    assert CloseCode.AUTH_FAILED.value == 4401
    assert CloseCode.SHUTTING_DOWN.value == 4503


@pytest.mark.parametrize("code", list(ErrorCode))
def test_every_default_message_is_safe(code: ErrorCode) -> None:
    error = ProtocolError(code)

    assert error.code is code
    assert str(error)
    _assert_safe(str(error))


def test_sanitize_error_message_removes_unsafe_content() -> None:
    message = sanitize_error_message(
        "failed C:\\Users\\alice\\project argv Traceback\nPATH=C:\\secret\x00"
    )

    _assert_safe(message)
    assert "secret" not in message
    assert "\x00" not in message


def test_sanitize_error_message_falls_back_when_empty() -> None:
    assert sanitize_error_message("\x00\x01") == "Protocol error"


def test_protocol_error_carries_code_close_code_and_safe_details() -> None:
    error = ProtocolError(
        ErrorCode.PARAM_INVALID,
        "bad argv at C:/tmp",
        close_code=CloseCode.PROTOCOL_ERROR,
        details={"field": "count"},
    )

    assert isinstance(error, DeckhandError)
    assert error.code is ErrorCode.PARAM_INVALID
    assert error.close_code is CloseCode.PROTOCOL_ERROR
    assert error.details == {"field": "count"}
    _assert_safe(str(error))


def test_supported_versions() -> None:
    assert SUPPORTED_VERSIONS == (1,)
    assert CURRENT_VERSION == 1
    assert is_supported(1)
    assert not is_supported(2)
    assert not is_supported(True)
    assert not is_supported("1")


def test_negotiate_picks_the_highest_overlap() -> None:
    assert negotiate_version([1, 2, 3], [1, 2, 4]) == 2
    assert negotiate_version([1, 2, 3]) == 1
    assert negotiate_version([1], [1]) == 1


def test_negotiate_reports_no_overlap() -> None:
    with pytest.raises(ProtocolError) as info:
        negotiate_version([2, 3], [1])

    assert info.value.code is ErrorCode.PROTO_VERSION_UNSUPPORTED
    _assert_safe(str(info.value))


def test_negotiate_treats_malformed_input_as_no_overlap() -> None:
    with pytest.raises(ProtocolError) as info:
        negotiate_version(cast(Any, None))

    assert info.value.code is ErrorCode.PROTO_VERSION_UNSUPPORTED


def test_negotiate_ignores_non_integer_entries() -> None:
    assert negotiate_version(cast(Any, [True, "2", 1])) == 1
    with pytest.raises(ProtocolError):
        negotiate_version(cast(Any, [True, "2"]))
