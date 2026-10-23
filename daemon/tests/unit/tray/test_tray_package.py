"""Smoke test for the ``deckhand.tray`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.tray")

    assert module.__doc__, "deckhand.tray must document its responsibility"
