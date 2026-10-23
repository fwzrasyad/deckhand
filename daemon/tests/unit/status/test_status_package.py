"""Smoke test for the ``deckhand.status`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.status")

    assert module.__doc__, "deckhand.status must document its responsibility"
