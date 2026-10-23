"""Smoke test for the ``deckhand.security`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.security")

    assert module.__doc__, "deckhand.security must document its responsibility"
