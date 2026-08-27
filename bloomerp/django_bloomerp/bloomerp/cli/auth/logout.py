import os

import click

from ..credentials import delete_api_key


@click.command()
def logout() -> None:
    """Remove locally stored Bloomerp.io credentials."""

    removed = delete_api_key()
    if os.environ.get("BLOOMERP_API_KEY"):
        click.secho(
            "BLOOMERP_API_KEY is still set in the environment.",
            fg="yellow",
            err=True,
        )
    if removed:
        click.secho("Logged out", fg="green")
    else:
        click.echo("No stored credentials found.")
