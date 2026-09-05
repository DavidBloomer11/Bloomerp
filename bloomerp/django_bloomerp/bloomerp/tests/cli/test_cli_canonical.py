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
    configure_sources, installed_apps, MarketplaceFinder, locks_for, write_release_cache,
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
    write_release_cache([lock] if selected else [])
    write_toml_model(Path('.bloomerp/project.bloomerp.toml'), manifest)
    return manifest


@pytest.mark.parametrize('linked,selected,excluded', [(False, False, False), (True, False, False), (True, True, True)])
def test_package_source_rules(linked, selected, excluded):
    with CliRunner().isolated_filesystem():
        manifest = project(linked=linked, selected=selected)
        assert bool(excluded_local_apps(manifest))
        assert upload_manifest(manifest)['apps'] == manifest.model_dump(mode='json', exclude_none=True)['apps']
        assert 'extensions' not in upload_manifest(manifest)
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
        manifest.apps[0].version = '2.0.0'
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
        lock = locks_for(manifest)[0]
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            archive.writestr('app.json', json.dumps(lock))
            archive.writestr('wheels/' + lock['wheel_name'], Path('.bloomerp/wheels/' + lock['wheel_name']).read_bytes())
        client = Mock()
        client.request.return_value.content = stream.getvalue()
        with patch('bloomerp.cli.marketplace.manage.BloomerpCliClient', return_value=client), patch('bloomerp.cli.marketplace.manage.subprocess.run') as install:
            resolved = resolve_manifest(manifest)
        assert resolved.apps == manifest.apps
        assert client.request.call_args.kwargs['params'] == {'version': '1.0.0'}
        assert 'Bloomerp==1.15.0' in install.call_args.args[0]
        assert Path('.bloomerp/marketplace/' + lock['wheel_sha256'] + '/apps/widget/__init__.py').exists()


def test_duplicate_marketplace_package_is_rejected_before_install():
    from bloomerp.cli.base import BloomerpProjectApp
    with CliRunner().isolated_filesystem():
        manifest = project()
        manifest.apps.append(BloomerpProjectApp(id='22222222-2222-4222-8222-222222222222', version='1.0.0'))
        lock = locks_for(manifest)[0]
        write_release_cache([lock, {**lock, 'id': '22222222-2222-4222-8222-222222222222'}])
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
    from bloomerp.cli.base import BloomerpProjectApp
    from bloomerp.cli.project.deploy import deploy
    with CliRunner().isolated_filesystem():
        manifest = project(selected=False)
        app_id = '11111111-1111-4111-8111-111111111111'
        manifest.apps = [BloomerpProjectApp(id=app_id)]
        events = []
        def sync(**kwargs):
            events.append('sync')
            return Mock(manifest=manifest)
        def upload_app(*args, **kwargs):
            events.append('app-upload')
            return {'version': '1.0.0'}
        def upload_project(*args, **kwargs):
            events.append('capture')
            assert manifest.apps[0].version == '1.0.0'
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


def test_scaffold_stays_current_after_nested_release_manifest_toml_round_trip():
    from bloomerp.cli.project.sync import synchronize_local_project
    from bloomerp.cli.project.scaffold import assert_scaffold_current
    from bloomerp.cli.utils import get_project_manifest
    with CliRunner().isolated_filesystem():
        manifest = project()
        # API JSON can put a scalar after nested tables. TOML necessarily moves it.
        lock = locks_for(manifest)[0]
        lock["manifest"] = {
            "name": "widget",
            "django": {"app_config": "apps.widget.apps.WidgetConfig"},
            "routes": [{"url": "/test/", "name": "test", "description": "Test route"}],
            "description": "App description",
        }
        write_release_cache([lock])
        synchronize_local_project(manifest)
        reloaded = get_project_manifest()
        assert reloaded.apps == manifest.apps
        assert_scaffold_current(Path.cwd(), reloaded)
        before = Path("config/settings/generated/common.py").read_bytes()
        synchronize_local_project(reloaded)
        assert Path("config/settings/generated/common.py").read_bytes() == before


