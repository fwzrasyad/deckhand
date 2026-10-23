"""Smoke test for the ``deckhand.transport.handlers`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.transport.handlers")

    assert module.__doc__, "deckhand.transport.handlers must document its responsibility"
