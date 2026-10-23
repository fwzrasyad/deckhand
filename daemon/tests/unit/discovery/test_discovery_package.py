"""Smoke test for the ``deckhand.discovery`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.discovery")

    assert module.__doc__, "deckhand.discovery must document its responsibility"
