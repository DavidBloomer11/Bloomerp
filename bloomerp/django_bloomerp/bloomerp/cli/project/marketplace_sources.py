"""Resolve a single source for every project app, locally and when packaging."""
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import sys
import zipfile

import click

from ..app._utils import find_app_dirs, read_app_manifest, read_app_state
from ..utils import get_project_metadata_dir


def app_package(config):
    parts = config.split('.')
    if len(parts) >= 2 and parts[0] == 'apps':
        return '.'.join(parts[:2])
    if len(parts) > 2 and parts[-2] == 'apps':
        return '.'.join(parts[:-2])
    return config


def write_release_cache(locks, metadata=None):
    metadata = metadata or get_project_metadata_dir()
    (metadata / 'app-releases.json').write_text(json.dumps(locks, sort_keys=True))


def locks_for(manifest, metadata=None):
    from ..base import BloomerpProjectManifest
    if not hasattr(manifest, 'model_dump'):
        manifest = BloomerpProjectManifest.model_validate(manifest)
    data = manifest.model_dump(mode='json')
    selected = {str(item['id']): item.get('version') for item in data.get('apps', [])}
    if len(selected) != len(data.get('apps', [])):
        raise click.ClickException('Each app must be declared once.')
    if not selected:
        return []
    cache = (metadata or get_project_metadata_dir()) / 'app-releases.json'
    try:
        locks = json.loads(cache.read_text()) if cache.is_file() else []
        return [lock for lock in locks
                if lock['id'] in selected and selected[lock['id']] == lock['version']]
    except (ValueError, KeyError, TypeError) as exc:
        raise click.ClickException('Invalid app release cache; run bloomerp marketplace resolve.') from exc


def ensure_release_cache(manifest):
    if not manifest.apps:
        return
    local_ids = {read_app_state(directory).app_id for directory in local_source_dirs(manifest)}
    resolved = {lock['id'] for lock in locks_for(manifest)}
    if any(item.version and str(item.id) not in local_ids and str(item.id) not in resolved
           for item in manifest.apps):
        from ..marketplace.manage import resolve_manifest
        resolve_manifest(manifest)


def local_source_dirs(manifest):
    from ..utils import get_project_state
    state = get_project_state()
    dependencies = set(state.dependency_ids) | set(state.excluded_app_ids)
    return [directory for directory in find_app_dirs()
            if read_app_state(directory).app_id not in dependencies]


def excluded_local_apps(manifest):
    # All app code travels in AppVersion wheels, never in the project wheel.
    return find_app_dirs()


def project_apps(manifest):
    return [read_app_manifest(directory).django.app_config for directory in local_source_dirs(manifest)]


def upload_manifest(manifest):
    data = manifest.model_dump(mode='json', exclude_none=True)
    root = get_project_metadata_dir().parent
    data['project_files'] = {name: (root / name).read_text(encoding='utf-8')
                            for name in ('pyproject.toml', 'README.md') if (root / name).is_file()}
    return data


def installed_apps(manifest):
    locks = locks_for(manifest)
    packages = [app_package(item['manifest']['django']['app_config']) for item in locks]
    if len(packages) != len(set(packages)):
        raise click.ClickException('Selected apps have duplicate Python packages.')
    apps = list(dict.fromkeys([*manifest.django.installed_apps,
                              *[item['manifest']['django']['app_config'] for item in locks]]))
    packages = [app_package(app) for app in apps]
    labels = [package.rsplit('.', 1)[-1] for package in packages]
    if len(packages) != len(set(packages)) or len(labels) != len(set(labels)):
        raise click.ClickException('Selected apps have conflicting Python packages or Django app labels.')
    return apps


def read_overrides(metadata=None):
    path = (metadata or get_project_metadata_dir()) / 'marketplace-overrides.json'
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text())
        if not isinstance(value, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in value.items()):
            raise ValueError('Expected paths keyed by marketplace slug')
        return value
    except (ValueError, OSError) as exc:
        raise click.ClickException(f'Invalid marketplace development overrides: {exc}') from exc


def assert_no_overrides():
    overrides = read_overrides()
    if overrides:
        raise click.ClickException('Disable marketplace development overrides before uploading or deploying: ' + ', '.join(sorted(overrides)))


