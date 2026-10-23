"""Smoke test for the ``deckhand.control`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.control")

    assert module.__doc__, "deckhand.control must document its responsibility"
