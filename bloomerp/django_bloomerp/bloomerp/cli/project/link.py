import click

from bloomerp.cli.base import BloomerpProjectState
from bloomerp.cli.client import BloomerpCliClient
from bloomerp.cli.utils import (
    get_project_manifest,
    get_project_state,
    write_project_state,
)


PROJECTS_ENDPOINT = "/api/projects/"
SELF_MANAGED_PROJECT_TYPE = "SELF_MANAGED_CLOUD"
DEFAULT_SERVER_LOCATION = "EU_CENTRAL"


def _project_name(project: dict) -> str:
    return str(project.get("name") or "Unnamed project")


def _project_description(project: dict) -> str:
    name = _project_name(project)
    domain = project.get("domain_name")
    project_id = project.get("id")

    details = [str(value) for value in (domain, project_id) if value]
    return f"{name} ({' · '.join(details)})" if details else name


def _projects_from_response(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [project for project in payload if isinstance(project, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return [
            project
            for project in payload["results"]
            if isinstance(project, dict)
        ]
    raise click.ClickException("Bloomerp.io returned an invalid projects response.")


def _confirm_relink(client: BloomerpCliClient, project_id: str) -> None:
    response = client.request(
        "GET",
        f"{PROJECTS_ENDPOINT}{project_id}/?type={SELF_MANAGED_PROJECT_TYPE}",
        allow_not_found=True,
    )
    if response.status_code == 404:
        click.echo(
            f"The currently linked project ({project_id}) no longer exists "
            "or is not accessible."
        )
        return

    project = response.json()
    click.echo(
        "This local project is already linked to "
        f"{_project_description(project)}."
    )
    click.confirm("Are you sure you want to continue?", abort=True)


def _select_project(projects: list[dict]) -> dict | None:
    selectable_projects = [project for project in projects if project.get("id")]

    click.echo("Available projects:")
    for index, project in enumerate(selectable_projects, start=1):
        click.echo(f"  {index}. {_project_description(project)}")
    create_index = len(selectable_projects) + 1
    click.echo(f"  {create_index}. Create a new project")

    selection = click.prompt(
        "Select a project",
        type=click.IntRange(1, create_index),
    )
    if selection == create_index:
        return None
    return selectable_projects[selection - 1]


def _create_project(client: BloomerpCliClient) -> dict:
    manifest = get_project_manifest()
    manifest_data = manifest.model_dump(mode="json")
    deployment = manifest_data.get("deployment")
    server_location = (
        deployment.get("server_location", DEFAULT_SERVER_LOCATION)
        if isinstance(deployment, dict)
        else DEFAULT_SERVER_LOCATION
    )

    session = client.session()
    user = session.get("user") if isinstance(session, dict) else None
    user_id = user.get("id") if isinstance(user, dict) else None
    if not user_id:
        raise click.ClickException(
            "Bloomerp.io did not return the authenticated user needed to create "
            "the project. Run 'bloomerp auth login' again."
        )

    response = client.request(
        "POST",
        PROJECTS_ENDPOINT,
        json={
            "name": manifest.name,
            "description": manifest.description,
            "owner": user_id,
            "server_location": server_location,
            "bloomerp_version": manifest.runtime.bloomerp_version,
            "type": SELF_MANAGED_PROJECT_TYPE,
        },
    )
    project = response.json()
    if not isinstance(project, dict) or not project.get("id"):
        raise click.ClickException(
            "Bloomerp.io returned an invalid project creation response."
        )
    click.echo(f"Created {_project_description(project)}.")
    return project


@click.command()
def link() -> None:
    """Link the local project to a Bloomerp.io project."""
    client = BloomerpCliClient()
    state = get_project_state()
    if state.project_id:
        _confirm_relink(client, state.project_id)

    projects = _projects_from_response(
        client.request(
            "GET",
            PROJECTS_ENDPOINT + f"?type={SELF_MANAGED_PROJECT_TYPE}",
        ).json()
    )
    selected_project = _select_project(projects) or _create_project(client)
    selected_id = str(selected_project["id"])

    write_project_state(BloomerpProjectState(project_id=selected_id))
    click.echo(f"Linked this project to {_project_description(selected_project)}.")