def validate_user_wheel(wheel, manifest):
    with zipfile.ZipFile(wheel) as archive:
        if any(name.startswith('apps/') for name in archive.namelist()):
            raise click.ClickException('Project wheels cannot include app code; upload app versions separately.')


def cache_marketplace_wheel(metadata, lock, content):
    if hashlib.sha256(content).hexdigest() != lock['wheel_sha256']:
        raise click.ClickException('Marketplace wheel failed integrity verification.')
    import io
    destination = metadata / 'marketplace' / lock['wheel_sha256']
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        if sum(item.file_size for item in archive.infolist()) > 100 * 1024 * 1024:
            raise click.ClickException('Expanded marketplace wheel exceeds 100 MiB.')
        for item in archive.infolist():
            path = PurePosixPath(item.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in item.filename:
                raise click.ClickException('Unsafe marketplace wheel path.')
        destination.mkdir(parents=True, exist_ok=True)
        archive.extractall(destination)
    return destination


class MarketplaceFinder(importlib.abc.MetaPathFinder):
    def __init__(self, sources):
        self.sources = sources

    def find_spec(self, fullname, path=None, target=None):
        if fullname not in self.sources:
            return None
        directory = self.sources[fullname]
        return importlib.util.spec_from_file_location(
            fullname, directory / '__init__.py', submodule_search_locations=[str(directory)],
        )


def configure_sources(project_root):
    """Run before Django imports apps; local presence never overrides a release."""
    metadata = Path(project_root) / '.bloomerp'
    manifest_path = metadata / 'project.bloomerp.toml'
    if not manifest_path.is_file():
        return  # Hosted releases install only their selected artifacts.
    overrides = read_overrides(metadata)
    if os.environ.get('BLOOMERP_SETTINGS_ENV', 'local').lower() != 'local':
        if overrides:
            raise RuntimeError('Marketplace development overrides cannot run in production.')
        # Hosted releases install selected wheels and have no local CLI state.
        return
    from ..utils import get_project_manifest, _read_toml_model
    from ..base import BloomerpProjectState
    manifest = get_project_manifest(Path(project_root))
    if not manifest.apps:
        return
    locks = locks_for(manifest, metadata)
    if set(overrides) - {item['id'] for item in locks}:
        raise RuntimeError('Remove overrides for apps no longer selected in the marketplace.')
    # Read through CLI helpers so state file naming stays centralized.
    dependencies = set(_read_toml_model(metadata / "state.toml", BloomerpProjectState).dependency_ids)
    local_ids = {read_app_state(directory).app_id for directory in find_app_dirs(Path(project_root))}
    resolved_ids = {lock['id'] for lock in locks}
    for selection in manifest.apps:
        app_id = str(selection.id)
        if app_id not in resolved_ids and (app_id not in local_ids or app_id in dependencies):
            raise RuntimeError('App release cache is missing; run bloomerp marketplace resolve.')
    sources = {}
    for lock in locks:
        if lock["id"] in local_ids and lock["id"] not in dependencies and lock["id"] not in overrides:
            continue
        package = app_package(lock['manifest']['django']['app_config'])
        if lock['id'] in overrides:
            source = Path(overrides[lock['id']])
            print(f"Marketplace {lock['id']}: LOCAL {source} (replaces {lock['version']})", file=sys.stderr)
        else:
            wheel = metadata / 'wheels' / PurePosixPath(lock['wheel_name']).name
            if not wheel.is_file():
                raise RuntimeError('Marketplace artifact is missing; resolve or pull the project.')
            cached = cache_marketplace_wheel(metadata, lock, wheel.read_bytes())
            source = cached.joinpath(*package.split('.'))
        if not (source / '__init__.py').is_file():
            raise RuntimeError(f'Marketplace package not found: {package}')
        if package in sys.modules:
            raise RuntimeError(f'Marketplace app imported before source selection: {package}')
        if package in sources:
            raise RuntimeError(f'Marketplace package collision: {package}')
        sources[package] = source
    if sources:
        sys.meta_path.insert(0, MarketplaceFinder(sources))
