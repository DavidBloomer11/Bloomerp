import hashlib
import importlib
import io
import json
from pathlib import Path
import sys
import zipfile
from unittest.mock import patch

import click
from click.testing import CliRunner
import pytest

from bloomerp.cli.base import BloomerpProjectManifest
from bloomerp.cli.toml import write_toml_model
from bloomerp.cli.project.marketplace_sources import (
    excluded_local_apps, upload_manifest, validate_user_wheel, assert_no_overrides,
    configure_sources, installed_apps, MarketplaceFinder,
)
from bloomerp.cli.marketplace.manage import develop


def project(*, linked=True, selected=True):
    Path('.bloomerp/apps').mkdir(parents=True)
    Path('.bloomerp/state.toml').write_text('project_id = "project-1"\nsnapshot_id = "snapshot-1"\n')
    if selected:
        with Path('.bloomerp/state.toml').open('a') as state:
            state.write('dependency_ids = ["11111111-1111-4111-8111-111111111111"]\n')
    Path('apps/widget').mkdir(parents=True)
    Path('apps/__init__.py').write_text('')
    Path('apps/widget/__init__.py').write_text('SOURCE = "local"\n')
    Path('apps/widget/app.bloomerp.toml').write_text('name = "widget"\nversion = "1.0.0"\n[django]\napp_config = "apps.widget.apps.WidgetConfig"\n')
    if linked:
        Path('.bloomerp/apps/widget.toml').write_text('app_id = "11111111-1111-4111-8111-111111111111"\n')
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('apps/widget/__init__.py', 'SOURCE = "marketplace"\n')
    content = stream.getvalue()
    lock = {'id': '11111111-1111-4111-8111-111111111111', 'app_slug': 'widget', 'version': '1.0.0', 'version_id': 'release-1',
            'wheel_name': 'widget-1.0.0-py3-none-any.whl', 'wheel_sha256': hashlib.sha256(content).hexdigest(),
            'manifest': {'django': {'app_config': 'apps.widget.apps.WidgetConfig'}}}
    Path('.bloomerp/wheels').mkdir()
    Path('.bloomerp/wheels/' + lock['wheel_name']).write_bytes(content)
    manifest = BloomerpProjectManifest.model_validate({'name': 'Project', 'description': '', 'environment': {},
        'runtime': {'bloomerp_version': '1.15.0'}, 'django': {'installed_apps': ['apps.widget.apps.WidgetConfig']},
        'extensions': [{'id': '11111111-1111-4111-8111-111111111111', 'version': '1.0.0'}] if selected else [],
        'apps': [lock] if selected else []})
    write_toml_model(Path('.bloomerp/project.bloomerp.toml'), manifest)
    return manifest


@pytest.mark.parametrize('linked,selected,excluded', [(False, False, False), (True, False, False), (True, True, True)])
def test_package_source_rules(linked, selected, excluded):
    with CliRunner().isolated_filesystem():
        manifest = project(linked=linked, selected=selected)
        assert bool(excluded_local_apps(manifest))
        assert 'apps' not in upload_manifest(manifest)
        assert installed_apps(manifest) == ['apps.widget.apps.WidgetConfig']


def test_unlinked_collision_rejected():
    with CliRunner().isolated_filesystem():
        manifest = project(linked=False)
        with pytest.raises(click.ClickException, match='collides'):
            from bloomerp.cli.project.sync import synchronize_local_project
            synchronize_local_project(manifest)


def test_stale_lock_is_not_used_for_a_new_version():
    from bloomerp.cli.project.marketplace_sources import locks_for
    with CliRunner().isolated_filesystem():
        manifest = project()
        manifest.extensions[0].version = '2.0.0'
        assert locks_for(manifest) == []


def test_upload_rejects_marketplace_source_even_in_prebuilt_wheel():
    with CliRunner().isolated_filesystem():
        manifest = project()
        with pytest.raises(click.ClickException, match='cannot include app code'):
            validate_user_wheel(Path('.bloomerp/wheels/widget-1.0.0-py3-none-any.whl'), manifest)


