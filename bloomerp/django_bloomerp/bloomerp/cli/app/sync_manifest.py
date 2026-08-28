from __future__ import annotations

import os
import sys
from pathlib import Path

import click

from ..base import BloomerpAppDjango, BloomerpAppManifest, BloomerpAppModel, BloomerpAppModule
from ..toml import write_toml_model
from ._utils import APP_MANIFEST_FILENAME, get_project_root, read_app_manifest, resolve_app_dir


def discover_app_manifest(
    app_dir: Path,
    existing: BloomerpAppManifest,
) -> BloomerpAppManifest:
    project_root = get_project_root()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django
    from django.apps import apps

    django.setup()

    expected_name = f"apps.{app_dir.name}"
    app_config = next(
        (config for config in apps.get_app_configs() if config.name == expected_name),
        None,
    )
    if app_config is None:
        raise click.ClickException(
            f"Django app {expected_name!r} is not installed in this project."
        )

    from bloomerp.modules.definition import module_registry

    module_registry.refresh()
    modules = [
        BloomerpAppModule(
            id=module.full_id or module.id,
            name=module.name,
            description=module.description or "",
        )
        for module in module_registry.get_all().values()
        if module.owner_app_label == app_config.label
    ]
    models = [
        BloomerpAppModel(
            name=model.__name__,
            database_table=model._meta.db_table,
        )
        for model in app_config.get_models()
    ]

    return existing.model_copy(
        update={
            "django": BloomerpAppDjango(
                app_config=(
                    f"{app_config.__class__.__module__}."
                    f"{app_config.__class__.__name__}"
                )
            ),
            "modules": sorted(modules, key=lambda module: module.id),
            "models": sorted(models, key=lambda model: model.name),
        }
    )


def synchronize_app_manifest(app_dir: Path) -> BloomerpAppManifest:
    manifest = discover_app_manifest(app_dir, read_app_manifest(app_dir))
    write_toml_model(app_dir / APP_MANIFEST_FILENAME, manifest)
    return manifest


@click.command("sync_manifest")
@click.argument("name", required=False)
def sync_manifest(name: str | None) -> None:
    """Synchronize an app manifest with its Django models and modules."""

    app_dir = resolve_app_dir(name)
    manifest = synchronize_app_manifest(app_dir)
    click.echo(
        f"Synchronized {app_dir / APP_MANIFEST_FILENAME}: "
        f"{len(manifest.modules)} module(s), {len(manifest.models)} model(s)."
    )
