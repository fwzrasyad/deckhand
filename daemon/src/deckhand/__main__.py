"""Entry point for ``python -m deckhand``.

Delegates to the Typer application in :mod:`deckhand.cli.main`.
"""

from deckhand.cli.main import app

if __name__ == "__main__":
    app()  # pragma: no cover - exercised by tests/integration and tests/e2e
