"""Smoke test for the ``deckhand.actions`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.actions")

    assert module.__doc__, "deckhand.actions must document its responsibility"
