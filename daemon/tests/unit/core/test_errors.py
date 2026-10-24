"""Tests for the shared exception hierarchy."""

from __future__ import annotations

import pytest

from deckhand.core.errors import (
    ConfigurationError,
    DeckhandError,
    LifecycleError,
    RateLimitError,
    ShutdownError,
    StartupError,
)


def test_root_error_carries_message_and_details() -> None:
    error = DeckhandError("something broke", details={"service": "transport"})

    assert str(error) == "something broke"
    assert error.message == "something broke"
    assert error.details == {"service": "transport"}
    assert error.args == ("something broke",)


def test_details_default_to_an_empty_independent_dict() -> None:
    first = DeckhandError()
    second = DeckhandError()

    assert first.details == {}
    first.details["added"] = True
    assert second.details == {}


@pytest.mark.parametrize(
    ("error_type", "parent"),
    [
        (ConfigurationError, DeckhandError),
        (LifecycleError, DeckhandError),
        (StartupError, LifecycleError),
        (ShutdownError, LifecycleError),
        (RateLimitError, DeckhandError),
    ],
)
def test_subclasses_share_the_root(
    error_type: type[DeckhandError], parent: type[Exception]
) -> None:
    assert issubclass(error_type, parent)
    assert isinstance(error_type("boom"), DeckhandError)
