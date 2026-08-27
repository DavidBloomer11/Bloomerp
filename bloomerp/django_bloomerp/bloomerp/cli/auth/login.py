import click

from ..base import BLOOMERP_IO_URL
from ..client import BloomerpCliClient
from ..credentials import save_api_key
from .browser import browser_login


@click.command()
@click.option(
    "--api-key",
    metavar="KEY",
    help="Use an existing API key instead of browser authentication.",
)
def login(api_key: str | None) -> None:
    """Log in to Bloomerp.io through a browser or with an API key."""

    resolved_api_key = api_key or browser_login()
    session = BloomerpCliClient(api_key=resolved_api_key).session()
    if not session.get("authenticated"):
        raise click.ClickException("Bloomerp.io did not authenticate this API key.")

    save_api_key(resolved_api_key)
    user = session.get("user", {})
    identity = user.get("email") or user.get("username") or user.get("id") or "user"
    click.secho(f"Logged in as {identity}", fg="green")
    click.echo(f"Server: {BLOOMERP_IO_URL}")
