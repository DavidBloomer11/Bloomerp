import click

from .._not_implemented import not_implemented


@click.command()
@click.argument("organization_id")
def use(organization_id: str) -> None:
    """Select an organization for future commands."""

    not_implemented()
