"""The autostart stub must fail loudly, not silently do nothing."""

from __future__ import annotations

import pytest

from deckhand.platform import autostart


def test_enable_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError, match="not implemented"):
        autostart.enable()


def test_disable_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError, match="not implemented"):
        autostart.disable()


def test_is_enabled_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError, match="autostart"):
        autostart.is_enabled()
