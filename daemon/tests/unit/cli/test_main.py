"""Unit tests for the root Typer application."""

from __future__ import annotations

from typer.testing import CliRunner

from deckhand import version
from deckhand.cli.main import app

runner = CliRunner()


def test_version_flag_prints_the_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert version.__version__ in result.stdout


def test_running_without_arguments_shows_help() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code != 0
    assert "Usage" in result.stdout