def test_develop_is_explicit_and_blocks_uploads():
    runner = CliRunner()
    with runner.isolated_filesystem():
        project()
        result = runner.invoke(develop, ['11111111-1111-4111-8111-111111111111', '--path', 'apps/widget'])
        assert result.exit_code == 0, result.output
        with pytest.raises(click.ClickException, match='Disable'):
            assert_no_overrides()
        result = runner.invoke(develop, ['11111111-1111-4111-8111-111111111111', '--off'])
        assert result.exit_code == 0, result.output
        assert_no_overrides()


@pytest.mark.parametrize('override,expected', [(False, 'marketplace'), (True, 'local')])
def test_actual_import_uses_selected_source(override, expected):
    with CliRunner().isolated_filesystem():
        project()
        if override:
            Path('.bloomerp/marketplace-overrides.json').write_text(json.dumps({'11111111-1111-4111-8111-111111111111': str(Path('apps/widget').resolve())}))
        before_path = list(sys.path)
        before_meta = list(sys.meta_path)
        saved = {name: value for name, value in sys.modules.items() if name == 'apps' or name.startswith('apps.')}
        try:
            for name in saved:
                del sys.modules[name]
            sys.path.insert(0, str(Path.cwd()))
            configure_sources(Path.cwd())
            assert importlib.import_module('apps.widget').SOURCE == expected
        finally:
            sys.path[:] = before_path
            sys.meta_path[:] = before_meta
            for name in list(sys.modules):
                if name == 'apps' or name.startswith('apps.'):
                    del sys.modules[name]
            sys.modules.update(saved)


def test_build_excludes_all_app_code():
    from bloomerp.cli.project.build import build_project_wheel
    with CliRunner().isolated_filesystem():
        project()
        Path('pyproject.toml').write_text('[project]\nname="example"\nversion="1.0.0"\n')
        Path('apps/owned').mkdir()
        Path('apps/owned/__init__.py').write_text('')
        def build(command, **kwargs):
            source = Path(command[-1])
            assert not (source / 'apps/widget').exists()
            assert not (source / 'apps/owned').exists()
            output = Path(command[command.index('--outdir') + 1])
            with zipfile.ZipFile(output / 'example-1.0.0-py3-none-any.whl', 'w') as archive:
                archive.writestr('config/__init__.py', '')
        with patch('bloomerp.cli.project.build.assert_scaffold_current'), patch('bloomerp.cli.project.build.subprocess.run', side_effect=build):
            result = build_project_wheel(Path('dist'))
            assert result.is_file()
        assert Path('apps/widget/__init__.py').is_file()


def test_resolve_downloads_exact_release_and_preserves_declarations():
    from unittest.mock import Mock
    from bloomerp.cli.marketplace.manage import resolve_manifest
    with CliRunner().isolated_filesystem():
        manifest = project()
        lock = manifest.apps[0]
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            archive.writestr('app.json', json.dumps(lock))
            archive.writestr('wheels/' + lock['wheel_name'], Path('.bloomerp/wheels/' + lock['wheel_name']).read_bytes())
        client = Mock()
        client.request.return_value.content = stream.getvalue()
        with patch('bloomerp.cli.marketplace.manage.BloomerpCliClient', return_value=client), patch('bloomerp.cli.marketplace.manage.subprocess.run') as install:
            resolved = resolve_manifest(manifest)
        assert resolved.extensions == manifest.extensions
        assert client.request.call_args.kwargs['params'] == {'version': '1.0.0'}
        assert 'Bloomerp==1.15.0' in install.call_args.args[0]
        assert Path('.bloomerp/marketplace/' + lock['wheel_sha256'] + '/apps/widget/__init__.py').exists()


def test_duplicate_marketplace_package_is_rejected_before_install():
    from bloomerp.cli.base import BloomerpExtension
    with CliRunner().isolated_filesystem():
        manifest = project()
        manifest.extensions.append(BloomerpExtension(id='22222222-2222-4222-8222-222222222222', version='1.0.0'))
        manifest.apps.append({**manifest.apps[0], 'app_slug': 'other', 'id': '22222222-2222-4222-8222-222222222222'})
        with pytest.raises(click.ClickException, match='duplicate Python packages'):
            installed_apps(manifest)


def test_owned_linked_app_uses_local_source_without_override():
    from bloomerp.cli.project.marketplace_sources import local_source_dirs
    with CliRunner().isolated_filesystem():
        manifest = project(selected=False)
        assert [path.name for path in local_source_dirs(manifest)] == ['widget']


