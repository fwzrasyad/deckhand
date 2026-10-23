"""Smoke test for the ``deckhand.status.probes`` package."""

import importlib


def test_package_imports_and_documents_itself() -> None:
    module = importlib.import_module("deckhand.status.probes")

    assert module.__doc__, "deckhand.status.probes must document its responsibility"
