from __future__ import annotations

import click

from ..base import BloomerpAppState
from ..client import BloomerpCliClient
from ._utils import read_app_manifest, read_app_state, resolve_app_dir, write_app_state


MARKETPLACE_APPS_ENDPOINT = "/api/marketplace_apps/"


def _apps_from_response(payload: object) -> list[dict]:
    if isinstance(payload, list):
        apps = payload
    elif isinstance(payload, dict) and isinstance(payload.get("results"), list):
        apps = payload["results"]
    else:
        raise click.ClickException("Bloomerp.io returned an invalid apps response.")
    return [app for app in apps if isinstance(app, dict) and app.get("id")]


def _app_description(app: dict) -> str:
    name = str(app.get("name") or "Unnamed app")
    slug = app.get("slug")
    app_id = app.get("id")
    details = [str(value) for value in (slug, app_id) if value]
    return f"{name} ({' · '.join(details)})" if details else name


def _confirm_relink(client: BloomerpCliClient, app_id: str) -> None:
    response = client.request(
        "GET",
        f"{MARKETPLACE_APPS_ENDPOINT}{app_id}/",
        allow_not_found=True,
    )
    if response.status_code == 404:
        click.echo(f"The currently linked app ({app_id}) is no longer accessible.")
        return
    click.echo(f"This local app is already linked to {_app_description(response.json())}.")
    click.confirm("Are you sure you want to continue?", abort=True)


def _select_app(apps: list[dict]) -> dict | None:
    click.echo("Available apps:")
    for index, app in enumerate(apps, start=1):
        click.echo(f"  {index}. {_app_description(app)}")
    create_index = len(apps) + 1
    click.echo(f"  {create_index}. Create a new app")
    selection = click.prompt(
        "Select an app",
        type=click.IntRange(1, create_index),
    )
    return None if selection == create_index else apps[selection - 1]


def _create_app(client: BloomerpCliClient, app_dir) -> dict:
    manifest = read_app_manifest(app_dir)
    session = client.session()
    user = session.get("user") if isinstance(session, dict) else None
    user_id = user.get("id") if isinstance(user, dict) else None
    if not user_id:
        raise click.ClickException(
            "Bloomerp.io did not return the authenticated user needed to create the app."
        )
    response = client.request(
        "POST",
        MARKETPLACE_APPS_ENDPOINT,
        json={
            "name": (
                manifest.display_name or manifest.name.replace("_", " ").title()
            ),
            "slug": manifest.name.replace("_", "-"),
            "description": manifest.description,
            "owner": user_id,
        },
    )
    app = response.json()
    if not isinstance(app, dict) or not app.get("id"):
        raise click.ClickException("Bloomerp.io returned an invalid app response.")
    click.echo(f"Created {_app_description(app)}.")
    return app


@click.command()
@click.argument("name", required=False)
def link(name: str | None) -> None:
    """Link a local app to a Bloomerp.io marketplace app."""

    app_dir = resolve_app_dir(name)
    client = BloomerpCliClient()
    state = read_app_state(app_dir)
    if state.marketplace_app_id:
        _confirm_relink(client, state.marketplace_app_id)

    apps = _apps_from_response(client.request("GET", MARKETPLACE_APPS_ENDPOINT).json())
    manageable_apps = [app for app in apps if app.get("owner") is not None]
    selected = _select_app(manageable_apps) or _create_app(client, app_dir)
    write_app_state(
        app_dir,
        BloomerpAppState(marketplace_app_id=str(selected["id"])),
    )
    click.echo(f"Linked this app to {_app_description(selected)}.")
