import click
from bloomerp.cli.client import BloomerpCliClient

from ..base import BLOOMERP_IO_URL

EDNPOINT = "/api/marketplace/"

@click.command()
def link_app() -> None:
    """Links an app to a marketplace app."""
    client = BloomerpCliClient()
    
    
    