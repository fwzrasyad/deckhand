"""Codec behaviour: typed decode, tolerant encoding, hostile input."""

from __future__ import annotations

import json
from typing import Any

import pytest

import deckhand.protocol.codec as codec_module
from deckhand.protocol.codec import decode, encode
from deckhand.protocol.envelope import Envelope
from deckhand.protocol.errors import ErrorCode, ProtocolError
from deckhand.protocol.messages.client import (
    ActionRunPayload,
    PingPayload,
    SnapshotGetPayload,
    UnpairSelfPayload,
)
from deckhand.protocol.messages.server import PongPayload

VALID_NONCE = "ZGVja2hhbmQtcGluZy0wMQ"
VALID_ID = "c-test-0001"


def _message(
    message_type: str,
    payload: Any,
    *,
    reply_to: str | None = None,
    **extra: Any,
) -> str:
    document: dict[str, Any] = {
        "v": 1,
        "type": message_type,
        "id": VALID_ID,
        "ts": 1760000000000,
        "payload": payload,
        **extra,
    }
    if reply_to is not None:
        document["reply_to"] = reply_to
    return json.dumps(document)


def _assert_safe(message: str) -> None:
    assert "/" not in message
    assert "\\" not in message
    assert "traceback" not in message.lower()
    assert "argv" not in message.lower()


def test_decode_returns_the_typed_payload() -> None:
    message = decode(_message("PING", {"nonce": VALID_NONCE}))

    assert isinstance(message.payload, PingPayload)
    assert message.payload.nonce == VALID_NONCE
    assert message.v == 1
    assert message.type == "PING"
    assert message.reply_to is None


def test_decode_preserves_reply_to() -> None:
    message = decode(_message("PONG", {"nonce": VALID_NONCE}, reply_to="c-test-0000"))

    assert isinstance(message.payload, PongPayload)
    assert message.reply_to == "c-test-0000"


def test_empty_payloads_decode_to_the_right_models() -> None:
    assert isinstance(decode(_message("SNAPSHOT_GET", {})).payload, SnapshotGetPayload)
    assert isinstance(decode(_message("UNPAIR_SELF", {})).payload, UnpairSelfPayload)


def test_unknown_top_level_field_is_ignored() -> None:
    message = decode(_message("PING", {"nonce": VALID_NONCE}, future_field="ignored"))

    encoded = encode(message)
    assert "future_field" not in encoded
    assert json.loads(encoded)["payload"] == {"nonce": VALID_NONCE}


def test_unknown_payload_field_is_ignored() -> None:
    message = decode(
        _message(
            "ACTION_RUN",
            {"action_id": "deploy", "params": {}, "argv": ["rm", "-rf"], "cwd": "/tmp"},
        )
    )

    assert isinstance(message.payload, ActionRunPayload)
    assert "argv" not in encode(message)
    assert "cwd" not in encode(message)


def test_unknown_type_is_reported() -> None:
    with pytest.raises(ProtocolError) as info:
        decode(_message("FUTURE_EVENT", {}))

    assert info.value.code is ErrorCode.PROTO_UNKNOWN_TYPE
    _assert_safe(str(info.value))


@pytest.mark.parametrize(
    "payload",
    [[], "empty", 42, None],
)
def test_payload_must_be_an_object(payload: Any) -> None:
    with pytest.raises(ProtocolError) as info:
        decode(_message("SNAPSHOT_GET", payload))

    assert info.value.code is ErrorCode.PROTO_MALFORMED


@pytest.mark.parametrize("text", ["", "{", "null", "[]", '"text"', b"{}"])
def test_invalid_json_is_reported(text: Any) -> None:
    with pytest.raises(ProtocolError) as info:
        decode(text)

    assert info.value.code is ErrorCode.PROTO_MALFORMED
    _assert_safe(str(info.value))


@pytest.mark.parametrize(
    "document",
    [
        {"v": 1, "type": "PING", "id": VALID_ID, "payload": {"nonce": VALID_NONCE}},
        {"v": 0, "type": "PING", "id": VALID_ID, "ts": 0, "payload": {"nonce": VALID_NONCE}},
        {"v": 1, "type": "ping", "id": VALID_ID, "ts": 0, "payload": {"nonce": VALID_NONCE}},
        {"v": 1, "type": "PING", "id": "", "ts": 0, "payload": {"nonce": VALID_NONCE}},
        {"v": 1, "type": "PING", "id": "x" * 65, "ts": 0, "payload": {"nonce": VALID_NONCE}},
        {
            "v": 1,
            "type": "PING",
            "id": VALID_ID,
            "ts": -1,
            "payload": {"nonce": VALID_NONCE},
        },
        {
            "v": 1,
            "type": "PING",
            "id": VALID_ID,
            "ts": 0,
            "reply_to": "",
            "payload": {"nonce": VALID_NONCE},
        },
    ],
)
def test_invalid_envelope_shapes_are_reported(document: dict[str, Any]) -> None:
    with pytest.raises(ProtocolError) as info:
        decode(json.dumps(document))

    assert info.value.code is ErrorCode.PROTO_MALFORMED
    _assert_safe(str(info.value))


