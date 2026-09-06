from re import S

import click
from typing import Optional

from bloomerp.cli.client import BloomerpCliClient
from bloomerp.cli.utils import get_project_state

SERVER_INSTANCE_ENDPOINT = "api/server_instances/"

@click.command("pull-data")
@click.option("--server", required=False, help="The server instance to pull data from.")
def pull_data(server:Optional[str] = None):
    """Pull data from the remote source."""
    state = get_project_state()
    if state.project_id is None:
        click.echo("Project is not linked to any remote source. Use 'bloomerp project link' first.")
        return
    
    # Get the server instance
    client = BloomerpCliClient()
    
    if not server:
        instances = client.request(
            "GET",
            SERVER_INSTANCE_ENDPOINT + "?project_id=" + str(state.project_id),
        ).json()
        
        if not instances:
            click.echo("No server instances found for this project.")
            return
        
    
    
    selected_server = "123456789"
    
    
        
    