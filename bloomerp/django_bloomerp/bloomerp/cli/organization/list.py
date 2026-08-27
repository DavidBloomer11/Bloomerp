import click

from .._not_implemented import not_implemented


@click.command(name="list")
def list_organizations() -> None:
    """List organizations available to the current user."""

    not_implemented()
