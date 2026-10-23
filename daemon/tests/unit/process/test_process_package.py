"""Smoke test for the ``deckhand.process`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.process")

    assert module.__doc__, "deckhand.process must document its responsibility"