def test_production_sources_need_no_local_state_or_wheel_cache(monkeypatch):
    with CliRunner().isolated_filesystem():
        project()
        Path('.bloomerp/state.toml').unlink()
        import shutil
        shutil.rmtree('.bloomerp/wheels')
        monkeypatch.setenv('BLOOMERP_SETTINGS_ENV', 'production')
        before = list(sys.meta_path)
        configure_sources(Path.cwd())
        assert sys.meta_path == before


def test_production_sources_still_reject_development_overrides(monkeypatch):
    with CliRunner().isolated_filesystem():
        project()
        Path('.bloomerp/state.toml').unlink()
        Path('.bloomerp/marketplace-overrides.json').write_text(json.dumps({
            '11111111-1111-4111-8111-111111111111': str(Path('apps/widget').resolve()),
        }))
        monkeypatch.setenv('BLOOMERP_SETTINGS_ENV', 'production')
        with pytest.raises(RuntimeError, match='overrides cannot run in production'):
            configure_sources(Path.cwd())


def test_schema_three_manifest_contains_only_app_selections():
    with CliRunner().isolated_filesystem():
        manifest = project()
        data = manifest.model_dump(mode='json')
        assert data['schema_version'] == 3
        assert 'extensions' not in data
        assert data['apps'] == [{'name': None, 'id': '11111111-1111-4111-8111-111111111111', 'version': '1.0.0'}]
        assert locks_for(manifest)[0]['manifest']['django']['app_config'] == 'apps.widget.apps.WidgetConfig'


def test_old_manifest_releases_move_to_local_cache():
    from bloomerp.cli.utils import get_project_manifest
    with CliRunner().isolated_filesystem():
        manifest = project()
        locks = locks_for(manifest)
        data = manifest.model_dump(mode='json', exclude_none=True)
        data.update(schema_version=2, extensions=data['apps'], apps=locks)
        from bloomerp.cli.toml import _render_table
        Path('.bloomerp/project.bloomerp.toml').write_text('\n'.join(_render_table(data)))
        Path('.bloomerp/app-releases.json').unlink()
        upgraded = get_project_manifest()
        assert upgraded.model_dump(mode='json')['apps'] == manifest.model_dump(mode='json')['apps']
        assert locks_for(upgraded) == locks


def test_missing_release_cache_is_resolved_for_dependency():
    from bloomerp.cli.project.marketplace_sources import ensure_release_cache
    with CliRunner().isolated_filesystem():
        manifest = project()
        Path('.bloomerp/app-releases.json').unlink()
        with patch('bloomerp.cli.marketplace.manage.resolve_manifest') as resolve:
            ensure_release_cache(manifest)
        resolve.assert_called_once_with(manifest)


def test_schema_three_rejects_embedded_app_metadata():
    from pydantic import ValidationError
    with CliRunner().isolated_filesystem():
        data = project().model_dump(mode='json')
        data['apps'][0]['manifest'] = {'name': 'widget'}
        with pytest.raises(ValidationError):
            BloomerpProjectManifest.model_validate(data)


def test_runtime_refuses_missing_dependency_cache():
    with CliRunner().isolated_filesystem():
        project()
        Path('.bloomerp/app-releases.json').unlink()
        with pytest.raises(RuntimeError, match='cache is missing'):
            configure_sources(Path.cwd())


def test_explicit_manifest_root_ignores_cwd_and_does_not_write_cache(tmp_path, monkeypatch):
    from bloomerp.cli.utils import get_project_manifest
    from bloomerp.cli.toml import _render_table
    with CliRunner().isolated_filesystem():
        manifest = project()
        root = Path.cwd()
        data = manifest.model_dump(mode='json', exclude_none=True)
        data.update(schema_version=2, extensions=data['apps'], apps=locks_for(manifest))
        (root / '.bloomerp/project.bloomerp.toml').write_text('\n'.join(_render_table(data)))
        (root / '.bloomerp/app-releases.json').unlink()
        (root / '.bloomerp/state.toml').unlink()
        monkeypatch.chdir(tmp_path)
        assert get_project_manifest(root) == manifest
        assert not (root / '.bloomerp/app-releases.json').exists()
        with pytest.raises(click.ClickException, match='Missing Bloomerp metadata'):
            get_project_manifest(root / 'missing')
        monkeypatch.undo()


