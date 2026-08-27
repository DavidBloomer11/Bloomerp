from __future__ import annotations

import click


def not_implemented() -> None:
    """Report a consistently formatted placeholder command."""

    raise click.ClickException("This command is not implemented yet.")
