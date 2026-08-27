import click

from .._not_implemented import not_implemented


@click.command()
@click.argument("slug")
def show(slug: str) -> None:
    """Show details for a marketplace app."""

    not_implemented()
