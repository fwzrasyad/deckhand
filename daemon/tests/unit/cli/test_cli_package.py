"""Smoke test for the ``deckhand.cli`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.cli")

    assert module.__doc__, "deckhand.cli must document its responsibility"