def test_local_source_selection_uses_explicit_root_from_another_cwd(tmp_path, monkeypatch):
    with CliRunner().isolated_filesystem():
        project()
        root = Path.cwd()
        before = list(sys.meta_path)
        monkeypatch.chdir(tmp_path)
        try:
            configure_sources(root)
            assert isinstance(sys.meta_path[0], MarketplaceFinder)
        finally:
            sys.meta_path[:] = before
            monkeypatch.undo()


@pytest.mark.parametrize('interactive', [False, True])
@pytest.mark.parametrize('dependency', [False, True])
def test_project_remove_app_removes_installed_app_and_survives_sync(interactive, dependency):
    from bloomerp.cli.main import main
    from bloomerp.cli.utils import get_project_manifest
    from bloomerp.cli.project.sync import synchronize_local_project
    from bloomerp.cli.project.marketplace_sources import local_source_dirs
    with CliRunner().isolated_filesystem():
        manifest = project()
        if not dependency:
            from bloomerp.cli.utils import get_project_state, write_project_state
            state = get_project_state()
            state.dependency_ids = []
            write_project_state(state)
        synchronize_local_project(manifest)
        args = ['project', 'remove-app']
        if not interactive:
            args.append(str(manifest.apps[0].id))
        result = CliRunner().invoke(main, args, input='1\n' if interactive else None)
        assert result.exit_code == 0, result.output
        manifest = get_project_manifest()
        assert manifest.apps == []
        assert manifest.django.installed_apps == []
        assert local_source_dirs(manifest) == []
        synchronize_local_project(manifest)
        assert get_project_manifest().django.installed_apps == []
        assert Path('apps/widget/__init__.py').exists()


@pytest.mark.parametrize('interactive', [False, True])
def test_project_add_app_supports_selector_and_records_name(interactive):
    from unittest.mock import Mock
    from bloomerp.cli.main import main
    from bloomerp.cli.utils import get_project_manifest, get_project_state, write_project_state
    with CliRunner().isolated_filesystem():
        manifest = project(selected=False)
        app_id = '11111111-1111-4111-8111-111111111111'
        state = get_project_state()
        state.excluded_app_ids = [app_id]
        write_project_state(state)
        app = {'id': app_id, 'name': 'Widget'}
        client = Mock()
        client.request.return_value.json.return_value = {'results': [app], 'next': None} if interactive else app
        def resolve(value):
            write_release_cache([{'id': app_id, 'version': '1.0.0', 'manifest': {'django': {'app_config': 'apps.widget.apps.WidgetConfig'}}}])
            return value
        args = ['project', 'add-app'] + ([] if interactive else [app_id, '--version', '1.0.0'])
        with patch('bloomerp.cli.project.apps.BloomerpCliClient', return_value=client), patch('bloomerp.cli.marketplace.manage.resolve_manifest', side_effect=resolve):
            result = CliRunner().invoke(main, args, input='1\n1.0.0\n' if interactive else None)
        assert result.exit_code == 0, result.output
        result_manifest = get_project_manifest()
        assert result_manifest.apps[0].name == 'Widget'
        assert result_manifest.django.installed_apps == ['apps.widget.apps.WidgetConfig']
        assert get_project_state().excluded_app_ids == []


def test_marketplace_no_longer_registers_add_and_remove():
    from bloomerp.cli.marketplace import marketplace
    assert 'add' not in marketplace.commands
    assert 'remove' not in marketplace.commands
