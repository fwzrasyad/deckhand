"""Smoke test for the ``deckhand.transport`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.transport")

    assert module.__doc__, "deckhand.transport must document its responsibility"
