"""Smoke test for the ``deckhand.alerts.notifiers`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.alerts.notifiers")

    assert module.__doc__, "deckhand.alerts.notifiers must document its responsibility"
