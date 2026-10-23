"""Smoke test for the ``deckhand.telemetry`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.telemetry")

    assert module.__doc__, "deckhand.telemetry must document its responsibility"
