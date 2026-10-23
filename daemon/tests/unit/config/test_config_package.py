"""Smoke test for the ``deckhand.config`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.config")

    assert module.__doc__, "deckhand.config must document its responsibility"
