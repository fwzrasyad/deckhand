"""Smoke test for the ``deckhand.alerts`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.alerts")

    assert module.__doc__, "deckhand.alerts must document its responsibility"
