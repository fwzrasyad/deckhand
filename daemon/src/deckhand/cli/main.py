"""Root Typer application for the ``deckhand`` command.

Layer 4 (edge). Subcommands are registered here; each command module owns one
responsibility.
"""

from typing import Annotated

import typer

from deckhand import version

app = typer.Typer(
    name=version.PRODUCT_NAME,
    help="Control surface daemon for a development PC.",
    no_args_is_help=True,
    add_completion=False,
)


def _show_version(value: bool) -> None:
    if value:
        typer.echo(f"{version.PRODUCT_NAME} {version.__version__}")
        raise typer.Exit


@app.callback()
def main(
    show_version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_show_version,
            is_eager=True,
            help="Show the daemon version and exit.",
        ),
    ] = False,
) -> None:
    """Start or inspect the Deckhand daemon."""
