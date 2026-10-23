"""Smoke test for the ``deckhand.layout`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.layout")

    assert module.__doc__, "deckhand.layout must document its responsibility"
