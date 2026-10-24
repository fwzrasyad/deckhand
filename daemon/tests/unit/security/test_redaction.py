"""Tests for the log redaction filter (SEC-016, FR-D-1103)."""

from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from deckhand.security.redaction import (
    REDACTION_MARKER,
    SAFE_PLACEHOLDER,
    Redactor,
    SecretRegistry,
)

SECRET = "fake-device-token-7c1f"
PAIRING_SECRET = "fake-pairing-secret-19ab"


def _record(message: object, args: tuple[object, ...] = ()) -> logging.LogRecord:
    return logging.LogRecord(
        name="deckhand.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=args,
        exc_info=None,
    )


@pytest.fixture
def registry() -> SecretRegistry:
    return SecretRegistry([SECRET, PAIRING_SECRET])


@pytest.fixture
def redactor(registry: SecretRegistry) -> Redactor:
    return Redactor(registry)


def test_filter_always_returns_true(redactor: Redactor) -> None:
    assert redactor.filter(_record("hello")) is True


def test_registered_secret_in_message_is_replaced(redactor: Redactor) -> None:
    record = _record(f"connected with {SECRET}")

    redactor.filter(record)

    assert record.getMessage() == f"connected with {REDACTION_MARKER}"
    assert SECRET not in record.getMessage()


def test_registered_secret_in_args_is_replaced(redactor: Redactor) -> None:
    record = _record("secret is %s and %s", (SECRET, "public"))

    redactor.filter(record)

    assert record.getMessage() == f"secret is {REDACTION_MARKER} and public"
    assert record.args == ()


def test_secret_from_msg_and_args_splits_is_still_found(redactor: Redactor) -> None:
    record = _record("value %s%s", ("fake-dev", "ice-token-7c1f"))

    redactor.filter(record)

    assert SECRET not in record.getMessage()
    assert record.getMessage() == f"value {REDACTION_MARKER}"


def test_registered_secret_in_extra_field_is_replaced(redactor: Redactor) -> None:
    record = _record("hello")
    record.__dict__["user_token"] = SECRET

    redactor.filter(record)

    assert record.__dict__["user_token"] == REDACTION_MARKER


def test_registered_secret_in_nested_extra_is_replaced(redactor: Redactor) -> None:
    record = _record("hello")
    record.__dict__["payload"] = {"params": [SECRET], "pair": (PAIRING_SECRET,)}

    redactor.filter(record)

    assert record.__dict__["payload"] == {
        "params": [REDACTION_MARKER],
        "pair": (REDACTION_MARKER,),
    }


def test_non_string_extra_is_left_alone(redactor: Redactor) -> None:
    record = _record("hello")
    record.__dict__["attempt"] = 3

    redactor.filter(record)

    assert record.__dict__["attempt"] == 3


def test_secret_twice_in_one_line_is_fully_replaced(redactor: Redactor) -> None:
    record = _record(f"{SECRET} then {SECRET} again")

    redactor.filter(record)

    message = record.getMessage()
    assert message.count(REDACTION_MARKER) == 2
    assert SECRET not in message


def test_exception_message_and_traceback_are_redacted(
    caplog: pytest.LogCaptureFixture, redactor: Redactor
) -> None:
    logger = logging.getLogger("deckhand.test.redaction")
    with caplog.at_level(logging.ERROR, logger=logger.name):
        try:
            raise ValueError(f"pairing proof for {PAIRING_SECRET} rejected")
        except ValueError:
            logger.exception("pairing failed")

    record = caplog.records[-1]
    before = record.exc_info
    assert before is not None

    redactor.filter(record)

    assert record.exc_info is None, "the raw traceback object must be dropped"
    exc_text = record.exc_text
    assert isinstance(exc_text, str)
    assert PAIRING_SECRET not in exc_text
    assert REDACTION_MARKER in exc_text
    assert PAIRING_SECRET not in logging.Formatter().format(record)


def test_preset_exc_text_is_redacted(redactor: Redactor) -> None:
    record = _record("hello")
    record.exc_text = f"Traceback (most recent call last):\nValueError: {SECRET}"

    redactor.filter(record)

    assert record.exc_text is not None
    assert SECRET not in record.exc_text
    assert REDACTION_MARKER in record.exc_text


