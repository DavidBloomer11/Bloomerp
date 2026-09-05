"""Synchronize editable local files with the canonical manifest."""
import re
import tomllib
from pathlib import Path

import click
from packaging.requirements import Requirement, InvalidRequirement
from packaging.utils import canonicalize_name
from ..toml import _render_table


def read_local_metadata(manifest, root):
    manifest = manifest.model_copy(deep=True)
    path = root / 'pyproject.toml'
    if path.is_file():
        data = tomllib.loads(path.read_text())
        requirements = data.get('project', {}).get('dependencies', [])
        dependencies = []
        for item in requirements:
            try:
                requirement = Requirement(item)
            except InvalidRequirement as exc:
                raise click.ClickException(f'Invalid project dependency: {item}') from exc
            if canonicalize_name(requirement.name) == 'bloomerp':
                continue
            if requirement.url:
                raise click.ClickException('Hosted project dependencies must use package names and version constraints, not local paths or URLs.')
            if requirement.name in data.get('tool', {}).get('uv', {}).get('sources', {}):
                raise click.ClickException(f'Custom uv sources for runtime dependency {requirement.name} cannot be deployed; use a published package.')
            dependencies.append(item)
        manifest.runtime.dependencies = dependencies
    readme = root / 'README.md'
    if readme.is_file():
        manifest.description = readme.read_text(encoding='utf-8')
    return manifest


def write_local_metadata(manifest, root):
    path = root / 'pyproject.toml'
    data = tomllib.loads(path.read_text()) if path.is_file() else {}
    project = data.setdefault('project', {})
    project.setdefault('name', re.sub(r'[^a-z0-9-]+', '-', manifest.name.lower()).strip('-') or 'bloomerp-project')
    project.setdefault('version', '0.1.0')
    project['dependencies'] = [f'Bloomerp=={manifest.runtime.bloomerp_version}', *manifest.runtime.dependencies]
    # Packaging is managed in the build staging directory.
    data.pop('build-system', None)
    data.get('tool', {}).pop('setuptools', None)
    path.write_text('\n'.join(_render_table(data)) + '\n', encoding='utf-8')
    (root / 'README.md').write_text(manifest.description, encoding='utf-8')


def write_build_config(manifest, root):
    name = re.sub(r'[^a-z0-9-]+', '-', manifest.name.lower()).strip('-') or 'bloomerp-project'
    data = {'build-system': {'requires': ['setuptools>=68', 'wheel'], 'build-backend': 'setuptools.build_meta'},
            'project': {'name': name, 'version': '0.1.0', 'dependencies': []},
            'tool': {'setuptools': {'packages': {'find': {'include': ['config*']}}, 'package-data': {'*': ['templates/**/*', 'static/**/*']}}}}
    (root / 'pyproject.toml').write_text('\n'.join(_render_table(data)) + '\n')
