"""Smoke test for the ``deckhand.protocol`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.protocol")

    assert module.__doc__, "deckhand.protocol must document its responsibility"