def test_stack_info_is_redacted(redactor: Redactor) -> None:
    record = _record("hello")
    record.stack_info = f"Stack (most recent call last):\n  token={SECRET}"

    redactor.filter(record)

    assert record.stack_info is not None
    assert SECRET not in record.stack_info


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        (
            "request Authorization: Bearer fake-bearer-token-99",
            "request Authorization: Bearer [REDACTED]",
        ),
        ("token=fake-unregistered-1", "token=[REDACTED]"),
        ("PASSWORD: fake-unregistered-2", "PASSWORD: [REDACTED]"),
        ('{"secret": "fake-unregistered-3", "keep": 1}', '{"secret": "[REDACTED]", "keep": 1}'),
        ("api_key='fake-unregistered-4'", "api_key='[REDACTED]'"),
        ("query?token=fake-unregistered-5&next=1", "query?token=[REDACTED]&next=1"),
        ("Authorization: Bearer fake-unregistered-6", "Authorization: Bearer [REDACTED]"),
    ],
)
def test_patterns_redact_unregistered_secrets(
    redactor: Redactor, message: str, expected: str
) -> None:
    record = _record(message)

    redactor.filter(record)

    assert record.getMessage() == expected


def test_bearer_token_alone_is_redacted(redactor: Redactor) -> None:
    record = _record("sending Bearer fake-bearer-token-abc next")

    redactor.filter(record)

    assert record.getMessage() == f"sending Bearer {REDACTION_MARKER} next"


def test_normal_prose_is_not_redacted(redactor: Redactor) -> None:
    message = "deployment finished; the keyboard shortcut was registered"

    record = _record(message)

    redactor.filter(record)

    assert record.getMessage() == message


def test_keyboard_key_is_not_mistaken_for_a_key(redactor: Redactor) -> None:
    record = _record("keyboard=standard")

    redactor.filter(record)

    assert record.getMessage() == "keyboard=standard"


def test_second_pass_does_not_change_the_message(redactor: Redactor) -> None:
    record = _record(f"token={SECRET}")

    redactor.filter(record)
    once = record.getMessage()
    redactor.filter(record)

    assert once == f"token={REDACTION_MARKER}"
    assert record.getMessage() == once


def test_registry_ignores_empty_values(registry: SecretRegistry, redactor: Redactor) -> None:
    registry.register("")

    record = _record("nothing to hide")
    redactor.filter(record)

    assert len(registry) == 2
    assert record.getMessage() == "nothing to hide"


def test_registry_unregister_stops_redaction(registry: SecretRegistry, redactor: Redactor) -> None:
    registry.unregister(SECRET)

    record = _record(f"still {SECRET}")
    redactor.filter(record)

    assert SECRET in record.getMessage()


def test_registry_clear(registry: SecretRegistry) -> None:
    registry.clear()

    assert len(registry) == 0
    assert registry.snapshot() == ()


def test_registry_redacts_the_longest_overlapping_value(redactor: Redactor) -> None:
    redactor.registry.register("fake-token-abc")
    redactor.registry.register("fake-token-abc-longer")

    record = _record("value fake-token-abc-longer end")
    redactor.filter(record)

    assert record.getMessage() == f"value {REDACTION_MARKER} end"


def test_registry_is_thread_safe(registry: SecretRegistry, redactor: Redactor) -> None:
    barrier = threading.Barrier(8)
    failures: list[Exception] = []

    def worker(index: int) -> None:
        try:
            barrier.wait(timeout=5)
            for step in range(40):
                value = f"fake-thread-secret-{index}-{step}"
                registry.register(value)
                record = _record(f"{value} and {SECRET}")
                redactor.filter(record)
                if value in record.getMessage():
                    failures.append(AssertionError(f"{value} leaked"))
                registry.unregister(value)
        except Exception as exc:
            failures.append(exc)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(worker, range(8)))

    assert failures == []
    assert len(registry) == 2


def test_failure_replaces_the_record_with_a_placeholder(
    redactor: Redactor, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(text: str) -> str:
        raise RuntimeError("redaction exploded")

    monkeypatch.setattr(redactor, "_scrub_text", explode)
    record = _record(f"token {SECRET}")
    record.__dict__["leaky"] = {"token": SECRET}

    assert redactor.filter(record) is True

    assert record.getMessage() == SAFE_PLACEHOLDER
    assert SECRET not in record.getMessage()
    assert not hasattr(record, "leaky")
    assert record.name == "deckhand.test"
