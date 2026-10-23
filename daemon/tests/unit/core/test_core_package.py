"""Smoke test for the ``deckhand.core`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.core")

    assert module.__doc__, "deckhand.core must document its responsibility"
