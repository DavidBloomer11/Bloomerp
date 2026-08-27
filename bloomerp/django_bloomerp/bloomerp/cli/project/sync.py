import click

from bloomerp.cli.utils import get_project_manifest, get_project_state, get_remote_project, write_project_manifest

@click.command()
def sync() -> None:
    """Synchronise your project with the bloomerp remote server."""
    manifest = get_project_manifest()
    state = get_project_state()
    
    if not state.project_id:
        click.echo("This local project isn't linked to any remote bloomerp.io project.\nPlease use `bloomerp project link` first")
        
    project = get_remote_project(state.project_id)
    
    if not project:
        click.echo("Project not found")
    
    value = click.prompt(
        """
    Please select an option:
        1. Sync from local to remote
        2. Sync from remote to local
        
    Press any other key to cancel.
        """
    )
    match value:
        case "1":
            pass
        case "2":
            manifest.name = project.get("name", "")
            manifest.description = project.get("description", "")
            write_project_manifest(manifest)
            click.echo(
                "Local manifest updated successfully!"
            )       
        case _:
            return
        
    
    

    
    
    
    
