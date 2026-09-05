"""Add and remove project app selections."""
from urllib.parse import urlsplit
from uuid import UUID

import click

from ..base import BloomerpProjectApp
from ..client import BloomerpCliClient
from ..utils import get_project_manifest, get_project_state, write_project_state
from .marketplace_sources import read_overrides


def _choose(apps, prompt):
    if not apps:
        raise click.ClickException("No apps available to select.")
    for index, app in enumerate(apps, 1):
        click.echo(f"  {index}. {app.get('name') or 'Unnamed app'} ({app['id']})")
    return apps[click.prompt(prompt, type=click.IntRange(1, len(apps))) - 1]


def _available_apps(client):
    apps, endpoint = [], '/api/apps/'
    while endpoint:
        payload = client.request('GET', endpoint).json()
        if isinstance(payload, list):
            apps.extend(payload)
            break
        apps.extend(payload['results'])
        next_page = payload.get('next')
        parts = urlsplit(next_page) if next_page else None
        endpoint = (parts.path + ('?' + parts.query if parts.query else '')) if parts else None
    return apps


@click.command('add-app')
@click.argument('app_id', required=False, type=click.UUID)
@click.option('--version', help='Exact ready version to install; prompted when omitted.')
def add_app(app_id, version):
    """Select an app release, interactively when APP_ID is omitted."""
    from ..marketplace.manage import resolve_manifest, save_and_sync
    manifest = get_project_manifest()
    client = BloomerpCliClient()
    if app_id is None:
        selected = {str(item.id) for item in manifest.apps}
        app = _choose([item for item in _available_apps(client) if str(item['id']) not in selected], 'Select an app to add')
    else:
        app = client.request('GET', f'/api/apps/{app_id}/').json()
    app_id = str(UUID(str(app['id'])))
    version = version or click.prompt('Version', type=str)
    manifest.apps = [item for item in manifest.apps if str(item.id) != app_id] + [
        BloomerpProjectApp(id=app_id, name=app.get('name'), version=version)]
    # Resolve before changing local selection preferences.
    resolved = resolve_manifest(manifest)
    state = get_project_state()
    state.excluded_app_ids = [item for item in state.excluded_app_ids if item != app_id]
    state.dependency_ids = sorted(set(state.dependency_ids) | {app_id})
    write_project_state(state)
    save_and_sync(resolved)
    click.echo(f"Added {app.get('name') or app_id} {version}. Run bloomerp project sync --to-remote to apply remotely.")


@click.command('remove-app')
@click.argument('app_id', required=False, type=click.UUID)
def remove_app(app_id):
    """Remove an app selection while retaining source files and database data."""
    from ..marketplace.manage import resolve_manifest, save_and_sync
    manifest = get_project_manifest()
    if app_id is None:
        app_id = _choose([item.model_dump(mode='json') for item in manifest.apps], 'Select an app to remove')['id']
    app_id = str(app_id)
    if not any(str(item.id) == app_id for item in manifest.apps):
        raise click.ClickException('This app is not selected in the project.')
    if app_id in read_overrides():
        raise click.ClickException('Disable the local development override first.')
    manifest.apps = [item for item in manifest.apps if str(item.id) != app_id]
    state = get_project_state()
    state.dependency_ids = [item for item in state.dependency_ids if item != app_id]
    state.excluded_app_ids = sorted(set(state.excluded_app_ids) | {app_id})
    write_project_state(state)
    # Sync derives installed_apps from the remaining releases and local apps.
    save_and_sync(manifest)
    click.echo('App removed. Run bloomerp project sync --to-remote to apply remotely.')
