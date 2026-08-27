import click

from ..base import BLOOMERP_IO_URL
from ..client import BloomerpCliClient


@click.command()
def status() -> None:
    """Show the current Bloomerp.io authentication status."""

    session = BloomerpCliClient().session()
    if not session.get("authenticated"):
        raise click.ClickException("Not logged in. Run 'bloomerp auth login'.")

    user = session.get("user", {})
    identity = user.get("email") or user.get("username") or user.get("id") or "user"
    click.secho(f"Logged in as {identity}", fg="green")
    click.echo(f"Server: {BLOOMERP_IO_URL}")
