"""Smoke test for the ``deckhand.protocol.messages`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.protocol.messages")

    assert module.__doc__, "deckhand.protocol.messages must document its responsibility"
