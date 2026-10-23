"""Smoke test for the ``deckhand.platform`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.platform")

    assert module.__doc__, "deckhand.platform must document its responsibility"