def test_payload_failure_uses_only_safe_field_locations() -> None:
    token = "C:\\Users\\alice\\secret-token"
    with pytest.raises(ProtocolError) as info:
        decode(
            _message(
                "AUTH",
                {
                    "device_id": "not-a-uuid",
                    "token": token,
                    "protocol_version": 1,
                    "client": {"app_version": "0.1.0", "platform": "windows"},
                },
            )
        )

    message = str(info.value)
    assert info.value.code is ErrorCode.PROTO_MALFORMED
    assert "secret-token" not in message
    _assert_safe(message)


def test_hostile_deep_nesting_never_escapes_as_another_exception() -> None:
    nested = "[" * 5000 + "]" * 5000
    text = '{"v":1,"type":"PING","id":"c","ts":0,"payload":{"nonce":' + nested + "}}"

    with pytest.raises(ProtocolError) as info:
        decode(text)

    assert info.value.code is ErrorCode.PROTO_MALFORMED


def test_hostile_ten_megabyte_string_never_escapes() -> None:
    text = _message("PING", {"nonce": VALID_NONCE}, future="a" * (10 * 1024 * 1024))

    message = decode(text)
    assert message.payload == PingPayload(nonce=VALID_NONCE)


def test_hostile_nan_and_infinity_are_not_json() -> None:
    for constant in ("NaN", "Infinity", "-Infinity"):
        text = '{"v":1,"type":"PING","id":"c","ts":0,"payload":{"nonce":' + constant + "}}"
        with pytest.raises(ProtocolError) as info:
            decode(text)
        assert info.value.code is ErrorCode.PROTO_MALFORMED


def test_hostile_huge_number_never_escapes() -> None:
    text = '{"v":1,"type":"RUNS_LIST","id":"c","ts":0,"payload":{"limit":' + "9" * 5000 + "}}"

    with pytest.raises(ProtocolError) as info:
        decode(text)

    assert info.value.code is ErrorCode.PROTO_MALFORMED


def test_hostile_null_bytes_are_data_not_a_crash() -> None:
    text = _message(
        "PROCESS_LOG",
        {
            "run_id": "run-1",
            "lines": [{"seq": 1, "stream": "stdout", "ts": 0, "text": "a\u0000b"}],
        },
    )

    message = decode(text)
    assert message.payload.lines[0].text == "a\x00b"
    assert "\\u0000" in encode(message)


def test_encode_omits_absent_reply_to_and_includes_present_one() -> None:
    payload = PingPayload(nonce=VALID_NONCE)
    absent = Envelope[Any](v=1, type="PING", id=VALID_ID, ts=0, payload=payload)
    present = Envelope[Any](v=1, type="PING", id=VALID_ID, ts=0, reply_to="c-0", payload=payload)

    assert "reply_to" not in json.loads(encode(absent))
    assert json.loads(encode(present))["reply_to"] == "c-0"


def test_encode_accepts_a_raw_payload_mapping() -> None:
    message = Envelope[Any](
        v=1,
        type="PING",
        id=VALID_ID,
        ts=0,
        payload={"nonce": VALID_NONCE},
    )

    decoded = decode(encode(message))
    assert isinstance(decoded.payload, PingPayload)


def test_encode_failure_is_a_protocol_error() -> None:
    message = Envelope[Any](
        v=1,
        type="PING",
        id=VALID_ID,
        ts=0,
        payload={"nonce": VALID_NONCE, "not_finite": float("nan")},
    )

    with pytest.raises(ProtocolError) as info:
        encode(message)

    assert info.value.code is ErrorCode.PROTO_MALFORMED


def test_decode_wraps_unexpected_internal_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(text: str) -> Any:
        raise RuntimeError("boom")

    monkeypatch.setattr(codec_module, "_decode", explode)

    with pytest.raises(ProtocolError) as info:
        decode(_message("PING", {"nonce": VALID_NONCE}))

    assert info.value.code is ErrorCode.PROTO_MALFORMED


def test_decode_wraps_unexpected_envelope_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    class ExplodingEnvelope:
        @classmethod
        def model_validate(cls, raw: Any) -> Any:
            raise RuntimeError("boom")

    monkeypatch.setattr(codec_module, "WireEnvelope", ExplodingEnvelope)

    with pytest.raises(ProtocolError) as info:
        decode(_message("PING", {"nonce": VALID_NONCE}))

    assert info.value.code is ErrorCode.PROTO_MALFORMED


def test_decode_wraps_unexpected_payload_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    class ExplodingPayload:
        @classmethod
        def model_validate(cls, raw: Any) -> Any:
            raise RuntimeError("boom")

    monkeypatch.setattr(
        codec_module,
        "MESSAGE_MODELS",
        {"PING": ExplodingPayload},
    )

    with pytest.raises(ProtocolError) as info:
        decode(_message("PING", {"nonce": VALID_NONCE}))

    assert info.value.code is ErrorCode.PROTO_MALFORMED
