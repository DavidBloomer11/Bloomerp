"""Select exact marketplace releases and explicit local development sources."""
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import zipfile

import click

from ..base import BloomerpProjectApp
from ..client import BloomerpCliClient
from ..utils import get_project_manifest, get_project_metadata_dir, get_project_state
from ..project.marketplace_sources import cache_marketplace_wheel, excluded_local_apps, read_overrides, locks_for, app_package


def resolve_manifest(manifest):
    """Download selected ready versions without modifying remote configuration."""
    metadata = get_project_metadata_dir()
    locks, paths = [], []
    client = BloomerpCliClient()
    for extension in manifest.apps:
        if extension.version is None:
            continue
        response = client.request('GET', f'/api/apps/{extension.id}/download/',
                                  params={'version': extension.version}, timeout=300)
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            if sum(item.file_size for item in archive.infolist()) > 100 * 1024 * 1024:
                raise click.ClickException('App download exceeds 100 MiB.')
            lock = json.loads(archive.read('app.json'))
            if lock['id'] != str(extension.id) or lock['version'] != extension.version:
                raise click.ClickException('Downloaded app does not match the selection.')
            name = PurePosixPath(lock['wheel_name']).name
            if name != lock['wheel_name'] or chr(92) in name or not name.endswith('.whl'):
                raise click.ClickException('Invalid app wheel filename.')
            content = archive.read('wheels/' + name)
            cache_marketplace_wheel(metadata, lock, content)
            path = metadata / 'wheels' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            paths.append(str(path))
            locks.append(lock)
    from ..project.marketplace_sources import write_release_cache
    write_release_cache(locks)
    from ..project.marketplace_sources import installed_apps
    installed_apps(manifest)  # Check package conflicts before installing.
    if paths or manifest.runtime.dependencies:
        installer = ['uv', 'pip', 'install', '--python', sys.executable] if shutil.which('uv') else [sys.executable, '-m', 'pip', 'install']
        subprocess.run([*installer, f"Bloomerp=={manifest.runtime.bloomerp_version}", *manifest.runtime.dependencies, *paths], check=True)
    return manifest


def save_and_sync(manifest):
    from ..project.sync import synchronize_local_project
    synchronize_local_project(manifest)


@click.command('resolve')
def resolve():
    """Download the exact releases declared in project.bloomerp.toml."""
    save_and_sync(resolve_manifest(get_project_manifest()))


@click.command('develop')
@click.argument('app_id')
@click.option('--path', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option('--off', is_flag=True)
def develop(app_id, path, off):
    """Explicitly replace one marketplace release with local source for development."""
    if bool(path) == bool(off):
        raise click.ClickException('Specify either --path or --off.')
    overrides = read_overrides()
    if off:
        overrides.pop(app_id, None)
    else:
        from ..app._utils import read_app_manifest, read_app_state
        locks = {item['id']: item for item in locks_for(get_project_manifest())}
        if app_id not in locks:
            raise click.ClickException('Add the marketplace app before overriding it.')
        lock = locks[app_id]
        local = read_app_manifest(path)
        if read_app_state(path).app_id != lock['id'] or app_package(local.django.app_config) != app_package(lock['manifest']['django']['app_config']):
            raise click.ClickException('The local app must be linked to this marketplace app and use the same Python package.')
        overrides[app_id] = str(path.resolve())
    (get_project_metadata_dir() / 'marketplace-overrides.json').write_text(json.dumps(overrides, indent=2) + '\n')
    click.echo(f'{app_id}: ' + ('marketplace release' if off else f'LOCAL {path.resolve()}; uploads/deployment blocked until disabled.'))
