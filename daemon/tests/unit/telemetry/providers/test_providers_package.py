"""Smoke test for the ``deckhand.telemetry.providers`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.telemetry.providers")

    assert module.__doc__, "deckhand.telemetry.providers must document its responsibility"
