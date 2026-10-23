"""Smoke test for the top-level ``deckhand`` modules."""

import importlib

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "deckhand",
        "deckhand.bootstrap",
        "deckhand.cli.main",
        "deckhand.logging_setup",
        "deckhand.version",
    ],
)
def test_module_imports(module_name: str) -> None:
    module = importlib.import_module(module_name)

    assert module.__doc__, f"{module_name} must document its responsibility"
