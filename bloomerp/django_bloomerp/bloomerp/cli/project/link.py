import click

from bloomerp.cli.base import BloomerpProjectState
from bloomerp.cli.client import BloomerpCliClient
from bloomerp.cli.utils import get_project_state, write_project_state


PROJECTS_ENDPOINT = "/api/projects/"


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
        f"{PROJECTS_ENDPOINT}{project_id}/",
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


def _select_project(projects: list[dict]) -> dict:
    selectable_projects = [project for project in projects if project.get("id")]
    if not selectable_projects:
        raise click.ClickException(
            "No Bloomerp.io projects are available for your account."
        )

    click.echo("Available projects:")
    for index, project in enumerate(selectable_projects, start=1):
        click.echo(f"  {index}. {_project_description(project)}")

    selection = click.prompt(
        "Select a project",
        type=click.IntRange(1, len(selectable_projects)),
    )
    return selectable_projects[selection - 1]


@click.command()
def link() -> None:
    """Link the local project to a Bloomerp.io project."""
    client = BloomerpCliClient()
    state = get_project_state()
    if state.project_id:
        _confirm_relink(client, state.project_id)

    projects = _projects_from_response(
        client.request("GET", PROJECTS_ENDPOINT).json()
    )
    selected_project = _select_project(projects)
    selected_id = str(selected_project["id"])

    write_project_state(BloomerpProjectState(project_id=selected_id))
    click.echo(f"Linked this project to {_project_description(selected_project)}.")
