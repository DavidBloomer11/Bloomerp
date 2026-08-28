import click

from bloomerp.cli.client import BloomerpCliClient
from bloomerp.cli.utils import get_project_manifest, get_project_state

from .check import check

@click.command()
def deploy() -> None:
    """Upload and deploy the current project to Bloomerp.io."""
    # 1. Upload to bloomerp server
    state = get_project_state()
    
    if not state.project_id:
        click.echo(
            "Project is not linked to a remote project. Use `bloomerp project link` first"
        )
    
    # 2. Call the deploy command
    client = BloomerpCliClient()
    
    response = client.request(
        "POST",
        f"/api/deployments/deploy/{state.project_id}/"
    )
    
    click.echo(
        response.json()
    )
    
    
    