def test_manifest_round_trip_preserves_dotted_source_file_names():
    from bloomerp.cli.utils import get_project_manifest
    with CliRunner().isolated_filesystem():
        manifest = project()
        manifest.project_files = {'README.md': '# Project', 'pyproject.toml': '[project]\nname="example"\n'}
        write_toml_model(Path('.bloomerp/project.bloomerp.toml'), manifest)
        assert get_project_manifest() == manifest


def test_app_wheel_has_id_distribution_and_reproducible_bytes():
    from bloomerp.cli.app.build import build_app_wheel
    with CliRunner().isolated_filesystem():
        project(selected=False)
        Path('apps/widget/apps.py').write_text('from django.apps import AppConfig\nclass WidgetConfig(AppConfig):\n    name="apps.widget"\n')
        first = build_app_wheel(Path('apps/widget').resolve(), Path('one'))
        second = build_app_wheel(Path('apps/widget').resolve(), Path('two'))
        assert first.name.startswith('bloomerp_app_11111111111141118111111111111111-')
        assert first.read_bytes() == second.read_bytes()
        with zipfile.ZipFile(first) as wheel:
            assert 'apps/widget/apps.py' in wheel.namelist()
            assert not any('.bloomerp/' in name for name in wheel.namelist())


def test_deploy_syncs_then_uploads_local_app_versions_before_capture():
    from unittest.mock import Mock
    from bloomerp.cli.base import BloomerpExtension
    from bloomerp.cli.project.deploy import deploy
    with CliRunner().isolated_filesystem():
        manifest = project(selected=False)
        app_id = '11111111-1111-4111-8111-111111111111'
        manifest.extensions = [BloomerpExtension(id=app_id)]
        events = []
        def sync(**kwargs):
            events.append('sync')
            return Mock(manifest=manifest)
        def upload_app(*args, **kwargs):
            events.append('app-upload')
            return {'version': '1.0.0'}
        def upload_project(*args, **kwargs):
            events.append('capture')
            assert manifest.extensions[0].version == '1.0.0'
            return {'id': 'snapshot-1'}
        client = Mock()
        client.request.return_value.json.side_effect = [{'deployment_id': 'deployment-1'}, {'status': 'SUCCEEDED'}]
        with (patch('bloomerp.cli.project.deploy.synchronize_project_to_remote', side_effect=sync),
              patch('bloomerp.cli.app.upload.upload_app', side_effect=upload_app),
              patch('bloomerp.cli.project.deploy.build_project_wheel', return_value=Path('project.whl')),
              patch('bloomerp.cli.project.deploy.upload_project_wheel', side_effect=upload_project),
              patch('bloomerp.cli.project.deploy.BloomerpCliClient', return_value=client)):
            result = CliRunner().invoke(deploy)
        assert result.exit_code == 0, result.output
        assert events == ['sync', 'app-upload', 'sync', 'capture']


def test_sync_registers_no_app_when_linked_source_is_a_dependency():
    from unittest.mock import Mock
    from bloomerp.cli.project.sync import synchronize_project_to_remote
    with CliRunner().isolated_filesystem():
        manifest = project()
        with Path('.bloomerp/state.toml').open('a') as output:
            output.write('manifest_revision="revision-1"\n')
        client = Mock()
        client.request.return_value.json.return_value = {'manifest': manifest.model_dump(mode='json'), 'revision':'revision-2'}
        with patch('bloomerp.cli.project.sync.synchronize_scaffold', return_value=([], [], None)):
            synchronize_project_to_remote(client=client)
        assert client.request.call_count == 1
        assert client.request.call_args.args == ('POST', '/api/projects/project-1/manifest/')


def test_combined_sync_excludes_dependencies_from_app_metadata_sync():
    from bloomerp.cli.sync import _selected_app_dirs
    with CliRunner().isolated_filesystem():
        project()
        assert _selected_app_dirs(None) == []


def test_local_sync_removes_stale_installed_app_declarations():
    from bloomerp.cli.project.sync import synchronize_local_project
    with CliRunner().isolated_filesystem():
        manifest = project(selected=False)
        manifest.django.installed_apps.append('apps.removed.apps.RemovedConfig')
        result = synchronize_local_project(manifest)
        assert result.manifest.django.installed_apps == ['apps.widget.apps.WidgetConfig']
