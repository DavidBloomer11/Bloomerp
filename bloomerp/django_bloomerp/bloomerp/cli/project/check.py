import click

from .._not_implemented import not_implemented


@click.command()
def check() -> None:
    """Run Django and Bloomerp project validation."""

    not_implemented()
