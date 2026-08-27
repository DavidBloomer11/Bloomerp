import click

from bloomerp.cli.utils import get_project_manifest, get_project_state

from .._not_implemented import not_implemented
from .check import check

@click.command()
def deploy() -> None:
    """Upload and deploy the current project to Bloomerp.io."""
    manifest = get_project_manifest()
    state = get_project_state()
    
    
    not_implemented()
